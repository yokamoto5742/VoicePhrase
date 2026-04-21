from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

from external_service.google_stt_api import (
    GoogleSttClient,
    setup_google_stt_client,
    transcribe_audio,
    validate_audio_file,
)
from tests.conftest import dict_to_app_config

_BASE_CONFIG = {'GOOGLE_STT': {'MODEL': 'chirp_3', 'LANGUAGE': 'ja-JP'}}


class TestSetupGoogleSttClient:

    @patch('external_service.google_stt_api.SpeechClient')
    @patch('external_service.google_stt_api.load_env_variables')
    def test_setup_client_success(self, mock_load_env, mock_speech_client):
        """正常系: 必要な環境変数が設定されている場合"""
        mock_load_env.return_value = {
            'GOOGLE_APPLICATION_CREDENTIALS': '/path/to/key.json',
            'GCP_PROJECT_ID': 'my-project',
            'GCP_LOCATION': 'us-central1',
        }
        mock_client_instance = Mock()
        mock_speech_client.return_value = mock_client_instance

        result = setup_google_stt_client()

        assert isinstance(result, GoogleSttClient)
        assert result.speech_client == mock_client_instance
        assert result.project_id == 'my-project'
        assert result.location == 'us-central1'

    @patch('external_service.google_stt_api.SpeechClient')
    @patch('external_service.google_stt_api.load_env_variables')
    def test_setup_client_default_location(self, mock_load_env, mock_speech_client):
        """正常系: GCP_LOCATIONが未設定の場合はglobalを使用"""
        mock_load_env.return_value = {
            'GOOGLE_APPLICATION_CREDENTIALS': '/path/to/key.json',
            'GCP_PROJECT_ID': 'my-project',
        }
        mock_speech_client.return_value = Mock()

        result = setup_google_stt_client()

        assert result.location == 'global'

    @patch('external_service.google_stt_api.load_env_variables')
    def test_setup_client_no_credentials(self, mock_load_env):
        """異常系: GOOGLE_APPLICATION_CREDENTIALSが未設定"""
        mock_load_env.return_value = {'GCP_PROJECT_ID': 'my-project'}

        with pytest.raises(ValueError, match='GOOGLE_APPLICATION_CREDENTIALSが未設定です'):
            setup_google_stt_client()

    @patch('external_service.google_stt_api.load_env_variables')
    def test_setup_client_no_project_id(self, mock_load_env):
        """異常系: GCP_PROJECT_IDが未設定"""
        mock_load_env.return_value = {
            'GOOGLE_APPLICATION_CREDENTIALS': '/path/to/key.json',
        }

        with pytest.raises(ValueError, match='GCP_PROJECT_IDが未設定です'):
            setup_google_stt_client()


class TestValidateAudioFile:

    def test_validate_empty_path(self):
        """異常系: ファイルパスが空文字列"""
        is_valid, error_msg = validate_audio_file('')

        assert is_valid is False
        assert error_msg == '音声ファイルパスが未指定です'

    @patch('external_service.google_stt_api.os.path.exists')
    def test_validate_file_not_exists(self, mock_exists):
        """異常系: ファイルが存在しない"""
        mock_exists.return_value = False
        file_path = '/test/path/audio.wav'

        is_valid, error_msg = validate_audio_file(file_path)

        assert is_valid is False
        assert error_msg == f'音声ファイルが存在しません: {file_path}'

    @patch('external_service.google_stt_api.os.path.getsize')
    @patch('external_service.google_stt_api.os.path.exists')
    def test_validate_zero_size_file(self, mock_exists, mock_getsize):
        """異常系: ファイルサイズが0バイト"""
        mock_exists.return_value = True
        mock_getsize.return_value = 0

        is_valid, error_msg = validate_audio_file('/test/audio.wav')

        assert is_valid is False
        assert error_msg == '音声ファイルサイズが0バイトです'

    @patch('external_service.google_stt_api.os.path.getsize')
    @patch('external_service.google_stt_api.os.path.exists')
    def test_validate_success(self, mock_exists, mock_getsize):
        """正常系: 有効なファイル"""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        is_valid, error_msg = validate_audio_file('/test/audio.wav')

        assert is_valid is True
        assert error_msg is None


def _make_client(project_id: str = 'my-project', location: str = 'global') -> GoogleSttClient:
    return GoogleSttClient(
        speech_client=Mock(),
        project_id=project_id,
        location=location,
    )


