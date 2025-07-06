import math
from icecream import ic


def split_text(text: str) -> list[str]:
    """
    テキストをsplit_size字以下になるまで分割する。
    split_size字以内の場合は分割しない。
    分割数は動的に決定する。
    """

    split_size = 300

    if len(text) <= split_size:
        return [text]

    parts = [text]
    result = []

    while parts:
        part = parts.pop(0)
        if len(part) <= split_size:
            result.append(part)
        else:
            # 分割数を決定
            num_splits = math.ceil(len(part) / split_size)
            # 各パーツの目標サイズを計算
            part_size = math.ceil(len(part) / num_splits)
            for i in range(num_splits):
                start = i * part_size
                end = (i + 1) * part_size if i < num_splits - 1 else len(part)
                parts.append(part[start:end])

    # ic(result)
    return result
