import os
import requests

api_key = os.getenv("GROK_API_KEY")

if not api_key:
    print("API key not found")
    exit()

response = requests.get(
    "https://api.x.ai/v1/models",
    headers={
        "Authorization": f"Bearer {api_key}"
    }
)

print("Status:", response.status_code)
print("Response:", response.text)
