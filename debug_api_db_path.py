import requests

url = "http://localhost:8100/api/students/"

try:
    response = requests.get(url)
    print(f"Status code: {response.status_code}")
    print("Response body:")
    print(response.text)
except Exception as e:
    print(f"Error calling {url}: {e}") 