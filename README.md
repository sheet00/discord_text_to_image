# Discord Text to Image/Voice Bot

## 概要

このプロジェクトは、Discord 上でテキストから画像生成、音声合成、チャットボット機能、および「ブック」としてコンテンツを管理・再生する機能を提供する多機能ボットです。

## 機能

- **テキストから音声生成**: `/talk [テキスト]` コマンドで、指定されたテキストを音声に変換し、Discord のボイスチャンネルで再生します。Voicevox サーバーを利用しています。
- **テキストから画像生成**: `/image [プロンプト]` コマンドで、指定されたプロンプトに基づいて画像を生成します。OpenAI DALL-E または Google Gemini の画像生成 API を選択して使用できます。
- **ブック機能**: Markdown 形式のテキストを保存し、各段落から画像と音声を自動生成して「ブック」として管理できます。
  - `/save [Markdownテキスト]` または `message.txt` 添付ファイルでブックを保存します。
  - `/list` で保存されているブックの一覧を表示します。
  - `/load [ブックタイトル]` で指定されたブックを読み込み、テキスト、画像、音声を順に再生します。
- **チャットボット機能**: `@ずんだもん [メッセージ]` でボットにメンションすると、Google Gemini API を利用した会話が可能です。ずんだもん口調で応答します。
- **翻訳機能**: AWS Translate を利用してテキストを翻訳します（主に内部的な画像生成プロンプトの翻訳に使用）。

## セットアップ

### 1. 環境変数

プロジェクトルートに `.env` ファイルを作成し、以下の環境変数を設定してください。

```dotenv
DISCORD_CHATBOT_TOKEN=YOUR_DISCORD_BOT_TOKEN
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
VOICEVOX_EXE_PATH=C:/Path/To/VOICEVOX/run.exe # Voicevoxの実行ファイルパス
IMAGE_GENERATOR=google # または openai
AWS_ACCESS_KEY=YOUR_AWS_ACCESS_KEY_ID
AWS_SECRET=YOUR_AWS_SECRET_ACCESS_KEY
AWS_REGION=YOUR_AWS_REGION # 例: us-east-1
```

### 2. 依存関係のインストール

Python の依存関係をインストールします。

```bash
pip install -r requirements.txt
```

### 3. Voicevox のセットアップ

Voicevox のアプリケーションをダウンロードし、インストールしてください。`VOICEVOX_EXE_PATH` には、インストールした Voicevox の `run.exe` ファイルへのパスを指定します。ボットが音声合成を行う際に、自動的に Voicevox サーバーを起動・停止します。

## 使用方法

ボットを起動します。

```bash
python src/discord_bot.py
```

Discord サーバーにボットを招待し、以下のコマンドを使用できます。

- `/neko`: 猫の鳴き声を送信します。
- `/image [プロンプト]`: 指定されたプロンプトに基づいて画像を生成します。
- `/talk [テキスト]`: 指定されたテキストを音声で再生します。
- `/save [テキスト]`: テキストをブックとして保存します。`message.txt` という名前の添付ファイルがある場合、その内容を保存します。
- `/list`: 保存されているブックの一覧を表示します。
- `/load [タイトル]`: 指定されたタイトルのブックを読み込み、テキスト、画像、音声を送信します。
- `@ずんだもん [メッセージ]`: ずんだもんにメンションすると、会話できます。
- `/help`: コマンド一覧を表示します。

## ファイル構造

```
.
├── .gitignore
├── requirements.txt
├── edit/
│   └── zundamon.png
├── ffmpg/
│   └── ffmpeg.exe  # FFmpegの実行ファイル
│   └── ... (その他のFFmpeg関連ファイル)
├── img_example/    # 生成された画像の例
│   ├── ghibli/
│   ├── manga/
│   └── photo/
├── src/
│   ├── discord_bot.py      # Discordボットのメインロジック
│   ├── generate_book.py    # ブック生成・管理ロジック
│   ├── generate_image.py   # 画像生成ロジック (OpenAI/Gemini)
│   ├── generate_voice.py   # 音声合成ロジック (Voicevox)
│   ├── image_test.py       # 画像生成テストスクリプト
│   ├── test.wav            # テスト用音声ファイル
│   ├── translate.py        # 翻訳ロジック (AWS Translate)
│   └── utils.py            # ユーティリティ関数
└── tests/
    └── test_utils.py       # テストファイル
```
