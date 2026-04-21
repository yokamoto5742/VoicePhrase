import os
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech


def transcribe_with_chirp3(audio_file_path: str):
    client = SpeechClient()

    # プロジェクトIDと場所の設定
    project_id = "gen-lang-client-0605794434"
    location = "us-central1"  # Chirp 3がサポートされているリージョンを指定

    # Recognizerのパス
    # 事前にコンソールで作成するか、コード内で動的に定義も可能
    recognizer_id = "chirp3-recognizer"
    parent = f"projects/{project_id}/locations/{location}"

    # 設定の定義
    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDecodingConfig(),
        # Chirp 3 を指定
        model="chirp-3",
        language_codes=["ja-JP"],
    )

    # 音声データの読み込み
    with open(audio_file_path, "rb") as f:
        content = f.read()

    request = cloud_speech.RecognizeRequest(
        recognizer=f"{parent}/recognizers/_",  # "_" はデフォルト設定を使用
        config=config,
        content=content,
    )

    # 推論実行
    response = client.recognize(request=request)

    for result in response.results:
        print(f"Transcript: {result.alternatives[0].transcript}")

# 使用例
# transcribe_with_chirp3("sample_medical_audio.wav")