import base64
import importlib.util
import json
import os
import sys
import types
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock


def _install_boto_mocks():
    """Instala mocks de boto3 e botocore.exceptions quando não estão no ambiente local."""
    if 'botocore.exceptions' not in sys.modules:
        botocore_mod = types.ModuleType('botocore')
        exceptions_mod = types.ModuleType('botocore.exceptions')

        class BotoCoreError(Exception):
            pass

        class ClientError(Exception):
            def __init__(self, error_response, operation_name):
                self.response = error_response
                self.operation_name = operation_name
                super().__init__(str(error_response))

        exceptions_mod.BotoCoreError = BotoCoreError
        exceptions_mod.ClientError = ClientError
        botocore_mod.exceptions = exceptions_mod
        sys.modules['botocore'] = botocore_mod
        sys.modules['botocore.exceptions'] = exceptions_mod

    if 'boto3' not in sys.modules:
        boto3_mod = types.ModuleType('boto3')
        boto3_mod.client = MagicMock(return_value=MagicMock())
        sys.modules['boto3'] = boto3_mod


def _load_lambda_module(filename, module_name):
    _install_boto_mocks()
    filepath = os.path.join(os.path.dirname(__file__), filename)
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


upload_mod = _load_lambda_module('file-manager-upload.py', 'file_manager_upload')
list_mod = _load_lambda_module('file-manager-list.py', 'file_manager_list')
download_mod = _load_lambda_module('file-manager-download.py', 'file_manager_download')

from botocore.exceptions import ClientError  # noqa: E402


class TestUploadLambda(unittest.TestCase):
    def setUp(self):
        upload_mod.s3 = MagicMock()
        upload_mod.s3.generate_presigned_url.return_value = 'https://s3.example.com/presigned-put'

    def test_options_cors(self):
        res = upload_mod.lambda_handler({'httpMethod': 'OPTIONS'}, None)
        self.assertEqual(res['statusCode'], 200)
        self.assertEqual(res['headers']['Access-Control-Allow-Origin'], '*')

    def test_method_not_allowed(self):
        res = upload_mod.lambda_handler({'httpMethod': 'GET'}, None)
        self.assertEqual(res['statusCode'], 405)

    def test_invalid_json_returns_400(self):
        res = upload_mod.lambda_handler({'httpMethod': 'POST', 'body': '{invalid'}, None)
        self.assertEqual(res['statusCode'], 400)
        self.assertIn('error', json.loads(res['body']))

    def test_missing_filename_returns_400(self):
        res = upload_mod.lambda_handler({'httpMethod': 'POST', 'body': json.dumps({})}, None)
        self.assertEqual(res['statusCode'], 400)

    def test_path_traversal_rejected(self):
        for bad_name in ['../secret.txt', 'dir/file.txt', 'dir\\file.txt', 'bad\x00.txt', '...']:
            res = upload_mod.lambda_handler(
                {'httpMethod': 'POST', 'body': json.dumps({'filename': bad_name})},
                None,
            )
            self.assertEqual(res['statusCode'], 400, msg=f'Should reject {bad_name!r}')

    def test_file_size_over_50mb_returns_413(self):
        over_limit = (50 * 1024 * 1024) + 1
        res = upload_mod.lambda_handler(
            {
                'httpMethod': 'POST',
                'body': json.dumps({'filename': 'video.mp4', 'file_size': over_limit}),
            },
            None,
        )
        self.assertEqual(res['statusCode'], 413)
        body = json.loads(res['body'])
        self.assertEqual(body['max_size_bytes'], 50 * 1024 * 1024)

    def test_invalid_file_size_returns_400(self):
        for bad_size in [0, -10, '1024', True, 12.5]:
            res = upload_mod.lambda_handler(
                {
                    'httpMethod': 'POST',
                    'body': json.dumps({'filename': 'doc.pdf', 'file_size': bad_size}),
                },
                None,
            )
            self.assertEqual(res['statusCode'], 400, msg=f'Should reject size={bad_size!r}')

    def test_valid_upload_sanitizes_and_avoids_collision(self):
        payload = base64.b64encode(
            json.dumps({'filename': 'Relatório Final (v2).pdf', 'file_size': 1024}).encode('utf-8')
        ).decode('utf-8')
        res = upload_mod.lambda_handler(
            {'httpMethod': 'POST', 'body': payload, 'isBase64Encoded': True},
            None,
        )
        self.assertEqual(res['statusCode'], 200)
        body = json.loads(res['body'])
        self.assertEqual(body['upload_url'], 'https://s3.example.com/presigned-put')
        self.assertEqual(body['sanitized_filename'], 'Relatorio_Final_v2.pdf')
        self.assertTrue(body['key'].endswith('_Relatorio_Final_v2.pdf'))
        self.assertEqual(body['max_size_bytes'], 50 * 1024 * 1024)

        call_kwargs = upload_mod.s3.generate_presigned_url.call_args[1]
        self.assertEqual(call_kwargs['Params']['ContentLength'], 1024)

    def test_s3_client_error_returns_500(self):
        upload_mod.s3.generate_presigned_url.side_effect = ClientError(
            {'Error': {'Code': 'InternalError', 'Message': 'boom'}},
            'PutObject',
        )
        res = upload_mod.lambda_handler(
            {'httpMethod': 'POST', 'body': json.dumps({'filename': 'ok.txt'})},
            None,
        )
        self.assertEqual(res['statusCode'], 500)


