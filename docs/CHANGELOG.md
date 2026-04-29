# 変更履歴

このプロジェクトのすべての重要な変更は、このファイルに記録されます。

フォーマットは [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に基づいており、
バージョン番号は [Semantic Versioning](https://semver.org/lang/ja/) に従っています。

## [Unreleased]

## [1.0.2] - 2026-04-29

### 削除
- バックアップから置換辞書を更新するUIボタンと機能を削除

## [1.0.1] - 2026-04-28

### 追加
- 専門用語登録ボタンをUIに追加
- 専門用語登録機能を置換エディタに実装

### 変更
- `google_stt_phrase_set_file`を相対パスに変更
- `replacements_editor`のタイトルとファイルパスを動的に設定
- 音声ファイル読み込み時のログメッセージを修正

### 修正
- `Recognizer`の`location`プロパティを修正
- `app/error_handler`の`_default_root`型警告を抑制

### 削除
- `main.py`から`setup_process`を削除
- `utils/process_setup.py`を削除

## [1.0.0] - 2026-04-24
- VoicePhrase の初版リリース
