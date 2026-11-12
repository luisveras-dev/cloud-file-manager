import requests

url = "https://cue8igv428.execute-api.us-east-2.amazonaws.com/prod"
response = requests.get(url)
# esta chamada diz para você quais arquivos estão no bucket

print("Status:", response.status_code)
print("Files:", response.json())
