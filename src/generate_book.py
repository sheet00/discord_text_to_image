from icecream import ic
import markdown
import bs4
import os
from google import genai
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional, List
from generate_image import generate_image_from_text_openai

load_dotenv()
SEP = "-" * 100


class MarkdownData(BaseModel):
    title: str
    paragraph: List[str]
    all_text: str


# --- PydanticモデルによるJSONスキーマ定義 ---
class CharacterInfo(BaseModel):
    """登場人物一人に関する情報"""

    name: Optional[str] = Field(None, description="登場人物の名前（もしあれば）")
    gender_age: Optional[str] = Field(None, description="性別・年齢（推定含む）")
    appearance_clothing: Optional[str] = Field(None, description="外見・服装の特徴")
    expression_pose: Optional[str] = Field(None, description="表情・ポーズ")


class LocationInfo(BaseModel):
    """場所に関する情報"""

    specific_place: Optional[str] = Field(None, description="具体的な場所の名前や種類")
    setting: Optional[str] = Field(None, description="屋内か屋外か")
    era: Optional[str] = Field(None, description="時代設定（もし示唆があれば）")
    atmosphere_features: Optional[str] = Field(
        None, description="場所の雰囲気や特徴的な要素"
    )


class TimeWeatherInfo(BaseModel):
    """時間・天候に関する情報"""

    time_of_day: Optional[str] = Field(
        None, description="時間帯（朝、昼、夕方、夜、深夜など）"
    )
    season: Optional[str] = Field(None, description="季節（もし示唆があれば）")
    weather: Optional[str] = Field(None, description="天気")
    light_condition: Optional[str] = Field(
        None, description="光の状態（例: 明るい日差し、薄暗い、月明かりなど）"
    )


class ActionSituationInfo(BaseModel):
    """行動・状況に関する情報"""

    character_action: Optional[str] = Field(
        None, description="登場人物が何をしているか（主要なアクション）"
    )
    overall_situation: Optional[str] = Field(
        None, description="シーン全体で何が起こっているか"
    )


class EmotionAtmosphereInfo(BaseModel):
    """感情・雰囲気に関する情報"""

    scene_atmosphere: Optional[str] = Field(
        None, description="シーン全体の雰囲気（例: 静か、ノスタルジックなど）"
    )
    character_emotion: Optional[str] = Field(
        None, description="登場人物の感情（読み取れる場合）"
    )


class SceneAnalysisResult(BaseModel):
    """抽出されたシーン要素全体の構造"""

    characters: List[CharacterInfo] = Field(
        ...,
        description="登場人物に関する情報のリスト。シーンに登場する各キャラクターの情報を個別に格納する。",
    )
    location: LocationInfo = Field(..., description="場所に関する情報")
    time_weather: TimeWeatherInfo = Field(..., description="時間・天候に関する情報")
    action_situation: ActionSituationInfo = Field(
        ..., description="行動・状況に関する情報"
    )
    emotion_atmosphere: EmotionAtmosphereInfo = Field(
        ..., description="感情・雰囲気に関する情報"
    )
    important_objects: Optional[List[str]] = Field(
        None,
        description="物語やシーンの鍵となる物、特徴的な小物、特に描写されているアイテムのリスト",
    )


def get_scene(input_text: str, prev_text: str) -> str:
    """
    Gemini APIを使って日本語からシーンを抽出する
    """

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    prompt = f"""
あなたは優秀な文芸編集者であり、イラストレーターのためのアシスタントです。
以下の小説本文を注意深く読み、このシーンを挿絵として描くために必要となる具体的な情景描写の要素を抽出・整理してください。
抽出対象で分からない情報は前ページを参考にして、不足情報を補ってください。

# 抽出対象の小説本文
{input_text}

*   上記の本文から、以下の要素に関する視覚的な情報を抽出してください。
    *   **登場人物 (characters)**: シーンに登場する**各人物**について、以下の情報を**リスト形式**で抽出してください。リストの各要素は一人の人物に対応します。
        *   名前 (name): 名前（もしあれば）
        *   性別・年齢 (gender_age): 性別・年齢（推定含む）
        *   外見・服装 (appearance_clothing): 外見・服装の特徴
        *   表情・ポーズ (expression_pose): 表情・ポーズ
    *   場所 (location): 具体的な場所、屋内/屋外、時代設定、雰囲気・特徴
    *   時間・天候 (time_weather): 時間帯、季節、天気、光の状態
    *   行動・状況 (action_situation): 登場人物の行動（主要な人物や全体の動き）、全体の状況
    *   感情・雰囲気 (emotion_atmosphere): シーンの雰囲気、登場人物の感情（主要な人物や全体の感情）
    *   重要なオブジェクト (important_objects): 鍵となる物や小物のリスト
*   抽出した結果を、**提供されたJSONスキーマに従ってJSON形式で厳密に出力してください。**
*   本文中に明示的に書かれていない要素については、JSONの値として `null` を使用するか、スキーマ定義に従って省略してください。
*   挿絵として描くことを意識し、視覚的な情報を優先して抽出してください。

# 重要な注意点
殺人、暴力、性的な内容、その他の不適切な内容は含まれないようにしてください。

# 前ページ
{prev_text}
"""

    print(SEP)
    # print(prompt)
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": SceneAnalysisResult,
        },
    )
    # JSONとしてパースされたオブジェクトから取得
    result = SceneAnalysisResult.model_validate_json(response.text)
    result = result.model_dump()
    ic(input_text, result)
    return result


def generate_image(data: MarkdownData, target_index: int) -> str:
    content = data.paragraph[target_index]
    # indexが進むにつれて、全文を増やす
    prev_text = "".join(data.paragraph[:target_index])
    # ic(content, prev_text)
    scene = get_scene(content, prev_text)

    prompt = f"""
# 指示
あなたは優秀な映画監督のアシスタントです。
以下の本文を注意深く読み、このシーンに対する実写画像を生成してください。

# 作風
best quality, ultra high res, (photorealistic:1.4), RAW photo, realistic

# 人種
日本人

# 本文
{content}

# シーン
{scene}
        """

    #     prompt = f"""
    # # 指示
    # あなたは優秀なアニメーション監督のアシスタントです。
    # 以下の本文を注意深く読み、このシーンに対するイラストを生成してください。

    # # 作風
    # ジブリ風、日本アニメ調、かわいいイラスト、子供向けイラスト

    # # 人種
    # 日本人

    # # 本文
    # {content}

    # # シーン
    # {scene}
    #         """

    return generate_image_from_text_openai(prompt)


def markdown_to_data(markdown_text: str) -> MarkdownData:
    html = markdown.markdown(markdown_text)
    soup = bs4.BeautifulSoup(html, "html.parser")
    # ic(str(soup))

    title = soup.find("h2").text

    paragraphs = []
    current_paragraph = ""
    for element in soup.find_all(["hr", "p"]):
        if element.name == "hr":
            if current_paragraph:
                paragraphs.append(current_paragraph.replace("\n", "").replace(" ", ""))
            current_paragraph = ""
        elif element.name == "p":
            current_paragraph += element.text
    if current_paragraph:
        paragraphs.append(current_paragraph.replace("\n", "").replace(" ", ""))

    return MarkdownData(title=title, paragraph=paragraphs, all_text=markdown_text)


def main():
    with open("work/02.md", "r", encoding="utf-8") as f:
        input_text = f.read()

    data = markdown_to_data(input_text)

    # ic(data)

    for i in range(len(data.paragraph)):
        result = generate_image(data, i)
        print(result)


if __name__ == "__main__":
    main()
