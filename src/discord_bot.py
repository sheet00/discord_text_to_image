import asyncio
import os
from dotenv import load_dotenv
import discord
from discord import VoiceClient, Message
from generate_image import generate_image_from_text_google
from generate_image import generate_image_from_text_openai
from generate_voice import synthesize_voice_with_timestamp
from google import genai
import re
from icecream import ic
from tenacity import retry, stop_after_attempt, wait_fixed
import generate_book as book

import time
import utils as utils
import base64

SEP = "-" * 100

# --- 会話履歴管理用グローバル変数 ---
# チャンネルIDごとに直近3ターン分の履歴を保持
channel_histories = {}

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

TOKEN = os.getenv("DISCORD_CHATBOT_TOKEN")

client = discord.Client(intents=intents)


def get_prompt(message_content, command):
    return message_content[len(command) :].strip()


@client.event
async def on_ready():
    print("ログインしました")


async def handle_neko(message):
    await message.channel.send("ポンにゃ")


@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
async def get_voice_client(message: Message) -> VoiceClient:
    """
    ボイスクライアント取得

    未接続の場合は新規接続し応答
    接続済みの場合は、既存のインスタンス応答
    """

    # 既に接続済みの場合はvoice_client
    # 未接続の場合はNone
    voice_client: VoiceClient = message.guild.voice_client

    # 新規接続
    if not voice_client:
        voice_client = await message.author.voice.channel.connect()
        return voice_client

    # 接続済みの場合は既存インスタンス応答
    return voice_client


async def handle_speech(message: Message):
    text = get_prompt(message.content, "/talk")

    if not text:
        await message.channel.send("プロンプトが空にゃ。/talk の後に説明文を入れてにゃ")
        return

    # テキストを分割
    texts = utils.split_text(text)

    # ボイスチャンネルの確認 (ループ前に一度行う)
    if not (message.author.voice and message.author.voice.channel):
        await message.channel.send("ボイスチャンネルに参加してからコマンドを使ってにゃ")
        return

    # 各テキスト断片ごとに音声合成と再生を実行
    for i, t in enumerate(texts):
        await message.channel.send(f"[音声を生成中にゃ][{i+1}/{len(texts)}]")

        # 1. 音声合成
        filepath = await asyncio.to_thread(synthesize_voice_with_timestamp, t)
        if filepath is None:
            await message.channel.send(
                f"テキスト「{t[:20]}...」の音声合成に失敗したにゃ"
            )
            continue  # 次のテキストへ

        # 2. ボイスチャンネル取得
        voice_client = await get_voice_client(message)

        # 3. 再生中の場合は待機
        while voice_client.is_playing():
            ic("前回音声処理が終わるまで待機")
            await asyncio.sleep(1)

        # 4. 音声再生
        source = discord.FFmpegPCMAudio(filepath, executable="ffmpg/ffmpeg.exe")
        await message.channel.send("[再生するにゃ]")
        # 音声待機中に切れてしまうケースがあるため、再取得
        voice_client = await get_voice_client(message)

        voice_client.play(source)


async def handle_text_to_image(message):
    """
    テキストからの画像生成
    """
    prompt = get_prompt(message.content, "/image")
    if not prompt:
        await message.channel.send(
            "プロンプトが空にゃ。/image の後に説明文を入れてにゃ"
        )
        return

    await message.channel.send("[画像を生成中にゃ]")

    try:
        image_generator = os.getenv("IMAGE_GENERATOR", "google").lower()
        if image_generator == "google":
            filename = await asyncio.to_thread(generate_image_from_text_google, prompt)
        elif image_generator == "openai":
            filename = await asyncio.to_thread(generate_image_from_text_openai, prompt)
        else:
            await message.channel.send(
                f"無効な画像ジェネレーター: {image_generator}。'google' または 'openai' を指定してにゃ。"
            )
            return

        if filename:
            await message.channel.send(file=discord.File(filename))
    except Exception as e:
        await message.channel.send(f"画像生成中にエラーが発生したにゃ: {str(e)}")


async def handle_book(message):
    """
    シーンからの画像生成
    """

    prompt = get_prompt(message.content, "/book")
    if not prompt:
        await message.channel.send("プロンプトが空にゃ。/book の後に説明文を入れてにゃ")
        return

    data = await asyncio.to_thread(book.markdown_to_data, prompt)
    for i in range(len(data.paragraph)):
        await message.channel.send(SEP)
        await message.channel.send("[画像を生成中にゃ]")

        filename = None
        # try:
        #     filename = book.generate_image(data, i)

        # except Exception as e:
        #     await message.channel.send(str(e))

        content = data.paragraph[i]
        await message.channel.send(content)
        if filename:
            await message.channel.send(file=discord.File(filename))

        message.content = f"/talk {content}"
        await handle_speech(message)


async def handle_save(message: Message):
    await book.save(message.content, message)


async def handle_list(message: Message):
    """
    /bookフォルダ内のフォルダ一覧を取得し、Base64デコードしてマークダウンリストとして出力する
    """
    book_dir = "./book"
    if not os.path.isdir(book_dir):
        await message.channel.send("`/book` ディレクトリが見つかりません。")
        return

    entries = os.listdir(book_dir)
    folders = sorted(
        [entry for entry in entries if os.path.isdir(os.path.join(book_dir, entry))]
    )

    if not folders:
        await message.channel.send("`/book` ディレクトリにフォルダがありません。")
        return

    folder_list = []
    for folder in folders:
        try:
            # Base64URLデコードのために末尾に'='を補う
            padded_folder = folder + "=" * ((4 - len(folder) % 4) % 4)
            decoded_name = base64.urlsafe_b64decode(padded_folder).decode("utf-8")
            folder_list.append(f"- {decoded_name}")
        except Exception as e:
            ic(f"Error decoding folder name {folder}: {e}")
            folder_list.append(f"- {folder} (デコード失敗)")

    response = "## ブック一覧\n" + "\n".join(folder_list)
    await message.channel.send(response)


