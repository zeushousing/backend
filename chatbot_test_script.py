import requests

BASE_URL = "http://127.0.0.1:8000/api/v1/"  # For API endpoints under api/v1/
TOKEN_BASE_URL = "http://127.0.0.1:8000/api/"  # For token endpoints
USERNAME = "tenant"
PASSWORD = "Venant4321"

# Get JWT token
def get_token():
    url = f"{TOKEN_BASE_URL}token/"
    response = requests.post(url, json={"username": USERNAME, "password": PASSWORD})
    print(f"Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")
    return response.json()["access"]

# Test chatbot
def test_chatbot(message, token):
    url = f"{BASE_URL}users/chat/"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.post(url, json={"message": message}, headers=headers)
    print(f"Message: {message}")
    print(f"Response: {response.json()['response']}\n")

# Run tests
token = get_token()
messages = [
    "Check my booking status",
    "Show me available properties",
    "I need help",
    "Tell me about Test Property",
    "What’s up?"
]
for msg in messages:
    test_chatbot(msg, token)