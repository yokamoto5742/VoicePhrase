import logging
import os
import traceback
from dataclasses import dataclass
from typing import Optional

from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import (
    AutoDetectDecodingConfig,
    RecognitionConfig,
    RecognizeRequest,
)

from utils.app_config import AppConfig
from utils.env_loader import load_env_variables


@dataclass
class GoogleSttClient:
    speech_client: SpeechClient
    project_id: str
    location: str


def setup_google_stt_client() -> GoogleSttClient:
    env_vars = load_env_variables()

    credentials_path = env_vars.get('GOOGLE_CREDENTIALS_JSON')
    if not credentials_path:
        raise ValueError('GOOGLE_CREDENTIALS_JSONが未設定です')
    os.environ['GOOGLE_CREDENTIALS_JSON'] = credentials_path

    project_id = env_vars.get('GOOGLE_PROJECT_ID')
    if not project_id:
        raise ValueError('GOOGLE_PROJECT_IDが未設定です')

    location = env_vars.get('GOOGLE_LOCATION', 'us-central1')

    speech_client = SpeechClient()
    return GoogleSttClient(speech_client=speech_client, project_id=project_id, location=location)


def validate_audio_file(file_path: str) -> tuple[bool, Optional[str]]:
    if not file_path:
        return False, '音声ファイルパスが未指定です'

    if not os.path.exists(file_path):
        return False, f'音声ファイルが存在しません: {file_path}'

    if os.path.getsize(file_path) == 0:
        return False, '音声ファイルサイズが0バイトです'

    return True, None


def transcribe_audio(
        audio_file_path: str,
        config: AppConfig,
        client: GoogleSttClient
) -> Optional[str]:
    is_valid, error_msg = validate_audio_file(audio_file_path)
    if not is_valid:
        logging.warning(error_msg) if '未指定' in str(error_msg) else logging.error(error_msg)
        return None

    try:
        logging.info('ファイル読み込み開始')
        with open(audio_file_path, 'rb') as f:
            audio_content = f.read()
        logging.info(f'ファイル読み込み完了: {len(audio_content)} bytes')

        recognizer = (
            f'projects/{client.project_id}/locations/{client.location}/recognizers/_'
        )
        recognition_config = RecognitionConfig(
            auto_decoding_config=AutoDetectDecodingConfig(),
            language_codes=[config.google_stt_language],
            model=config.google_stt_model,
        )
        request = RecognizeRequest(
            recognizer=recognizer,
            config=recognition_config,
            content=audio_content,
        )

        response = client.speech_client.recognize(request=request)

        transcripts = [
            result.alternatives[0].transcript
            for result in response.results
            if result.alternatives
        ]
        text_result = ''.join(transcripts)

        if len(text_result) == 0:
            logging.warning('文字起こし結果が空です')
            return ''

        logging.info(f'文字起こし完了: {len(text_result)}文字')
        return text_result

    except FileNotFoundError as e:
        logging.error(f'ファイルが見つかりません: {str(e)}')
        logging.debug(f'詳細: {traceback.format_exc()}')
        return None
    except PermissionError as e:
        logging.error(f'ファイルアクセス権限エラー: {str(e)}')
        logging.debug(f'詳細: {traceback.format_exc()}')
        return None
    except OSError as e:
        logging.error(f'OS関連エラー: {str(e)}')
        logging.debug(f'詳細: {traceback.format_exc()}')
        return None
    except Exception as e:
        logging.error(f'文字起こしエラー: {str(e)}')
        logging.error(f'エラーのタイプ: {type(e).__name__}')
        logging.debug(f'詳細: {traceback.format_exc()}')
        return None
