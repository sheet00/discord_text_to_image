from icecream import ic
import markdown
import bs4
import os
from google import genai
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional, List
import generate_image as gi

load_dotenv()
SEP = "-" * 100


class MarkdownData(BaseModel):
    title: str
    paragraph: List[str]
    all_text: str


# --- PydanticモデルによるJSONスキーマ定義 ---
class CharacterInfo(BaseModel):
    """登場キャラクターに関する情報"""

    type: Optional[str] = Field(
        None,
        description="キャラクターの種類（例: 人間, 動物, 植物, 架空の生物, ロボット, 擬人化されたオブジェクト）",
    )  # Nキャラクタータイプ
    name: Optional[str] = Field(
        None, description="キャラクターの名前や呼称（もしあれば。種族名なども可）"
    )
    attributes: Optional[str] = Field(
        None,
        description="キャラクターの属性（性別、年齢、種類、品種、状態など。例: 若い女性, オスの老犬, 満開の桜, 古いロボット）",
    )
    appearance: Optional[str] = Field(
        None,
        description="外見の特徴（服装、体型、毛並み、色、形、大きさ、質感、光沢など。例: 青いドレス, 銀色の毛並み, 緑の葉が茂っている, 金属製のボディ）",
    )
    state_action: Optional[str] = Field(
        None,
        description="キャラクターの状態や行動（表情、ポーズ、動作、様子など。例: 微笑んでいる, 尻尾を振っている, 風に揺れている, 赤く点滅している）",
    )


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
    *   **登場キャラクター (characters)**: シーンに登場する各キャラクター（人間、動物、植物、擬人化された物など）について、以下の情報を**リスト形式**で抽出してください。リストの各要素は一体のキャラクターに対応します。
        *   **種類 (type)**: キャラクターの種類（例: 人間, 犬, 猫, 木, ロボット, 喋るティーポット）
        *   名前 (name): 名前や呼称（もしあれば）
        *   属性 (attributes): 性別、年齢、種類、品種、状態など（例: 少年, 白い子猫, 大きな柳の木, 旧式の警備ドローン）
        *   外見 (appearance): 服装、体型、毛並み、色、形、大きさ、質感など（例: 赤いセーター, ふさふさの尻尾, 緑の葉が茂っている, 傷のついた金属）
        *   状態・行動 (state_action): 表情、ポーズ、動作、様子など（例: 驚いた顔, 丸くなって眠っている, 枝が風に揺れている, ゆっくりと回転している）
    *   場所 (location): 具体的な場所、屋内/屋外、時代設定、雰囲気・特徴
    *   時間・天候 (time_weather): 時間帯、季節、天気、光の状態
    *   行動・状況 (action_situation): キャラクター（達）の行動（主要なアクション）、全体の状況
    *   感情・雰囲気 (emotion_atmosphere): シーンの雰囲気、キャラクター（達）の感情や状態
    *   重要なオブジェクト (important_objects): キャラクターとして扱わない、シーンの鍵となる物や小物のリスト
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
        model="gemini-2.5-pro-exp-03-25",
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
    def get_photo_prompt(story, scene) -> str:
        style_keywords = [
            "best quality",
            "ultra high res",
            "(photorealistic:1.4)",
            "RAW photo",
            "photorealistic",  # 最重要: 写真のようにリアル
            "hyperrealistic",  # 超リアル
            "realistic photo",  # リアルな写真
            "high detail",  # 高精細
            "highly detailed skin texture",  # (人物の場合) 詳細な肌の質感
            "sharp focus",  # シャープなピント (被写体に応じて)
            "professional photography",  # プロの写真
            "cinematic lighting",  # 映画的な照明 (ドラマチックに)
            "soft shadows",  # 柔らかい影 (自然に見える)
            "realistic textures",  # リアルな質感 (布、木、金属など)
            "shot on high-resolution DSLR camera",
        ]

        selected_styles = ", ".join(style_keywords)

        prompt = f"""
        # 指示
        あなたは優秀なフォトグラファー、またはフォトリアルCGアーティストのアシスタントです。
        以下の本文とシーン設定を注意深く読み、**極めてリアルな実写写真、または写真と見分けがつかないレベルのCG画像**を生成してください。
        光と影の自然な表現、被写体の質感、空気感、細部のディテールに最大限こだわり、**絶対にイラスト、アニメ、3Dモデルに見えない**ようにしてください。

        # 作風
        {selected_styles}

        # 人種
        日本人

        # 本文
        {story}

        # シーン
        {scene}
        """
        return prompt.strip()

    def get_ghibli_anime_prompt(story, scene) -> str:
        style_keywords = [
            "Studio Ghibli style",
            "anime screenshot appearance",  # 重要: アニメ画面感を強く指示
            "hand-drawn animation look",  # 重要: 手描きアニメのルック
            "painted backgrounds",  # ジブリ背景の特徴 (これは維持)
            "lush green landscapes",  # ジブリ風景
        ]

        selected_styles = ", ".join(style_keywords)

        prompt = f"""
        # 指示
        あなたは優秀なアニメーション監督のアシスタントです。
        以下の本文を注意深く読み、このシーンに対するイラストを生成してください。

        # 作風
        {selected_styles}

        # 人種
        日本人

        # 本文
        {story}

        # シーン
        {scene}
        """
        return prompt.strip()

    def get_modern_anime_prompt(story, scene) -> str:
        # 現代風アニメのスタイルキーワードリスト
        # 必要に応じてキーワードを追加・削除・調整してください
        style_keywords = [
            "modern anime style",
            "anime key visual",
            "anime screencap",
            "vibrant colors",
            "bright lighting",  # または "dramatic lighting", "dynamic lighting" などシーンに応じて
            "clean linework",
            "sharp focus",
            "cel shading",  # セルルックの影表現
            "detailed character design",
            "contemporary anime aesthetic",
            "digital illustration",
            "smooth gradients",  # 滑らかなグラデーション
            "detailed background",  # 背景の描き込み
            "dynamic composition",  # ダイナミックな構図
        ]

        selected_styles = ", ".join(style_keywords)

        prompt = f"""
        # 指示
        あなたは優秀なアニメーション監督のアシスタントです。
        以下の本文を注意深く読み、このシーンに対するイラストを生成してください。

        # 作風
        {selected_styles}

        # 人種
        日本人

        # 本文
        {story}

        # シーン
        {scene}
        """

        return prompt.strip()

    def get_kids_anime_prompt(story, scene) -> str:
        # 現代風・かわいい・ポップ・子供向けアニメのスタイルキーワードリスト
        style_keywords = [
            "cute anime style",  # かわいいアニメスタイル
            "kawaii aesthetic",  # カワイイの美学
            "children's anime style",  # 子供向けアニメスタイル
            "pop and colorful aesthetic",  # ポップでカラフルな美学
            "bright and cheerful colors",  # 明るく楽しい色使い
            "vibrant colors",  # 鮮やかな色彩
            "bright and soft lighting",  # 明るく柔らかい光
            "clean and simple linework",  # クリーンでシンプルな線画
            "rounded shapes and forms",  # 丸みを帯びた形状（かわいらしさ）
            "simple cel shading",  # シンプルなセルルックの影
            "adorable character design",  # とても可愛いキャラクターデザイン
            "big expressive eyes",  # 大きな感情豊かな目
            "chibi proportions",  # チビキャラの比率（デフォルメ感を強調）
            "digital illustration",  # デジタルイラストレーション
            "smooth gradients",  # 滑らかなグラデーション
            "simple and colorful background",  # シンプルでカラフルな背景
            "fun and energetic atmosphere",  # 楽しく元気な雰囲気
            "playful composition",  # 遊び心のある構図
            "clear and easy to understand",  # 分かりやすい画面
        ]

        selected_styles = ", ".join(style_keywords)

        prompt = f"""
        # 指示
        あなたは明るく楽しい子供向けアニメーションの制作アシスタントです。
        以下の本文を注意深く読み、このシーンに対する**非常にキュートでポップな子供向けアニメ**のイラストを生成してください。

        # 作風
        {selected_styles}

        # 人種

        # 本文
        {story}

        # シーン
        {scene}
        """

        return prompt.strip()

    def get_manga_prompt(story, scene) -> str:
        # スタイルキーワード (少年漫画・カラー向けに選定)
        style_keywords = [
            "manga style",
            "Japanese comic style",
            "shonen manga style",  # 少年漫画スタイル
            "color manga page",  # カラー漫画ページ
            "vibrant colors",  # 鮮やかな色彩
            "digital manga coloring",  # デジタル彩色
            "clean coloring",
            "dynamic composition",  # ダイナミックな構図
            "expressive characters",  # 表情豊かなキャラクター
            "detailed linework",  # 詳細な線画
            "dynamic action poses",  # ダイナミックなアクションポーズ
            "intense expressions",  # 激しい表情
            "single manga panel",  # 漫画の1コマ ★追加
            "comic panel",  # コミックのコマ ★追加
            "framed panel view",  # 枠線のあるコマ視点 ★追加
        ]
        selected_styles = ", ".join(style_keywords)

        # ネガティブプロンプト (複数コマやページレイアウトを除外)
        negative_prompts_keywords = [
            # 基本的な除外要素
            "photorealistic",
            "3D render",
            "low quality",
            "blurry",
            "watermark",
            "signature",
            "ugly",
            "disfigured",
            "poorly drawn",
            # スタイルに関する除外要素
            "monochrome",
            "black and white",
            "screentone",
            "shojo style",
            "soft atmosphere",
            "delicate lines",
            "floral patterns",
            "kawaii",
            "chibi",
            "watercolor",
            "oil painting",
            "sketch",
            # 吹き出し・文字関連の除外キーワード
            "speech bubble",
            "dialogue bubble",
            "text bubble",
            "word balloon",
            "text",
            "dialogue",
            "words",
            "letters",
            "font",
            "writing",
            "onomatopoeia",
            "sound effects text",
            "narration box",
            "caption",
            "subtitle",
            "logo",
            # --- 複数コマ・ページレイアウト関連の除外キーワード ---
            "multiple panels",  # 複数のコマ ★追加
            "comic page layout",  # ページレイアウト ★追加
            "full page spread",  # 見開きページ ★追加
            "manga page",  # ページ全体 ★追加 (color manga page との混同避けるため注意)
            "storyboard",  # ストーリーボード ★追加
            "grid layout",  # グリッドレイアウト ★追加
            "panel borders touching",  # 隣接するコマ枠 ★追加
        ]
        # 重複除去して結合
        negative_prompt_string = ", ".join(negative_prompts_keywords)

        prompt = f"""
        # 指示
        あなたは熟練の漫画家アシスタントです。
        以下の本文とシーン設定を読み、**カラーの少年漫画（コミック）の『1コマ』だけ**を描いてください。
        生成するのは、**枠線で区切られた単一の漫画パネル**です。ページ全体や複数のコマを描画しないでください。
        線画のタッチ、カラー彩色、キャラクターの表情やポーズ、効果線などに、**エネルギッシュでダイナミックな少年漫画**的な表現を強く意識してください。
        **重要：生成する1コマのイラストには、いかなる種類の吹き出し、セリフ、文字、テキスト、ロゴも絶対に含めないでください。純粋なイラストレーションのコマのみを生成してください。**

        # 作風
        {selected_styles}
        上記のキーワードに基づき、**カラーの少年漫画**の特徴を捉えたイラストを生成してください。

        # 色モード
        color

        # ジャンル
        shonen

        # 本文
        {story}

        # シーン
        {scene}

        # ネガティブプロンプト (重要: 吹き出し・文字・複数コマを除外)
        --no {negative_prompt_string}
        """

        return prompt.strip()

    content = data.paragraph[target_index]
    # indexが進むにつれて、全文を増やす
    prev_text = "".join(data.paragraph[:target_index])
    # ic(content, prev_text)
    scene = get_scene(content, prev_text)

    prompt = get_photo_prompt(content, scene)
    # ic(prompt)
    return gi.generate_image_from_text_google(prompt)


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
    with open("work/14.md", "r", encoding="utf-8") as f:
        input_text = f.read()

    data = markdown_to_data(input_text)

    # ic(data)

    for i in range(len(data.paragraph)):
        result = generate_image(data, i)
        print(result)


if __name__ == "__main__":
    main()
