import os
from icecream import ic
from dotenv import load_dotenv
from pydantic import BaseModel
from openai import OpenAI
import time
from datetime import datetime
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import base64
from translate import translate_text

SEP = "-" * 100

# .envファイルの内容を読み込む
load_dotenv()


def generate_image_from_text_openai(input_text: str) -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=60)

    model = "gpt-image-1"
    size = "1024x1024"
    # low 1.58 円, medium 6.03 円, high 23.98 円
    quality = "low"

    # 日本語を英語に変換
    # english_txt = translate_text(text=input_text)
    # prompt = english_txt

    prompt = input_text

    print(SEP)
    print("openaiで画像を生成中...")
    print(model, size, quality)
    print(prompt)

    # 画像の生成
    result = client.images.generate(
        model=model,
        moderation="low",
        prompt=prompt,
        size=size,
        quality=quality,
    )

    # 画像をダウンロードして保存
    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    # imgディレクトリがなければ作成
    os.makedirs("img", exist_ok=True)
    filename = datetime.now().strftime(f"%Y%m%d_%H%M%S_openai_{quality}.png")
    filepath = os.path.join("img", filename)
    with open(filepath, "wb") as f:
        f.write(image_bytes)
    print(f"画像を '{filepath}' に保存しました。")
    return filepath


def generate_image_from_text_google(input_text: str) -> str:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # 日本語を英語に変換
    # english_txt = translate_text(text=input_text)
    # prompt = english_txt

    prompt = input_text

    print(SEP)
    print("Google Geminiで画像を生成中...")
    print(prompt)
    base_delay = 1  # 初期待機秒数
    max_delay = 3  # 最大待機秒数

    for attempt in range(10):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp-image-generation",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["Text", "Image"]
                ),
            )
            # imgディレクトリがなければ作成
            os.makedirs("img", exist_ok=True)
            filename = datetime.now().strftime("%Y%m%d_%H%M%S_gemini.png")
            filepath = os.path.join("img", filename)

            for part in response.candidates[0].content.parts:
                if hasattr(part, "text") and part.text is not None:
                    print(part.text)
                elif hasattr(part, "inline_data") and part.inline_data is not None:
                    image = Image.open(BytesIO(part.inline_data.data))
                    image.save(filepath)
                    # image.show()
                    print(f"画像を '{filepath}' に保存しました。")
                    return filepath

            raise Exception("画像データが見つかりませんでした。")
        except Exception as e:
            print(
                f"[{attempt+1}/10] Google Geminiでの生成中にエラーが発生しました: {e}"
            )
            if attempt == 9:
                print("最大リトライ回数に達しました。")
                raise Exception("最大リトライ回数に達しました。")
            else:
                delay = min(base_delay * (2**attempt), max_delay)
                print(f"{delay}秒待機してリトライします。")
                time.sleep(delay)
                continue


def edit_image(input_text: str) -> str:
    client = OpenAI()

    english_keywords = translate_text(text=input_text)
    prompt = english_keywords
    model = "gpt-image-1"
    size = "1024x1024"
    # low 1.58 円, medium 6.03 円, high 23.98 円
    quality = "low"

    result = client.images.edit(
        model=model,
        image=[
            open(os.path.join("edit", "zundamon.png"), "rb"),
        ],
        prompt=prompt,
    )

    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    # Save the image to a file
    filename = datetime.now().strftime("%Y%m%d_%H%M%S_openai_edit.png")
    filepath = os.path.join("img", filename)

    with open(filepath, "wb") as f:
        f.write(image_bytes)


if __name__ == "__main__":
    sample_text = """
    best quality, ultra high res, (photorealistic:1.4), RAW photo, 1japanese girl, solo, cute, detailed beautiful face,
    猫と戯れている。逆光。
       
    """
    generate_image_from_text_openai(sample_text)

    # edit_image(sample_text)

    # generate_image_from_text_google(sample_text)
