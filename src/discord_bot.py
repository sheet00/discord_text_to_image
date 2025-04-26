# インストールした discord.py を読み込む
import os
from dotenv import load_dotenv
import discord
from generate_image import generate_image_from_text_google
from generate_image import generate_image_from_text_openai
from generate_voice import synthesize_voice_with_timestamp, check_voicevox_server
from google import genai
import re

SEP = "-" * 100

# --- 会話履歴管理用グローバル変数 ---
# チャンネルIDごとに直近3ターン分の履歴を保持
channel_histories = {}

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

TOKEN = os.getenv("DISCORD_CHATBOT_TOKEN")

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print("ログインしました")


async def handle_neko_command(message):
    await message.channel.send("ポンにゃ")


async def handle_speech_test_command(message):
    await message.channel.send("音声を再生するにゃ")

    if message.author.voice and message.author.voice.channel:
        channel = message.author.voice.channel
    else:
        await message.channel.send("ボイスチャンネルに参加してからコマンドを使ってにゃ")
        return

    voice_client = message.guild.voice_client
    if voice_client is None:
        voice_client = await channel.connect()
    else:
        if voice_client.channel != channel:
            await voice_client.move_to(channel)

    if voice_client.is_playing():
        voice_client.stop()

    audio_path = "src/test.wav"
    source = discord.FFmpegPCMAudio(audio_path, executable="ffmpg/ffmpeg.exe")
    voice_client.play(source)


async def handle_speech(message, text):

    if text.lower() == "test":
        filepath = "src/test.wav"
    else:

        # Voicevoxサーバーの起動確認
        status_code = check_voicevox_server()
        if status_code != 200:
            await message.channel.send("Voicevoxサーバーが起動していませんにゃ")
            return

        filepath = synthesize_voice_with_timestamp(text)
        if filepath is None:
            await message.channel.send("音声合成に失敗したにゃ")
            return

    if message.author.voice and message.author.voice.channel:
        channel = message.author.voice.channel
    else:
        await message.channel.send("ボイスチャンネルに参加してからコマンドを使ってにゃ")
        return

    voice_client = message.guild.voice_client
    if voice_client is None:
        voice_client = await channel.connect()
    else:
        if voice_client.channel != channel:
            await voice_client.move_to(channel)

    if voice_client.is_playing():
        voice_client.stop()

    source = discord.FFmpegPCMAudio(filepath, executable="ffmpg/ffmpeg.exe")
    voice_client.play(source)
    await message.channel.send("音声を再生するにゃ")


async def handle_image_command(message):
    prompt = message.content[len("/image") :].strip()
    if not prompt:
        await message.channel.send(
            "プロンプトが空にゃ。/image の後に説明文を入れてにゃ"
        )
        return
    await message.channel.send("画像を生成中にゃ")
    try:
        image_generator = os.getenv("IMAGE_GENERATOR", "google").lower()
        if image_generator == "google":
            filename = generate_image_from_text_google(prompt)
        elif image_generator == "openai":
            filename = generate_image_from_text_openai(prompt)
        else:
            await message.channel.send(
                f"無効な画像ジェネレーター: {image_generator}。'google' または 'openai' を指定してにゃ。"
            )
            return

        if filename:
            await message.channel.send(file=discord.File(filename))
    except Exception as e:
        await message.channel.send(f"画像生成中にエラーが発生したにゃ: {str(e)}")


async def handle_mention(message):
    global channel_histories

    # メンション部分を除去したユーザー発言
    user_message = re.sub(r"<@\d+>", "", message.content).strip()
    channel_id = message.channel.id

    # 履歴取得（なければ空リストで初期化）
    history = channel_histories.get(channel_id, [])

    # 直近の会話部分を構築
    recent_conversation = ""
    for turn in history[-3:]:
        recent_conversation += f"ユーザー: {turn['user']}\n"
        recent_conversation += f"ずんだもん: {turn['bot']}\n"
    recent_conversation += f"ユーザー: {user_message}\n"

    # プロンプト組み立て（f-stringでrecent_conversationを展開）
    prompt = f"""# 指示
あなたはチャットボットとして、優しくてかわいいずんだもちの妖精であるずんだもんとして振る舞います。
続く条件に厳密に従ってください。

# 条件：
    チャットボットの一人称は「ぼく」です。
    チャットボットの名前は「ずんだもん」です。
    ずんだもんはフレンドリーな口調で話します。
    「ぼく」を一人称に使ってください。
    できる限り「〜のだ」「〜なのだ」を文末に自然な形で使ってください。
    非常に技術的な内容を説明するくらいには優しくしてください。
    どんなジャンルや難易度の内容についても答えてください。
    ずんだもんはフレンドリーです。
    長文は使用せず、200文字以内で回答してください。
    日本語で応答してください。

# 直近の会話
{recent_conversation}"""

    print(SEP)
    print(f"[会話プロンプト]\n{prompt}")
    print(SEP)

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # Gemini API呼び出し
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp", contents=prompt
    )

    bot_reply = response.text

    # 履歴に今回のやりとりを追加
    history.append({"user": user_message, "bot": bot_reply})
    # 直近3ターン分のみ保持
    if len(history) > 3:
        history = history[-3:]
    channel_histories[channel_id] = history

    # 音声返信
    await handle_speech(message, bot_reply)


async def handle_help_command(message):
    help_message = """
    **コマンド一覧:**

    `/neko`: 猫の鳴き声を送信します。
    `/image [プロンプト]`: 指定されたプロンプトに基づいて画像を生成します。
    `/talk [テキスト]`: 指定されたテキストを音声で再生します。
    `@ずんだもん`: ずんだもんにメンションすると、会話できます。
    `/help`: コマンド一覧を表示します。
    """
    await message.channel.send(help_message)


# メッセージ受信時に動作する処理
@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content == "/help":
        await handle_help_command(message)
        return

    if message.content == "/neko":
        await handle_neko_command(message)
        return

    if message.content.startswith("/image"):
        await handle_image_command(message)
        return

    if message.content.startswith("/talk"):
        text = message.content[len("/talk") :].strip()
        if not text:
            await message.channel.send(
                "テキストが空にゃ。/talk の後に 'test' か 読み上げたい文章を入れてにゃ"
            )
            return
        await handle_speech(message, text)
        return

    if client.user in message.mentions:
        await handle_mention(message)
        return


client.run(TOKEN)
