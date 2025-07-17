import os
from twilio.rest import Client
from dotenv import load_dotenv
load_dotenv()

def call_user(phone_number, twilio_sid, twilio_auth_token, twilio_phone, public_url):
    client = Client(twilio_sid, twilio_auth_token)
    
    call = client.calls.create(
        to=phone_number,
        from_=twilio_phone,
        url=f"{public_url}/voice"  # Twilio will GET this after connecting the call
    )
    
    print(f"[📞] Calling {phone_number}, SID: {call.sid}")
    return call.sid


# Example usage
call_user(
    phone_number="+97694970947",
    twilio_sid=os.getenv("TWILIO_ACCOUNT_SID"),
    twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
    twilio_phone=os.getenv("TWILIO_PHONE_NUMBER"),
    public_url="https://7826a4714643.ngrok-free.app"
)
