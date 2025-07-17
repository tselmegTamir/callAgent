import requests

r = requests.post("https://805ae74452fa.ngrok-free.app/call-user")
print(r.json())
