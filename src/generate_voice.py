import os
from retry import retry
import datetime
import requests

SPEED_SCALE = 1.2


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
    print(f"音声合成するテキスト: {text}")

    status_code = check_voicevox_server()
    if status_code != 200:
        print(f"Voicevoxサーバーが起動していません (status_code={status_code})")
        return status_code

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
    # print(query)
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
