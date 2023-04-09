import openai
import json
import jsonlines
import os
import html

# Set up OpenAI GPT-3 API Key (replace with your own API key)
API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = API_KEY

def generate_description(command):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Without mentioning the name of the command (or sometimes even suggesting an approach), describe what the command does as an imperative. For example, if the command is 'ls', you could say 'list the contents of a directory'. Add some variability to your writing style. Flip a coin to decide to use proper capitalization. Flip a coin to decide to use proper punctuation. If the command is unclear, you aren't at least 99% certain it is a valid terminal command, or a clear description can't be made, or might be something other than a terminal command, or might be a command for something else (like SQL or other), just say '##DONTKNOW##'. Don't guess. Again, be ABSOLUTELY SURE you know what the command is and what it does. Otherwise say '##DONTKNOW##'.\n\nCommand: {command}\n\nDescription:",
        max_tokens=100
    )
    description = response.choices[0].text.strip()
    return description

def generate_descriptions(commands):
    with jsonlines.open("commandpairs.jsonl", mode='w') as writer:
        file_obj = writer._fp

        for command in commands:
            command = html.unescape(command)
            if command.startswith("-") or command[0].isdigit():
                continue
            if command[0] == "." and command[1] != "/":
                continue
            description = generate_description(command)

            if '##DONTKNOW##' in description:
                continue

            print(f"Command: {command}")
            print(f"Description: {description}\n")

            writer.write({
                "completion": command,
                "prompt": description
            })
            file_obj.flush()



with open("commands.json", 'r') as f:
    data = json.load(f)
    generate_descriptions(data)
