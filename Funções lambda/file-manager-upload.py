from datetime import datetime, timezone
import base64
import json
import os
import re
import unicodedata
import uuid

import boto3
from botocore.exceptions import BotoCoreError, ClientError

s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'projeto-cloud-computing-bucket')
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
PRESIGNED_EXPIRATION_SECONDS = int(os.environ.get('PRESIGNED_EXPIRATION_SECONDS', 300))

CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'OPTIONS,POST',
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


def _parse_json_body(event):
    raw_body = event.get('body')
    if raw_body is None or raw_body == '':
        return {}

    if isinstance(raw_body, dict):
        return raw_body

    if not isinstance(raw_body, str):
        raise ValueError('Corpo da requisição inválido.')

    if event.get('isBase64Encoded'):
        try:
            raw_body = base64.b64decode(raw_body).decode('utf-8')
        except Exception as exc:
            raise ValueError('Corpo da requisição em Base64 inválido.') from exc

    try:
        parsed = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise ValueError('JSON inválido no corpo da requisição.') from exc

    if not isinstance(parsed, dict):
        raise ValueError('O corpo da requisição deve ser um objeto JSON.')

    return parsed


def sanitize_filename(filename):
    """Valida e sanitiza o nome do arquivo, evitando path traversal e caracteres inválidos."""
    if not isinstance(filename, str):
        raise ValueError('O campo "filename" deve ser uma string.')

    cleaned = filename.strip()
    if not cleaned:
        raise ValueError('O parâmetro "filename" é obrigatório.')

    if '\x00' in cleaned or any(ord(ch) < 32 for ch in cleaned):
        raise ValueError('Nome de arquivo contém caracteres de controle inválidos.')

    # Impede path traversal (ex.: ../../arquivo.txt ou caminhos com barra)
    if '..' in cleaned or '/' in cleaned or '\\' in cleaned:
        raise ValueError('Nome de arquivo inválido: caminhos de diretório não são permitidos.')

    # Normaliza acentos para ASCII seguro
    normalized = unicodedata.normalize('NFKD', cleaned).encode('ascii', 'ignore').decode('ascii')

    stem, ext = os.path.splitext(normalized)
    safe_stem = re.sub(r'[^a-zA-Z0-9._-]', '_', stem)
    safe_stem = re.sub(r'_+', '_', safe_stem).strip('._-')

    safe_ext = re.sub(r'[^a-zA-Z0-9.]', '', ext).lower()
    if safe_ext and not safe_ext.startswith('.'):
        safe_ext = f'.{safe_ext}'

    if not safe_stem:
        raise ValueError('Nome de arquivo inválido após sanitização.')

    safe_stem = safe_stem[:150]
    safe_ext = safe_ext[:20]

    return f'{safe_stem}{safe_ext}'


def generate_unique_key(safe_filename):
    """Gera uma chave única no S3 com timestamp UTC e UUID curto para evitar colisões."""
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    short_id = uuid.uuid4().hex[:8]
    return f'{timestamp}_{short_id}_{safe_filename}'


def validate_file_size(raw_size):
    """Valida o tamanho do arquivo (limite máximo de 50 MB) quando informado."""
    if raw_size is None:
        return None

    if isinstance(raw_size, bool) or not isinstance(raw_size, (int, float)):
        raise ValueError('O campo "file_size" deve ser um número inteiro em bytes.')

    if isinstance(raw_size, float) and not raw_size.is_integer():
        raise ValueError('O campo "file_size" deve ser um número inteiro em bytes.')

    size_bytes = int(raw_size)
    if size_bytes <= 0:
        raise ValueError('O tamanho do arquivo deve ser maior que zero bytes.')

    if size_bytes > MAX_FILE_SIZE_BYTES:
        raise OverflowError(
            f'Arquivo excede o limite máximo permitido de 50 MB ({MAX_FILE_SIZE_BYTES} bytes).'
        )

    return size_bytes


def lambda_handler(event, context):
    if not isinstance(event, dict):
        return _response(400, {'error': 'Evento inválido recebido pela função.'})

    method = _get_http_method(event)
    if method == 'OPTIONS':
        return _response(200, {'message': 'CORS OK'})

    if method and method != 'POST':
        return _response(405, {'error': f'Método {method} não permitido. Utilize POST.'})

    try:
        body = _parse_json_body(event)
    except ValueError as exc:
        return _response(400, {'error': str(exc)})

    raw_filename = body.get('filename')
    try:
        safe_filename = sanitize_filename(raw_filename)
    except ValueError as exc:
        return _response(400, {'error': str(exc)})

    raw_size = body.get('file_size') if 'file_size' in body else body.get('size')
    try:
        file_size = validate_file_size(raw_size)
    except OverflowError as exc:
        return _response(413, {'error': str(exc), 'max_size_bytes': MAX_FILE_SIZE_BYTES})
    except ValueError as exc:
        return _response(400, {'error': str(exc)})

    unique_key = generate_unique_key(safe_filename)

    presign_params = {
        'Bucket': BUCKET_NAME,
        'Key': unique_key,
    }
    if file_size is not None:
        presign_params['ContentLength'] = file_size

    content_type = body.get('content_type')
    if isinstance(content_type, str) and content_type.strip():
        presign_params['ContentType'] = content_type.strip()[:128]

    try:
        presigned_url = s3.generate_presigned_url(
            'put_object',
            Params=presign_params,
            ExpiresIn=PRESIGNED_EXPIRATION_SECONDS,
        )
    except (ClientError, BotoCoreError) as exc:
        return _response(500, {'error': 'Erro ao gerar URL de upload no S3.', 'details': str(exc)})
    except Exception:
        return _response(500, {'error': 'Erro interno inesperado ao processar o upload.'})

    return _response(
        200,
        {
            'upload_url': presigned_url,
            'key': unique_key,
            'sanitized_filename': safe_filename,
            'expires_in_seconds': PRESIGNED_EXPIRATION_SECONDS,
            'max_size_bytes': MAX_FILE_SIZE_BYTES,
        },
    )
