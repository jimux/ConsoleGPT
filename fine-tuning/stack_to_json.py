import argparse
import os
import py7zr
import glob
import re
import xml.etree.ElementTree as ET
from io import StringIO
import json
from typing import List, Dict
import shutil
import tempfile

# Global list to store all valid terminal commands encountered
commands_list = []

def extract_code_block(text: str) -> str:
    # Define a regular expression pattern to match the <code>...</code> block
    pattern = r"<code>(.*?)<\/code>"
    # Use re.findall to find all occurrences of the pattern in the text
    code_blocks = re.findall(pattern, text)
    # Join the code blocks (if multiple) with a newline separator
    return code_blocks

def is_valid_command_code_block(code_block):
    """
    Determines if the given code block is a valid terminal command.
    """
    # Split code block into lines
    lines = code_block.split('\n')

    for line in lines:
        if not line or not line.strip():
            continue

        # Check if "=" sign has spaces on either side
        if " = " in line:
            return False

        # Check if the line ends with \ except the last line
        if line.endswith('\\') and line == lines[-1]:
            return False

        # Check if the first word contains valid characters in a command
        first_word = line.split()[0]
        if not all(c.isalnum() or c in ('_', '-', '.') for c in first_word):
            return False

        # If the block contains a space followed by a "-", it is positively identified as a command
        if " -" in line:
            commands_list.append(line)
            return True

    # If all the checks passed, then the code block is a valid terminal command
    commands_list.append(line)
    return True

def identify_terminal_commands(json_obj):
    """
    Walks through a JSON object containing questions and answers, and marks each question object with an "is_command" flag
    based on whether the answers discuss terminal commands or not.
    """
    for question_obj in json_obj:
        answers = question_obj['answers']

        # Initialize a flag to identify if the answers are about terminal commands
        is_command = True

        # Check if answers contain valid terminal commands
        for answer_obj in answers:
            answer = answer_obj['answer']
            answer_code_blocks = extract_code_block(answer)
            # If there are code blocks in the answer, check if they are valid commands
            if answer_code_blocks:
                is_command &= all(is_valid_command_code_block(code_block) for code_block in answer_code_blocks)
                if not is_command:
                    break
            # If there are no code blocks in the answer, set is_command to False
            else:
                is_command = False
                break

        # Set the "is_command" flag for the question object
        question_obj['is_command'] = is_command

    return json_obj

# Testing the function with the provided json_obj
#identified_json_obj = identify_terminal_commands(json_obj)
#print(json.dumps(identified_json_obj, indent=4))

def convert_xml_to_objects(xml_data: str) -> List[Dict]:
    questions = {}
    deferred_answers = {}

    # Wrap the xml_data string with StringIO to create a file-like object
    xml_file = StringIO(xml_data)

    # Use iterparse to parse the XML data iteratively
    context = ET.iterparse(xml_file, events=("start", "end"))

    # Iterate through all rows
    for event, elem in context:
        if event == "end" and elem.tag == "row":
            # Get attributes
            post_type_id = int(elem.get('PostTypeId', 0))
            if post_type_id == 1:  # Question
                question_id = int(elem.get('Id', 0))
                accepted_answer_id = int(elem.get('AcceptedAnswerId', 0))
                body = elem.get('Body', '')
                questions[question_id] = {
                    'question': body,
                    'AcceptedAnswerId': accepted_answer_id,
                    'answers': deferred_answers.get(question_id, [])
                }
                # Remove the question_id from deferred_answers
                deferred_answers.pop(question_id, None)
            elif post_type_id == 2:  # Answer
                parent_id = int(elem.get('ParentId', 0))
                body = elem.get('Body', '')
                score = int(elem.get('Score', 0))
                answer_id = int(elem.get('Id', 0))
                answer_data = {
                    'answer': body,
                    'score': score,
                    'accepted': False  # We'll update this later
                }
                if parent_id in questions:
                    accepted_answer_id = questions[parent_id].get('AcceptedAnswerId', 0)
                    answer_data['accepted'] = answer_id == accepted_answer_id
                    questions[parent_id]['answers'].append(answer_data)
                else:
                    # Defer adding the answer until the question is encountered
                    if parent_id not in deferred_answers:
                        deferred_answers[parent_id] = []
                    deferred_answers[parent_id].append(answer_data)

            # Clear the element to free memory
            elem.clear()

    # Update the 'accepted' status for deferred answers
    for question_id, answers in deferred_answers.items():
        accepted_answer_id = questions.get(question_id, {}).get('AcceptedAnswerId', 0)
        for answer_data in answers:
            answer_data['accepted'] = answer_id == accepted_answer_id
            questions[question_id]['answers'].append(answer_data)

    # Convert the questions dictionary to a list and remove the 'AcceptedAnswerId' key
    result = []
    for question in questions.values():
        question.pop('AcceptedAnswerId', None)
        result.append(question)

    return result

def convert_xml_to_json(xml_data: str) -> str:
    # Convert XML data to list of objects
    result = convert_xml_to_objects(xml_data)

    identified_json_obj = identify_terminal_commands(result)

    # Dump the result to JSON string
    json_str = json.dumps(result, indent=4)

    return json_str

def process_7z_files(folder: str) -> None:
    # Walk through the directory to find all 7z files
    for file in glob.glob(os.path.join(folder, '*.7z')):
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Open the 7z archive
            with py7zr.SevenZipFile(file, mode='r') as archive:
                # Get the list of files in the archive
                file_list = archive.getnames()
                # Find the Posts.xml file in the archive
                posts_xml_file = next((f for f in file_list if f.endswith('Posts.xml')), None)
                if posts_xml_file:
                    # Extract the Posts.xml file to the temporary directory
                    archive.extractall(path=temp_dir)
                    # Determine the output JSON file name
                    output_json_file = os.path.splitext(os.path.basename(file))[0] + '.json'
                    # Get the full path of the extracted Posts.xml file
                    extracted_posts_xml_file = os.path.join(temp_dir, posts_xml_file)
                    # Read XML data from the extracted Posts.xml file
                    with open(extracted_posts_xml_file, 'r') as xml_file:
                        xml_data = xml_file.read()
                    # Convert XML data to JSON
                    json_str = convert_xml_to_json(xml_data)
                    # Write JSON string to output file
                    with open(os.path.join(folder, output_json_file), 'w') as json_file:
                        json_file.write(json_str)
                    # Remove the extracted Posts.xml file
                    os.remove(extracted_posts_xml_file)
                    # Output message
                    print(f"XML data from '{file}' has been successfully converted to JSON and saved in '{output_json_file}'.")

def main():
    # Create the argument parser
    parser = argparse.ArgumentParser(description='Convert XML data in 7z files to JSON')
    parser.add_argument('folder', type=str, help='Folder containing 7z files')
    args = parser.parse_args()

    # Process all 7z files in the specified folder
    process_7z_files(args.folder)

    # Write the commands_list to a JSON file
    with open('commands.json', 'w') as json_file:
        json.dump(list(set(commands_list)), json_file, indent=4)

    print("All valid terminal commands have been saved to 'commands.json'.")

if __name__ == '__main__':
    main()