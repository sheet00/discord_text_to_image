from icecream import ic
import json
import markdown


def markdown_to_json(markdown_file):
    """
    マークダウンファイルをJSONに変換する汎用的なメソッド
    """
    with open(markdown_file, "r", encoding="utf-8") as f:
        markdown_text = f.read()

    html = markdown.markdown(markdown_text)
    return {"html": html}


def main():
    # ファイルを読み込む
    with open("work/01.md", "r", encoding="utf-8") as f:
        text = f.read()

    data = markdown_to_json("work/01.md")
    ic(data)


if __name__ == "__main__":
    main()
