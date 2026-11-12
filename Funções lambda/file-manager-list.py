import boto3
import json

s3 = boto3.client('s3')

def lambda_handler(event, context):
    bucket_name = 'projeto-cloud-computing-bucket'
    
    response = s3.list_objects_v2(Bucket=bucket_name)
    
    files = []
    for obj in response.get('Contents', []):
        files.append({
            'key': obj['Key'],
            'size_bytes': obj['Size'],
            'last_modified': str(obj['LastModified'])
        })
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,GET'
        },
        'body': json.dumps({
            'bucket': bucket_name,
            'file_count': len(files),
            'files': files
        })
    }
