import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3')

def lambda_handler(event, context):
    bucket_name = 'projeto-cloud-computing-bucket'
    file_key    = event['key']
    expiration  =  3600  
    
    try:
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': file_key},
            ExpiresIn=expiration
        )
        return {
            'statusCode': 200,
            'presigned_url': url,
            'expires_in_seconds': expiration
        }
    except ClientError as e:
        return {
            'statusCode': 500,
            'error': str(e)
        }