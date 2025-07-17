import requests

r = requests.post("https://bfab2dafefc4.ngrok-free.app/call-user")
print(r.json())
