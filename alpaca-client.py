import requests
import json
import argparse

def send_prompt(url, instruction, input_text=None):
    # Prepare the request data
    data = {'instruction': instruction}
    if input_text is not None:
        data['input'] = input_text

    # Send the POST request to the Alpaca web service
    response = requests.post(url, json=data)

    # Check if the request was successful
    if response.ok:
        # Print the response from the web service
        response_data = response.json()
        print(response_data['response'])
    else:
        print(f"Request failed. Status code: {response.status_code}")
        print(response.text)

if __name__ == '__main__':
    # Set up command-line argument parser
    parser = argparse.ArgumentParser(description='Alpaca Web Service Client')
    parser.add_argument('-u', '--url', type=str, default='http://127.0.0.1:5791/alpaca', help='URL of the Alpaca web service')
    parser.add_argument('-i', '--instruction', type=str, required=True, help='Instruction for the Alpaca web service')
    parser.add_argument('--input', type=str, default=None, help='Input text for the Alpaca web service (optional)')

    # Parse command-line arguments
    args = parser.parse_args()

    # Send the instruction and input to the Alpaca web service
    send_prompt(args.url, args.instruction, args.input)
