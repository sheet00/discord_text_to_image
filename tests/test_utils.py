import utils as utils


def test_split_size_or_less():
    """split_size以下の長さのテキストは分割されないこと"""
    # Arrange
    text = "あ" * 300

    # Act
    result = utils.split_text(text)

    # Assert
    assert result == [text]


def test_longer_than_split_size():
    """split_sizeより長いテキストが適切に分割されること"""
    # Arrange
    text = "あ" * 1000
    expected_len = 4  # 1000 / 300 = 3.33... -> 4分割
    expected_part_len = 250

    # Act
    result = utils.split_text(text)

    # Assert
    assert len(result) == expected_len
    assert len(result[0]) == expected_part_len
    assert len(result[1]) == expected_part_len
    assert len(result[2]) == expected_part_len
    assert len(result[3]) == expected_part_len
    assert "".join(result) == text


def test_multiple_of_split_size():
    """split_sizeの倍数の長さのテキストが適切に分割されること"""
    # Arrange
    text = "あ" * 800
    expected_len = 3  # 800 / 300 = 2.66... -> 3分割
    expected_part_len1 = 267
    expected_part_len2 = 267
    expected_part_len3 = 266

    # Act
    result = utils.split_text(text)

    # Assert
    assert len(result) == expected_len
    assert len(result[0]) == expected_part_len1
    assert len(result[1]) == expected_part_len2
    assert len(result[2]) == expected_part_len3
    assert "".join(result) == text


def test_example():

    # Arrange
    text = """
むかしむかし、あるところに、カモ取りのごんべえさんという人がいました。
ある朝、ごんべえさんは、近くの池へ行ってみてビックリ。
仕掛けておいたワナに、数え切れないほどのカモがかかっていたのです。
おまけに池には氷が張っているので、カモたちは動けずにいる様子です。
ごんべえさんは大喜びでワナのアミを集めると、池の氷が溶けるまで見張る事にしました。
そしてうっかり居眠りしてしまい、気がついた時には、もう池の氷は溶けていたのです。
「おっと、大変」
あわてた時は、もう遅く、目を覚ましたカモたちがバタバタバタと飛び立ち、それと一緒にごんべえさんもカモたちに引っ張られて空へ舞いあがってしまいました。
カモたちはごんべえさんをぶらさげたまま、野をこえ、山をこえ、谷をこえ。
「たっ、たすけてくれー！」
叫んでいるうちに、うっかりアミを離してしまいました。
"""
    utils.split_text(text)


def test_empty_string():
    """空文字列が分割されないこと"""
    # Arrange
    text = ""

    # Act
    result = utils.split_text(text)

    # Assert
    assert result == [""]
