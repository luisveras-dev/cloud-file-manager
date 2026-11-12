import requests
import os

API_URL = "https://veicu6cgzb.execute-api.us-east-2.amazonaws.com/prod"

file_path = "/home/antonino/Downloads/photo.jpg"
#substituir o endereço acima pelo caminho do arquivo que deseja enviar, substituindo o nome do arquivo no final do caminho, caso queira enviar outro arquivo.

# Get presigned URL
upload_url = requests.post(API_URL, json={"filename": os.path.basename(file_path)}).json()["upload_url"]

# Upload the file
with open(file_path, "rb") as f:
    requests.put(upload_url, data=f)

print("Upload done!")