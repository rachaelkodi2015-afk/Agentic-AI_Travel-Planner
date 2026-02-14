"""
Test which OpenAI models you have access to
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print("="*60)
print("Testing OpenAI Model Access")
print("="*60)

models_to_test = [
    "gpt-3.5-turbo",
    "gpt-4o-mini", 
    "gpt-4o",
    "gpt-4-turbo",
    "gpt-4"
]

print("\nTesting models with a simple request...\n")

working_models = []

for model in models_to_test:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say 'hello'"}],
            max_tokens=5
        )
        print(f"✓ {model} - WORKS!")
        working_models.append(model)
    except Exception as e:
        error_msg = str(e)
        if "model_not_found" in error_msg or "does not have access" in error_msg:
            print(f"✗ {model} - No access")
        elif "insufficient_quota" in error_msg:
            print(f"⚠ {model} - No credits (need to add payment)")
        else:
            print(f"✗ {model} - Error: {error_msg[:50]}")

print("\n" + "="*60)
if working_models:
    print("Models you can use:")
    for model in working_models:
        print(f"  • {model}")
    print(f"\nRecommendation: Use '{working_models[0]}'")
else:
    print("⚠ No models are working!")
    print("\nPossible issues:")
    print("1. API key is invalid")
    print("2. No payment method on file (OpenAI requires billing)")
    print("3. Quota exceeded")
    print("\nVisit: https://platform.openai.com/settings/organization/billing")
print("="*60)
