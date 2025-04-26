from icecream import ic
import json
import markdown
import bs4
import json
import re


def markdown_to_json(markdown_file):
    """
    マークダウンファイルをJSONに変換する汎用的なメソッド
    """
    with open(markdown_file, "r", encoding="utf-8") as f:
        markdown_text = f.read()

    html = markdown.markdown(markdown_text)
    soup = bs4.BeautifulSoup(html, "html.parser")

    title = soup.find("h2").text

    paragraphs = []
    for p in soup.find_all("p"):
        text = p.text.replace("\n", "").replace(" ", "")
        paragraphs.append({"p": text})

    return json.dumps({"title": title, "paragraph": paragraphs}, ensure_ascii=False)


def main():
    # ファイルを読み込む
    with open("work/01.md", "r", encoding="utf-8") as f:
        text = f.read()

    data = markdown_to_json("work/01.md")
    ic(data)


if __name__ == "__main__":
    main()
