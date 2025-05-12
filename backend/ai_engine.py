from transformers import pipeline

pipe = pipeline("text-generation", model="distilgpt2")  # Tiny, fast

def get_cultural_advice(question, culture):
    prompt = f"As a cultural wisdom expert from {culture}, give advice on: {question}"
    result = pipe(prompt, max_new_tokens=60)[0]['generated_text']
    return result.replace(prompt, '').strip()
