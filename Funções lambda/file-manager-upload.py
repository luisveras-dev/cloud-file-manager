import boto3
import json

s3_client = boto3.client('s3')
BUCKET_NAME = 'projeto-cloud-computing-bucket'

def lambda_handler(event, context):
    file_content = event.get('file_content')
    file_name = event.get('file_name')
    
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=file_name,
        Body=file_content.encode('utf-8')
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps(f'File {file_name} uploaded successfully!')
    }