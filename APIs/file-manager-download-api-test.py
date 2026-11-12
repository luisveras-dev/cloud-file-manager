import requests

url = "https://87oyrf9w8a.execute-api.us-east-2.amazonaws.com/prod"
response = requests.get(url, params={"key": "test-file.txt"})
# substituir test-file.txt pelo arquivo no bucket que você deseja baixar, use file-manager-list-api-test.py para saber quais arquivos estão no bucket

print("Status code:", response.status_code)
print("Response:", response.json())