class TestListLambda(unittest.TestCase):
    def setUp(self):
        list_mod.s3 = MagicMock()

    def test_options_cors(self):
        res = list_mod.lambda_handler({'httpMethod': 'OPTIONS'}, None)
        self.assertEqual(res['statusCode'], 200)

    def test_method_not_allowed(self):
        res = list_mod.lambda_handler({'httpMethod': 'POST'}, None)
        self.assertEqual(res['statusCode'], 405)

    def test_enriches_metadata_and_handles_pagination(self):
        dt = datetime(2026, 11, 13, 12, 30, 0, tzinfo=timezone.utc)
        list_mod.s3.list_objects_v2.side_effect = [
            {
                'Contents': [{'Key': 'doc.pdf', 'Size': 1536, 'LastModified': dt}],
                'IsTruncated': True,
                'NextContinuationToken': 'tok1',
            },
            {
                'Contents': [{'Key': 'README', 'Size': 0, 'LastModified': dt}],
                'IsTruncated': False,
            },
        ]

        res = list_mod.lambda_handler({'httpMethod': 'GET'}, None)
        self.assertEqual(res['statusCode'], 200)
        body = json.loads(res['body'])
        self.assertEqual(body['file_count'], 2)

        first = body['files'][0]
        self.assertEqual(first['key'], 'doc.pdf')
        self.assertEqual(first['extension'], 'pdf')
        self.assertEqual(first['size_bytes'], 1536)
        self.assertEqual(first['size_formatted'], '1.50 KB')
        self.assertEqual(first['last_modified'], '2026-11-13T12:30:00Z')
        self.assertEqual(first['last_modified_iso'], '2026-11-13T12:30:00Z')

        second = body['files'][1]
        self.assertEqual(second['extension'], '')
        self.assertEqual(second['size_formatted'], '0 Bytes')

    def test_s3_error_returns_500(self):
        list_mod.s3.list_objects_v2.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'denied'}},
            'ListObjectsV2',
        )
        res = list_mod.lambda_handler({'httpMethod': 'GET'}, None)
        self.assertEqual(res['statusCode'], 500)


class TestDownloadLambda(unittest.TestCase):
    def setUp(self):
        download_mod.s3 = MagicMock()
        download_mod.s3.head_object.return_value = {'ContentLength': 100}
        download_mod.s3.generate_presigned_url.return_value = 'https://s3.example.com/presigned-get'

    def test_options_cors(self):
        res = download_mod.lambda_handler({'httpMethod': 'OPTIONS'}, None)
        self.assertEqual(res['statusCode'], 200)

    def test_method_not_allowed(self):
        res = download_mod.lambda_handler({'httpMethod': 'POST'}, None)
        self.assertEqual(res['statusCode'], 405)

    def test_missing_key_returns_400(self):
        res = download_mod.lambda_handler({'httpMethod': 'GET', 'queryStringParameters': {}}, None)
        self.assertEqual(res['statusCode'], 400)

    def test_path_traversal_rejected(self):
        for bad_key in ['../etc/passwd', '/root/file.txt', 'a\\b.txt', 'bad\x00key']:
            res = download_mod.lambda_handler(
                {'httpMethod': 'GET', 'queryStringParameters': {'key': bad_key}},
                None,
            )
            self.assertEqual(res['statusCode'], 400, msg=f'Should reject {bad_key!r}')

    def test_not_found_returns_404(self):
        download_mod.s3.head_object.side_effect = ClientError(
            {'Error': {'Code': '404', 'Message': 'Not Found'}},
            'HeadObject',
        )
        res = download_mod.lambda_handler(
            {'httpMethod': 'GET', 'queryStringParameters': {'key': 'missing.txt'}},
            None,
        )
        self.assertEqual(res['statusCode'], 404)

    def test_valid_download_15_minutes(self):
        res = download_mod.lambda_handler(
            {'httpMethod': 'GET', 'queryStringParameters': {'key': 'relatorio.pdf'}},
            None,
        )
        self.assertEqual(res['statusCode'], 200)
        body = json.loads(res['body'])
        self.assertEqual(body['presigned_url'], 'https://s3.example.com/presigned-get')
        self.assertEqual(body['expires_in_seconds'], 900)
        self.assertEqual(body['key'], 'relatorio.pdf')


if __name__ == '__main__':
    unittest.main()
