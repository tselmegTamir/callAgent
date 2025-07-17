import requests
import os
from dotenv import load_dotenv  
load_dotenv()  # Load environment variables from .env file

def test_vapi_tts_call():
    vapi_api_key = os.getenv("VAPI_API_KEY")
    assistant_id = os.getenv("VAPI_ASSISTANT_ID")
    phone_number_id = os.getenv("VAPI_PHONE_NUMBER_ID")
    customer_number = "+97694970947"  # your test number

    url = "https://api.vapi.ai/call"
    headers = {
        "Authorization": f"Bearer {vapi_api_key}",
        "Content-Type": "application/json"
    }
    body = {
        "assistant": { "id": assistant_id },
        "phoneNumberId": phone_number_id,
        "customer": { "number": customer_number }
    }

    response = requests.post(url, json=body, headers=headers)
    if response.status_code == 200:
        call_data = response.json()
        print("✅ Call created:", call_data["id"])
        return call_data
    else:
        print("❌ Failed to create call:", response.status_code, response.text)

test_vapi_tts_call()
