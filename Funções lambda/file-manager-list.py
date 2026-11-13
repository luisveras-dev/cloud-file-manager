from datetime import datetime, timezone
import json
import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError

s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'projeto-cloud-computing-bucket')

CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'OPTIONS,GET',
}


def _response(status_code, payload):
    return {
        'statusCode': status_code,
        'headers': CORS_HEADERS,
        'body': json.dumps(payload, ensure_ascii=False),
    }


def _get_http_method(event):
    if not isinstance(event, dict):
        return None
    return (
        event.get('httpMethod')
        or event.get('requestContext', {}).get('http', {}).get('method')
    )


def format_size(size_bytes):
    """Formata tamanho em bytes para unidade legível (Bytes, KB, MB, GB)."""
    if not size_bytes or size_bytes <= 0:
        return '0 Bytes'

    units = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    value = float(size_bytes)
    unit_index = 0
    while value >= 1024 and unit_index < len(units) - 1:
        value /= 1024.0
        unit_index += 1

    if unit_index == 0:
        return f'{int(value)} Bytes'
    return f'{value:.2f} {units[unit_index]}'


def extract_extension(key):
    """Extrai a extensão do arquivo em minúsculas (sem ponto)."""
    _, ext = os.path.splitext(key or '')
    return ext.lstrip('.').lower()


def format_iso_date(last_modified):
    """Converte datetime do S3 para string ISO 8601 em UTC."""
    if isinstance(last_modified, datetime):
        dt = last_modified
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
    return str(last_modified) if last_modified is not None else None


def lambda_handler(event, context):
    if event is not None and not isinstance(event, dict):
        return _response(400, {'error': 'Evento inválido recebido pela função.'})

    method = _get_http_method(event)
    if method == 'OPTIONS':
        return _response(200, {'message': 'CORS OK'})

    if method and method != 'GET':
        return _response(405, {'error': f'Método {method} não permitido. Utilize GET.'})

    files = []
    continuation_token = None

    try:
        while True:
            params = {'Bucket': BUCKET_NAME}
            if continuation_token:
                params['ContinuationToken'] = continuation_token

            response = s3.list_objects_v2(**params)

            for obj in response.get('Contents', []):
                key = obj.get('Key', '')
                size_bytes = int(obj.get('Size', 0))
                iso_date = format_iso_date(obj.get('LastModified'))

                files.append({
                    'key': key,
                    'extension': extract_extension(key),
                    'size_bytes': size_bytes,
                    'size_formatted': format_size(size_bytes),
                    'last_modified': iso_date,
                    'last_modified_iso': iso_date,
                })

            if not response.get('IsTruncated'):
                break
            continuation_token = response.get('NextContinuationToken')
    except (ClientError, BotoCoreError) as exc:
        return _response(500, {'error': 'Erro ao listar arquivos do bucket S3.', 'details': str(exc)})
    except Exception:
        return _response(500, {'error': 'Erro interno inesperado ao listar arquivos.'})

    return _response(
        200,
        {
            'bucket': BUCKET_NAME,
            'file_count': len(files),
            'files': files,
        },
    )
