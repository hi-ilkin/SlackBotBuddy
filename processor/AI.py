import openai
import os

openai.api_key = os.environ.get('OPENAI_TOKEN')


def get_openai_response(message):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=message,
        top_p=1
    )

    return response


def get_formatted_response(response):
    # print(f"OpenAI response: {json.dumps(response)}")
    return f"{response['choices'][0]['message']['content']}"


def mock_code_response():
    message = "\n\nwindow = 3\n\nl = [1, 2, 3, 4, 5, 6, 7, 8, 9]\n\nfor i in range(len(l) - window + 1):\n\nprint(l[i:i+window])"
    return f"```{message.strip()}```"
