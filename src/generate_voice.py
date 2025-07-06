import os
from retry import retry
import datetime
import requests
import subprocess
from dotenv import load_dotenv
from icecream import ic

load_dotenv()

SEP = "-" * 100
SPEED_SCALE = 1.3
VOICEVOX_EXE_PATH = os.environ.get("VOICEVOX_EXE_PATH")


def start_voicevox_server():
    """Voicevoxサーバーを起動する"""
    print(SEP)
    print("Voicevoxサーバーを起動します...")
    try:
        subprocess.Popen([VOICEVOX_EXE_PATH])
        print("Voicevoxサーバーの起動が完了しました。")
    except Exception as e:
        print(f"Voicevoxサーバーの起動に失敗しました: {e}")
    print(SEP)


def stop_voicevox_server():
    """Voicevoxサーバーを停止する"""
    print(SEP)
    print("Voicevoxサーバーを停止します...")
    try:
        subprocess.call(["taskkill", "/F", "/IM", "run.exe"])
        print("Voicevoxサーバーの停止が完了しました。")
    except Exception as e:
        print(f"Voicevoxサーバーの停止に失敗しました: {e}")
    print(SEP)


def check_voicevox_server():
    """
    Voicevoxサーバーの起動確認を行い、HTTPステータスコードを返す
    接続できない場合は0を返す
    """
    try:
        response = requests.get("http://127.0.0.1:50021/version")
        return response.status_code
    except requests.exceptions.RequestException:
        return 0


@retry(tries=10)
def synthesize_voice_with_timestamp(text, speaker=1):
    print(SEP)
    print(f"音声合成するテキスト: {text}")

    start_voicevox_server()

    try:
        status_code = check_voicevox_server()
        if status_code != 200:
            raise Exception(
                f"Voicevoxサーバーが起動していません (status_code={status_code})"
            )

        # 現在時刻を取得し、ファイル名を生成
        now = datetime.datetime.now()
        filename = now.strftime("%Y%m%d_%H%M%S") + ".wav"
        # wavディレクトリがなければ作成
        os.makedirs("wav", exist_ok=True)
        filepath = f"wav/{filename}"

        # 1. テキストから音声合成のためのクエリを作成
        print("音声合成クエリを作成中...")
        query_payload = {"text": text, "speaker": speaker}
        query_response = requests.post(
            "http://localhost:50021/audio_query", params=query_payload
        )

        if query_response.status_code != 200:
            print(f"Error in audio_query: {query_response.text}")
            return None

        print("クエリ作成完了")
        query = query_response.json()
        query["speedScale"] = SPEED_SCALE

        # 2. クエリを元に音声データを生成
        print("音声データを生成中...")
        synthesis_payload = {"speaker": speaker}
        synthesis_response = requests.post(
            "http://localhost:50021/synthesis", params=synthesis_payload, json=query
        )

        if synthesis_response.status_code == 200:
            # 音声ファイルとして保存
            print("音声ファイルを保存中...")
            with open(filepath, "wb") as f:
                f.write(synthesis_response.content)
            print(f"音声が {filepath} に保存されました。")
            return filepath
        else:
            print(f"Error in synthesis: {synthesis_response.text}")
            raise Exception(f"Error in synthesis: {synthesis_response.text}")

    finally:
        stop_voicevox_server()
