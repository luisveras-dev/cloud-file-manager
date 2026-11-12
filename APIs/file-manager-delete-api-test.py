import requests

# Substituir pela URL do API Gateway gerada para a Lambda de exclusão
url = "https://77szunm20c.execute-api.us-east-2.amazonaws.com/prod"
response = requests.delete(url, params={"key": "test-file.txt"})

print("Status code:", response.status_code)
print("Response:", response.json())
