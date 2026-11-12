import boto3
import json

s3 = boto3.client('s3')
BUCKET_NAME = 'projeto-cloud-computing-bucket'

def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'OPTIONS,POST'
    }

    # Resposta rápida para preflight CORS do navegador
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': 'CORS OK'})
        }
    
    body = json.loads(event.get("body") or "{}")
    file_name = body.get("filename")

    if not file_name:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"error": "filename parameter is required"})
        }

    presigned_url = s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": BUCKET_NAME, "Key": file_name},
        ExpiresIn=300
    )
    
    return {
        "statusCode": 200,
        "headers": headers,
        "body": json.dumps({"upload_url": presigned_url})
    }
