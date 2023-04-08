import argparse
import openai
import os

API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = API_KEY

def select_option(options):
    while True:
        # Enumerate and display the strings
        print("0. Exit")
        for index, string in enumerate(options, start=1):
            print(f"{index}. {string}")
        print(f"{len(options) + 1}. None of these work. I need to provide more context.")
        
        # Simulate user input
        user_input = input("Prompt: ")
        
        if user_input == '':
            # Default to the first option if no input is given
            selected_index = 1
            break
        else:
            try:
                # Convert the user input to an integer
                selected_index = int(user_input)
                # Ensure the user selects a valid option
                if selected_index < 0 or selected_index > len(options) + 1:
                    raise ValueError
                # Exit option
                if selected_index == 0:
                    return 0
                if selected_index == len(options) + 1:
                    return -1
                break
            except ValueError:
                # If the input is invalid, inform the user and prompt to try again
                print("Invalid selection. Please try again.")
    
    # Return the selected string
    return options[selected_index - 1]

def breakup_response(input_string):
    # Step 1: Split the string into lines
    lines = input_string.splitlines()

    # Step 2: Filter out unwanted lines
    filtered_lines = [line for line in lines if line.strip() and line.strip() != "```" and not line.startswith("Option")]

    # Step 3: Remove "```" from the beginning and end
    if filtered_lines and filtered_lines[0] == "```":
        filtered_lines.pop(0)
    if filtered_lines and filtered_lines[-1] == "```":
        filtered_lines.pop(-1)

    return filtered_lines

def generate_response(messages):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    return response.choices[0].message['content']

def main():
    parser = argparse.ArgumentParser(description='A command line helper.')
    parser.add_argument("--tempfile", type=str, required=True, help="Delimiter string to mark the relevant output.")
    parser.add_argument("--context", type=str, help='System info context')
    args = parser.parse_args()

    prompts = []
    command_responses = []

    while True:
        messages = [
            {"role": "system", "content": "You are ConsoleGPT, a command line terminal user assistant. You respond only with console commands."},
            {"role": "system", "content": f"System information context: {args.context}"},
        ]

        for index, prompt in enumerate(prompts):
            messages.append({"role": "user", "content": prompts[index]})
            messages.append({"role": "system", "content": command_responses[index]})

        user_prompt = input("Prompt: ")
        messages.append({"role": "user", "content": user_prompt})
        messages.append({"role": "system", "content": "Remember, only answer with console commands. Do not enumerate them, describe them, or provide any context. Only give commands. If there are several suggestions, put them on separate lines. Again, only the commands themselves. No context. No enumerations. Don't surround with quotes. Just the commands."})

        response = generate_response(messages)
        response = response.replace("\\n", "\n")

        command_responses.append(response)
        prompts.append(user_prompt)

        commands = breakup_response(response)
        selection = select_option(commands)
        if selection == -1:
            print("Please provide more context.")
        elif selection == 0:
            print("Exiting.")
            exit()
        else:
            break

    print("Selected command: " + selection)
    with open(args.tempfile, "w") as file:
        file.write(selection)


if __name__ == '__main__':
    main()
