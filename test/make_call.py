# Download the helper library from https://www.twilio.com/docs/python/install
import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
from twilio.rest import Client

# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
client = Client(account_sid, auth_token)

call = client.calls.create(
    url="http://demo.twilio.com/docs/voice.xml",
    to="+97694970947",
    from_=os.getenv("TWILIO_PHONE_NUMBER"),
)

print(call.sid)