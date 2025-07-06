import boto3
import os
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET")
AWS_REGION_NAME = os.getenv("AWS_REGION")


def translate_text(text, source_language_code="ja", target_language_code="en"):
    """
    Amazon Translateを使用して、ある言語から別の言語にテキストを翻訳します。

    Args:
        text (str): 翻訳するテキスト。
        source_language_code (str): ソース言語の言語コード (デフォルト: 'ja' (日本語))。
        target_language_code (str): ターゲット言語の言語コード (デフォルト: 'en' (英語))。

    Returns:
        str: 翻訳されたテキスト。エラーが発生した場合はNone。
    """
    try:
        translate = boto3.client(
            service_name="translate",
            region_name=AWS_REGION_NAME,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            use_ssl=True,
        )
        result = translate.translate_text(
            Text=text,
            SourceLanguageCode=source_language_code,
            TargetLanguageCode=target_language_code,
        )
        return result.get("TranslatedText")
    except Exception as e:
        print(f"Error during translation: {e}")
        return None


if __name__ == "__main__":
    text_to_translate = "こんにちは、世界！"
    translated_text = translate_text(text_to_translate)
    if translated_text:
        print(f"Original text: {text_to_translate}")
        print(f"Translated text: {translated_text}")
    else:
        print("Translation failed.")
