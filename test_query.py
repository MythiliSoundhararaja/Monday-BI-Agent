import httpx

url = "http://127.0.0.1:8000/query"

payload = {
    "message": "How's our pipeline looking for the energy sector this quarter?",
    "history": []
}
import requests
import traceback

try:
    url = "http://127.0.0.1:8000/query"
    payload = {
        "message": "“How's our pipeline looking for the energy sector this quarter?",
        "history": []
    }
    
    print("Sending request...")
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")
    
except Exception as e:
    print("Request failed:")
    traceback.print_exc()

with httpx.Client(timeout=30.0) as client:
    response = client.post(url, json=payload)

print("Status:", response.status_code)
print("Body:", response.text)
