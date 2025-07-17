import requests

r = requests.post("https://b7a5bf2e1b58.ngrok-free.app/call-user")
print(r.json())
