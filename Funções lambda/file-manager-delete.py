import boto3
from botocore.exceptions import ClientError
import json

s3 = boto3.client('s3')
BUCKET_NAME = 'projeto-cloud-computing-bucket'


def lambda_handler(event, context):
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'OPTIONS,DELETE'
    }

    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': 'CORS OK'})
        }

    query_params = event.get('queryStringParameters') or {}
    body = {}
    if event.get('body'):
        try:
            body = json.loads(event.get('body'))
        except json.JSONDecodeError:
            body = {}

    file_key = query_params.get('key') or body.get('key') or event.get('key')

    if not file_key:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': 'Missing required parameter: key'})
        }

    try:
        s3.delete_object(
            Bucket=BUCKET_NAME,
            Key=file_key
        )
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': f'File "{file_key}" deleted successfully',
                'key': file_key
            })
        }
    except ClientError as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
