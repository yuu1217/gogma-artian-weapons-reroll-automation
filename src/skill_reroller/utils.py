from difflib import SequenceMatcher


def is_fuzzy_match(target: str, skill: str, threshold: float) -> bool:
    """
    ターゲット文字列がスキル文字列に含まれているか、あるいは類似しているかを判定する。
    """
    if target in skill:
        return True

    len_t = len(target)
    len_s = len(skill)

    if len_s < len_t:
        ratio = SequenceMatcher(None, target, skill).ratio()
        return ratio >= threshold

    # スライディングウィンドウで類似度判定
    for i in range(len_s - len_t + 1):
        window = skill[i : i + len_t]
        ratio = SequenceMatcher(None, target, window).ratio()
        if ratio >= threshold:
            return True
    return False


def calculate_similarity(text1: str, text2: str) -> float:
    """
    2つの文字列の類似度を計算する (0.0 - 1.0)
    """
    return SequenceMatcher(None, text1, text2).ratio()
