from flask import Flask, request, jsonify
import torch
from peft import PeftModel
import transformers
import logging
from transformers import LlamaTokenizer, LlamaForCausalLM, GenerationConfig
import os


# Set up logging
log_file = 'alpaca-web.log' # '/var/log/alpaca-web.log'
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')

print("Loading tokenizer")
tokenizer = LlamaTokenizer.from_pretrained("decapoda-research/llama-7b-hf")

BASE_MODEL = "decapoda-research/llama-7b-hf"
LORA_WEIGHTS = "tloen/alpaca-lora-7b"

if torch.cuda.is_available():
    print("CUDA found")
    device = "cuda"
else:
    print("No CUDA devices found.")
    device = "cpu"

try:
    if torch.backends.mps.is_available():
        device = "mps"
except:
    pass


if device == "cuda":
    num_devices = torch.cuda.device_count()
    bits8 = False
    for i in range(num_devices):
        device_name = torch.cuda.get_device_name(i)
        cc_major, cc_minor = torch.cuda.get_device_capability(i)
        if cc_major <= 7 and cc_minor < 5:
            print(f"GPU needs compute capability 7.5 or great for 16-bit mode. Installed device supports {cc_major}.{cc_minor}. Falling back to 8-bit mode.")
            bits8 = True

        device_memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)

        if device_memory < 12:
            print("GPU needs at least 12GB of VRAM to run. Installed device has {device_memory}GB. Falling back to CPU. Except slow responses.")
            device = "cpu"
        elif device_memory < 24 and not bits8:
            print(f"At least 24GB of VRAM is recommended to run in 16-bit mode. Installed device has {device_memory}GB. Falling back to 8-bit mode.")

print("Loading Llama...")
if device == "cuda":
    model = LlamaForCausalLM.from_pretrained(
        BASE_MODEL,
        load_in_8bit=bits8,
        torch_dtype=torch.float16,
        device_map="auto",
    )
    model = PeftModel.from_pretrained(
        model, LORA_WEIGHTS, torch_dtype=torch.float16, force_download=True
    )
elif device == "mps":
    model = LlamaForCausalLM.from_pretrained(
        BASE_MODEL,
        device_map={"": device},
        torch_dtype=torch.float16,
    )
    model = PeftModel.from_pretrained(
        model,
        LORA_WEIGHTS,
        device_map={"": device},
        torch_dtype=torch.float16,
    )
else:
    model = LlamaForCausalLM.from_pretrained(
        BASE_MODEL, device_map={"": device}, low_cpu_mem_usage=True
    )
    model = PeftModel.from_pretrained(
        model,
        LORA_WEIGHTS,
        device_map={"": device},
    )
print("Llama loaded.")

def generate_prompt(instruction, input=None):
    if input:
        return f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Input:
{input}

### Response:"""
    else:
        return f"""Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Response:"""

if device != "cpu":
    model.half()
model.eval()
if torch.__version__ >= "2":
    model = torch.compile(model)


def evaluate(
    instruction,
    input=None,
    temperature=0.1,
    top_p=0.75,
    top_k=40,
    num_beams=4,
    max_new_tokens=128,
    **kwargs,
):
    prompt = generate_prompt(instruction, input)
    inputs = tokenizer(prompt, return_tensors="pt")
    input_ids = inputs["input_ids"].to(device)
    generation_config = GenerationConfig(
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        num_beams=num_beams,
        **kwargs,
    )
    with torch.no_grad():
        generation_output = model.generate(
            input_ids=input_ids,
            generation_config=generation_config,
            return_dict_in_generate=True,
            output_scores=True,
            max_new_tokens=max_new_tokens,
        )
    s = generation_output.sequences[0]
    output = tokenizer.decode(s)
    return output.split("### Response:")[1].strip()

app = Flask(__name__)

# Define the endpoint
@app.route('/alpaca', methods=['POST'])
def alpaca():
    # Extract instruction and input from the request data
    data = request.get_json()
    instruction = data.get('instruction', '')
    input_text = data.get('input', None)

    # Log the request data
    logging.info(f'request: instruction="{instruction}", input="{input_text}"')

    # Use the evaluate function to generate the response
    response = evaluate(instruction, input_text)

    # Log the response data
    logging.info(f'response: "{response}"')

    # Return the response as JSON
    return jsonify({'response': response})

if __name__ == '__main__':
    # Start the Flask application
    print("Starting flask.")
    app.run(host='127.0.0.1', port="5791")
