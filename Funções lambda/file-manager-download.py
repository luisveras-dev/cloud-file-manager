import json
import os
import re

import boto3
from botocore.exceptions import BotoCoreError, ClientError

s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'projeto-cloud-computing-bucket')
PRESIGNED_EXPIRATION_SECONDS = int(os.environ.get('PRESIGNED_URL_EXPIRATION', 900))  # 15 minutos

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


def validate_object_key(raw_key):
    """Valida a chave do objeto no S3 para evitar path traversal e entradas inválidas."""
    if not isinstance(raw_key, str):
        raise ValueError('O parâmetro "key" é obrigatório e deve ser uma string.')

    cleaned = raw_key.strip()
    if not cleaned:
        raise ValueError('O parâmetro obrigatório "key" não foi informado.')

    if len(cleaned) > 1024:
        raise ValueError('O parâmetro "key" excede o tamanho máximo permitido.')

    if '\x00' in cleaned or any(ord(ch) < 32 for ch in cleaned):
        raise ValueError('O parâmetro "key" contém caracteres de controle inválidos.')

    if '..' in cleaned or cleaned.startswith('/') or '\\' in cleaned:
        raise ValueError('Chave de arquivo inválida: path traversal não é permitido.')

    return cleaned


def _safe_disposition_filename(key):
    basename = os.path.basename(key) or 'download'
    return re.sub(r'["\r\n]', '_', basename)


def lambda_handler(event, context):
    if not isinstance(event, dict):
        return _response(400, {'error': 'Evento inválido recebido pela função.'})

    method = _get_http_method(event)
    if method == 'OPTIONS':
        return _response(200, {'message': 'CORS OK'})

    if method and method != 'GET':
        return _response(405, {'error': f'Método {method} não permitido. Utilize GET.'})

    query_params = event.get('queryStringParameters')
    if query_params is not None and not isinstance(query_params, dict):
        return _response(400, {'error': 'Parâmetros de consulta inválidos.'})

    query_params = query_params or {}
    raw_key = query_params.get('key') if 'key' in query_params else event.get('key')

    try:
        file_key = validate_object_key(raw_key)
    except ValueError as exc:
        return _response(400, {'error': str(exc)})

    try:
        s3.head_object(Bucket=BUCKET_NAME, Key=file_key)
    except ClientError as exc:
        error_code = str(exc.response.get('Error', {}).get('Code', ''))
        if error_code in ('404', 'NoSuchKey', 'NotFound'):
            return _response(404, {'error': 'Arquivo não encontrado no bucket S3.'})
        return _response(500, {'error': 'Erro ao verificar arquivo no S3.', 'details': str(exc)})
    except BotoCoreError as exc:
        return _response(500, {'error': 'Erro de comunicação com o S3.', 'details': str(exc)})
    except Exception:
        return _response(500, {'error': 'Erro interno inesperado ao verificar o arquivo.'})

    try:
        safe_name = _safe_disposition_filename(file_key)
        url = s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': file_key,
                'ResponseContentDisposition': f'attachment; filename="{safe_name}"',
            },
            ExpiresIn=PRESIGNED_EXPIRATION_SECONDS,
        )
        return _response(
            200,
            {
                'presigned_url': url,
                'key': file_key,
                'expires_in_seconds': PRESIGNED_EXPIRATION_SECONDS,
            },
        )
    except (ClientError, BotoCoreError) as exc:
        return _response(500, {'error': 'Erro ao gerar URL de download.', 'details': str(exc)})
    except Exception:
        return _response(500, {'error': 'Erro interno inesperado ao gerar URL de download.'})
