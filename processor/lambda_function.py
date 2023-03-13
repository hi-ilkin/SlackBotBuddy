import json
import boto3
import requests
import AI
import os

auth_token = os.environ.get('SLACK_TOKEN')
header = {'Authorization': f'Bearer {auth_token}'}


class Slack:
    GET_CONVERSATION = 'https://www.slack.com/api/conversations.replies'
    POST_RESPONSE = 'https://www.slack.com/api/chat.postMessage'


def merge_messages_into_conversation(messages):
    conversation = []
    for message in messages:
        role = 'user'
        if message.get('bot_id') is not None:
            role = 'assistant'
        conversation.append({'role': role, 'content': message['text']})

    return conversation


def save_msg_with_response(payload, response):
    client = boto3.resource('dynamodb')
    table = client.Table("messageDataWithResponse")

    p_event = payload['event']

    item = {
        "event_id": payload['event_id'],
        "channel": p_event['channel'],
        "type": p_event.get('type', "Input message type is not available"),
        "text": p_event['text'],
        "ts": p_event['ts'],
        "thread_ts": p_event.get('thread_ts', None),
        "open_ai_response": response['choices'][0]['text'],
        "open_ai_usage": response['usage']
    }

    table.put_item(Item=item)


def get_conversation(payload):
    if payload.get('thread_ts', None) is None:
        return [{"role": "user", "content": payload['text']}]
    else:
        params = {
            'channel': payload['channel'],
            'ts': payload['thread_ts']
        }
        converstation = requests.post(Slack.GET_CONVERSATION, params=params, headers=header)
        data = converstation.json()
        return merge_messages_into_conversation(data['messages'])


def lambda_handler(event, context):
    print(f'event: {event} type: {type(event)}')

    for record in event['Records']:
        body = json.loads(record['body'])
        payload = body['event']

        if payload.get('client_msg_id', None) is not None and payload['type'] == 'message':
            text = get_conversation(payload)
            response = AI.get_openai_response(text)
            response_text = AI.get_formatted_response(response)
            # response = AI.mock_code_response()

            data = {
                "text": response_text,
                "channel": payload['channel'],
                "thread_ts": payload['ts']
            }
            try:
                save_msg_with_response(body, response)
            except Exception as e:
                print(f"Unable to write data to DynamoDB")
                print(e)

            requests.post(Slack.POST_RESPONSE, json=data, headers=header)

    return {
        'statusCode': 200
    }
