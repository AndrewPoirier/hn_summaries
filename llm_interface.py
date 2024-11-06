import json
from transformers import BartTokenizer, BartForConditionalGeneration

# Load settings from settings.json
with open('llm_settings.json', 'r') as f:
    settings = json.load(f)
    
# Load the tokenizer and model
tokenizer = BartTokenizer.from_pretrained(settings["pretrained_model_name_or_path"])
model = BartForConditionalGeneration.from_pretrained(settings["pretrained_model_name_or_path"])

def summarize(text):
    
    # prompt_text = f"{settings['prompt']} ### {text}"˚
    prompt_text = f"{settings['prompt']} End of prompt. Text begins: {text}"
    # prompt_text = f"{text}"
    
    # Tokenize the input text
    inputs = tokenizer.encode(
        text=prompt_text,
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
        early_stopping=settings["early_stopping"]
    )
    
    # Decode the summary
    summary = tokenizer.decode(
        token_ids=summary_ids[0], 
        skip_special_tokens=settings["skip_special_tokens"])
    
    # if the prompt leaks into the summary, it's not a good summary
    if "Text begins" in summary:
        raise ValueError(f"The summary contains parts of the prompt, indicating a poor summary. Summary: {summary}")        
    
    return summary