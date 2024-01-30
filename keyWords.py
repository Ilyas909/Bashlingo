import json
from json import JSONDecodeError
from openai import OpenAI

try:
    with open("config.json", "r") as file:
        inf = json.load(file)
        api_key = inf["api_key"]
except (FileNotFoundError, json.decoder.JSONDecodeError):
    raise JSONDecodeError("config.json not found")



client = OpenAI(api_key=api_key)

response = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[
    {
      "role": "system",
      "content": "You are proficient in the Russian language, and teachers turn to you for help; always respond in Russian."
    },
    {
      "role": "user",
      "content": 'Write 10 words on the topic of plants, and return the answer in JSON format {"words": []}. Provide only the JSON response.'
    }
  ],
  temperature=0.7,
  max_tokens=64,
  top_p=1
)
print(response)