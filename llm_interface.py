import json
from transformers import BartTokenizer, BartForConditionalGeneration

# Load settings from settings.json
with open('llm_settings.json', 'r') as f:
    settings = json.load(f)
    
# Load the tokenizer and model
tokenizer = BartTokenizer.from_pretrained(settings["pretrained_model_name_or_path"])
model = BartForConditionalGeneration.from_pretrained(settings["pretrained_model_name_or_path"])

def summarize(text):
    # TODO: error handling
    # TODO: learn how to adjust the model parameters
    
    # Tokenize the input text
    inputs = tokenizer.encode(
        text=settings["prompt"] + text,
        return_tensors="pt", 
        max_length=settings["max_length"], 
        truncation=True
    )
    
    # Generate summary
    summary_ids = model.generate(
        inputs=inputs, 
        max_length=settings["summary_max_length"], 
        min_length=settings["min_length"], 
        length_penalty=settings["length_penalty"], 
        num_beams=settings["num_beams"], 
        early_stopping=settings["early_stopping"] # CHANGED THIS TO FALSE, HAVE NOT TESTED
    )
    
    # Decode the summary
    summary = tokenizer.decode(
        token_ids=summary_ids[0], 
        skip_special_tokens=settings["skip_special_tokens"])
    
    # Remove the prompt from the summary, NOT TESTED
    if settings["prompt"] in summary:
        summary = summary.split(settings["prompt"])[1]
    
    return summary