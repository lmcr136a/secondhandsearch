import requests
import json

data = {
    "key1": "value1"
}

url = "https://lmcr136a.wixsite.com/secondhandsearch/_functions-dev/fromPython"


response = requests.post(url, data=data, timeout=2)

if response.status_code == 200:
    print(json.loads(response.text))
else:
    print(response.text)
    print(response.status_code)
