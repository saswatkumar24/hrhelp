#!/usr/bin/env python3

import google.generativeai as genai
from config import Config

# Configure the API key
genai.configure(api_key=Config.GOOGLE_API_KEY)

print("Available Gemini models:")
print("-" * 40)

try:
    # List available models
    for model in genai.list_models():
        print(f"Model: {model.name}")
        print(f"  Display name: {model.display_name}")
        print(f"  Supported methods: {model.supported_generation_methods}")
        print("-" * 40)
        
except Exception as e:
    print(f"Error listing models: {e}")
    
    # Try with common model names
    test_models = [
        "gemini-pro",
        "gemini-1.5-pro", 
        "gemini-1.5-flash",
        "models/gemini-pro",
        "models/gemini-1.5-pro",
        "models/gemini-1.5-flash"
    ]
    
    print("\nTesting common model names:")
    print("-" * 40)
    
    for model_name in test_models:
        try:
            model = genai.GenerativeModel(model_name)
            print(f"✓ {model_name} - Available")
        except Exception as e:
            print(f"✗ {model_name} - Error: {str(e)[:100]}...")
