import boto3
from botocore.exceptions import ClientError
import json

s3 = boto3.client('s3')

def lambda_handler(event, context):

    print("EVENT:", json.dumps(event))

    query_params = event.get('queryStringParameters') or {}
    file_key = query_params.get('key') or event.get('key')

    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'OPTIONS,GET'
    }

    if not file_key:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': 'Missing required parameter: key'})
        }


    bucket_name = 'projeto-cloud-computing-bucket'
    expiration  =  3600  
    
    try:
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': file_key},
            ExpiresIn=expiration
        )
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'presigned_url': url,
                'expires_in_seconds': expiration
            })
        }
    except ClientError as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
