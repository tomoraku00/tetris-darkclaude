#!/usr/bin/env python3
"""テキスト解析ツール - 単語分割・カウント・JSON出力"""

import json
import re
import sys
from collections import Counter


def analyze_text(text: str) -> dict:
    """テキストを解析し、統計情報を辞書として返す。

    Args:
        text: 解析対象のテキスト文字列

    Returns:
        以下の情報を含む辞書:
            - char_count: 文字数（空白・改行含む）
            - word_count: 単語数
            - line_count: 行数
            - top_10_words: 出現頻度の上位10単語 (word, count)
    """
    # 行数のカウント
    lines = text.splitlines()
    line_count = len(lines)

    # 文字数（空白・改行含む）
    char_count = len(text)

    # 単語に分割（英数字とアクセント記号を含む単語を抽出）
    words = re.findall(r"[a-zA-Z0-9\u00C0-\u017F]+", text.lower())
    word_count = len(words)

    # 出現頻度の上位10単語
    counter = Counter(words)
    top_10_words = [
        {"word": word, "count": count}
        for word, count in counter.most_common(10)
    ]

    return {
        "char_count": char_count,
        "word_count": word_count,
        "line_count": line_count,
        "top_10_words": top_10_words,
    }


def main():
    """コマンドラインからファイルを読み込み、解析結果をJSONで出力する。"""
    if len(sys.argv) < 2:
        print("使用方法: python text_analyzer.py <ファイルパス>")
        sys.exit(1)

    file_path = sys.argv[1]

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"エラー: ファイル '{file_path}' が見つかりません。")
        sys.exit(1)
    except UnicodeDecodeError:
        print(f"エラー: ファイル '{file_path}' の読み込みに失敗しました（エンコード問題）。")
        sys.exit(1)

    result = analyze_text(text)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