class TestTranscribeAudio:

    def setup_method(self):
        self.mock_config = dict_to_app_config(_BASE_CONFIG)
        self.mock_client = _make_client()

    def test_transcribe_empty_file_path(self):
        """異常系: ファイルパスが空"""
        result = transcribe_audio('', self.mock_config, self.mock_client)
        assert result is None

    @patch('external_service.google_stt_api.os.path.exists')
    def test_transcribe_file_not_exists(self, mock_exists):
        """異常系: ファイルが存在しない"""
        mock_exists.return_value = False

        result = transcribe_audio('/test/nonexistent.wav', self.mock_config, self.mock_client)
        assert result is None

    @patch('external_service.google_stt_api.os.path.getsize')
    @patch('external_service.google_stt_api.os.path.exists')
    def test_transcribe_zero_size_file(self, mock_exists, mock_getsize):
        """異常系: ファイルサイズが0バイト"""
        mock_exists.return_value = True
        mock_getsize.return_value = 0

        result = transcribe_audio('/test/empty.wav', self.mock_config, self.mock_client)
        assert result is None

    @patch('builtins.open', new_callable=mock_open, read_data=b'audio_data')
    @patch('external_service.google_stt_api.os.path.getsize')
    @patch('external_service.google_stt_api.os.path.exists')
    def test_transcribe_success(self, mock_exists, mock_getsize, _mock_file):
        """正常系: 文字起こし成功"""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        mock_alternative = Mock()
        mock_alternative.transcript = '文字起こし結果'
        mock_result = Mock()
        mock_result.alternatives = [mock_alternative]
        mock_response = Mock()
        mock_response.results = [mock_result]
        self.mock_client.speech_client.recognize.return_value = mock_response

        result = transcribe_audio('/test/audio.wav', self.mock_config, self.mock_client)

        assert result == '文字起こし結果'
        self.mock_client.speech_client.recognize.assert_called_once()

    @patch('builtins.open', new_callable=mock_open, read_data=b'audio_data')
    @patch('external_service.google_stt_api.os.path.getsize')
    @patch('external_service.google_stt_api.os.path.exists')
    def test_transcribe_multiple_results(self, mock_exists, mock_getsize, _mock_file):
        """正常系: 複数のresultを結合する"""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        def _make_result(text: str) -> Mock:
            alt = Mock()
            alt.transcript = text
            r = Mock()
            r.alternatives = [alt]
            return r

        mock_response = Mock()
        mock_response.results = [_make_result('こんにちは'), _make_result('世界')]
        self.mock_client.speech_client.recognize.return_value = mock_response

        result = transcribe_audio('/test/audio.wav', self.mock_config, self.mock_client)

        assert result == 'こんにちは世界'

    @patch('builtins.open', new_callable=mock_open, read_data=b'audio_data')
    @patch('external_service.google_stt_api.os.path.getsize')
    @patch('external_service.google_stt_api.os.path.exists')
    def test_transcribe_empty_results(self, mock_exists, mock_getsize, _mock_file):
        """正常系: 文字起こし結果が空"""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        mock_response = Mock()
        mock_response.results = []
        self.mock_client.speech_client.recognize.return_value = mock_response

        result = transcribe_audio('/test/audio.wav', self.mock_config, self.mock_client)

        assert result == ''

    @patch('builtins.open', new_callable=mock_open, read_data=b'audio_data')
    @patch('external_service.google_stt_api.os.path.getsize')
    @patch('external_service.google_stt_api.os.path.exists')
    def test_transcribe_recognizer_path(self, mock_exists, mock_getsize, _mock_file):
        """正常系: recognizerパスが正しく構築される"""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        mock_response = Mock()
        mock_response.results = []
        self.mock_client.speech_client.recognize.return_value = mock_response

        client = _make_client(project_id='test-proj', location='us-central1')
        transcribe_audio('/test/audio.wav', self.mock_config, client)

        call_kwargs = client.speech_client.recognize.call_args
        request = call_kwargs.kwargs['request']
        assert request.recognizer == 'projects/test-proj/locations/us-central1/recognizers/_'

    @patch('builtins.open', side_effect=FileNotFoundError('ファイルが見つかりません'))
    @patch('external_service.google_stt_api.os.path.getsize')
    @patch('external_service.google_stt_api.os.path.exists')
    def test_transcribe_file_not_found_error(self, mock_exists, mock_getsize, _mock_file):
        """異常系: ファイル読み込みでFileNotFoundError"""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        result = transcribe_audio('/test/audio.wav', self.mock_config, self.mock_client)
        assert result is None

    @patch('builtins.open', side_effect=PermissionError('アクセス拒否'))
    @patch('external_service.google_stt_api.os.path.getsize')
    @patch('external_service.google_stt_api.os.path.exists')
    def test_transcribe_permission_error(self, mock_exists, mock_getsize, _mock_file):
        """異常系: ファイル読み込みでPermissionError"""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        result = transcribe_audio('/test/audio.wav', self.mock_config, self.mock_client)
        assert result is None

    @patch('builtins.open', new_callable=mock_open, read_data=b'audio_data')
    @patch('external_service.google_stt_api.os.path.getsize')
    @patch('external_service.google_stt_api.os.path.exists')
    def test_transcribe_api_exception(self, mock_exists, mock_getsize, _mock_file):
        """異常系: API呼び出しで例外発生"""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024
        self.mock_client.speech_client.recognize.side_effect = Exception('API エラー')

        result = transcribe_audio('/test/audio.wav', self.mock_config, self.mock_client)
        assert result is None