async def handle_load(message: Message):
    """
    /load コマンドを処理し、指定されたタイトルのブックを読み込み、
    テキスト、画像、音声ファイルを送信します。
    """
    title = get_prompt(message.content, "/load")
    if not title:
        await message.channel.send(
            "読み込むブックのタイトルを指定してくださいにゃ。例: `/load ブックタイトル`"
        )
        return

    # ボイスチャンネルの確認
    if not (message.author.voice and message.author.voice.channel):
        await message.channel.send("ボイスチャンネルに参加してからコマンドを使ってにゃ")
        return

    encoded_dir_name = (
        base64.urlsafe_b64encode(title.encode("utf-8")).decode("utf-8").rstrip("=")
    )
    dir_path = os.path.join("book", encoded_dir_name)

    if not os.path.exists(dir_path):
        await message.channel.send(f"ブック '{title}' は見つかりませんでしたにゃ。")
        return

    # 対象フォルダ内の子フォルダ一覧を取得
    subdirectories = [
        d for d in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, d))
    ]

    for subdir_name in sorted(subdirectories):  # 子フォルダ名をソートして順番に処理
        subdir_path = os.path.join(dir_path, subdir_name)

        # テキスト処理
        text_file_path = os.path.join(subdir_path, "target.txt")
        if os.path.exists(text_file_path):
            with open(text_file_path, "r", encoding="utf-8") as f:
                content = f.read()
                await message.channel.send(content)

        # 画像処理
        image_file_path = os.path.join(subdir_path, "target.png")
        if os.path.exists(image_file_path):
            await message.channel.send(file=discord.File(image_file_path))

        # 音声処理
        wav_files = [
            os.path.join(subdir_path, f)
            for f in os.listdir(subdir_path)
            if f.endswith(".wav") and os.path.isfile(os.path.join(subdir_path, f))
        ]

        voice_client = await get_voice_client(message)
        for filepath in wav_files:
            while voice_client.is_playing():
                ic("前回音声処理が終わるまで待機")
                await asyncio.sleep(1)

            source = discord.FFmpegPCMAudio(filepath, executable="ffmpg/ffmpeg.exe")
            voice_client = await get_voice_client(message)

            voice_client.play(source)

        while voice_client.is_playing():
            ic("段落の音声処理が終わるまで待機")
            await asyncio.sleep(1)

    await message.channel.send("おしまいにゃ。")


async def handle_mention(message):
    global channel_histories

    # メンション部分を除去したユーザー発言
    user_message = re.sub(r"<@\d+>", "", message.content).strip()
    ic(user_message)
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
    response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.5-flash-preview-04-17",
        contents=prompt,
    )

    bot_reply = response.text
    ic(bot_reply)

    # 履歴に今回のやりとりを追加
    history.append({"user": user_message, "bot": bot_reply})
    # 直近3ターン分のみ保持
    if len(history) > 3:
        history = history[-3:]
    channel_histories[channel_id] = history

    # 音声返信
    message.content = f"/talk {bot_reply}"
    await handle_speech(message)


async def handle_help(message):
    help_message = """
    **コマンド一覧:**

    `/neko`: 猫の鳴き声を送信します。
    `/image [プロンプト]`: 指定されたプロンプトに基づいて画像を生成します。
    `/talk [テキスト]`: 指定されたテキストを音声で再生します。
    `@ずんだもん`: ずんだもんにメンションすると、会話できます。
    `/help`: コマンド一覧を表示します。
    `/book [プロンプト]`: 指定されたプロンプトに基づいて画像を生成します(本のシーン)。
    """
    await message.channel.send(help_message)


# メッセージ受信時に動作する処理
@client.event
async def on_message(message):
    async def extract_text_from_attachment(message):
        """
        添付ファイルあり
        message.txtという名前の添付ファイルがある場合、
        その内容を読み取り、/saveコマンドの引数として設定します。

        添付がない場合は通常message応答
        """
        # 通常テキスト 添付なし
        if len(message.attachments) == 0:
            return message

        # 添付ファイルパターン
        attachment = message.attachments[0]
        if attachment.filename == "message.txt":
            data = await attachment.read()
            text = data.decode("utf-8")
            message.content = f"/save {text}"

            return message

    if message.author.bot:
        return

    if message.content == "/help":
        await handle_help(message)
        return

    if message.content == "/neko":
        await handle_neko(message)
        return

    if message.content.startswith("/image"):
        await handle_text_to_image(message)
        return

    if message.content.startswith("/talk"):
        await handle_speech(message)
        return

    if message.content.startswith("/book"):
        message = await extract_text_from_attachment(message)
        if message:
            await handle_book(message)

        return

    # book一覧表示
    if message.content.startswith("/list"):
        await handle_list(message)
        return

    # book保存処理
    if message.content.startswith("/save"):
        message = await extract_text_from_attachment(message)
        if message:
            await handle_save(message)

        return

    # bookロード処理
    if message.content.startswith("/load"):
        await handle_load(message)
        return

    if client.user in message.mentions:
        await handle_mention(message)
        return


client.run(TOKEN)
