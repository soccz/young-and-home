
import os

try:
    key = os.getenv("OPENAI_API_KEY")
    print(f"Key from env: '{key}'")
    print(f"Type: {type(key)}")
    print(f"Bool value: {bool(key)}")
except Exception as e:
    print(f"Error: {e}")
