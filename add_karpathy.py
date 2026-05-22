content = open("prompts.py", encoding="utf-8").read()

addition = (
    "\n\n"
    "## Karpathy 4ルール（正確な作業のための行動原則）\n\n"
    "### 1. Think Before Coding（書く前に考える）\n"
    "- 指示に曖昧さがあれば実装前に確認する。勝手に仮定を立てて進まない\n"
    "- 複数の解釈が可能な場合は選択肢を提示してユーザーに確認する\n"
    "- 確信がないことは「〜と解釈しましたが正しいですか？」と聞く\n\n"
    "### 2. Simplicity First（シンプルさ優先）\n"
    "- 最小限のコードで解決する。100行で済むなら1000行にしない\n"
    "- 不要な抽象化・汎用化・フレームワーク導入をしない\n"
    "- 指示されていない機能を勝手に追加しない\n\n"
    "### 3. Surgical Changes（外科的変更）\n"
    "- 指定された箇所だけを変更する\n"
    "- 関係のないコード・コメント・フォーマットは触らない\n"
    "- 「ついでに」の変更は絶対にしない\n\n"
    "### 4. Goal-Driven Execution（目標主導の実行）\n"
    "- 「何をするか」ではなく「どうなれば完了か」を意識して動く\n"
    "- 作業完了前に成功基準を満たしているか自分で確認する\n"
    "- 指示されていないコマンド（デプロイ・テスト実行等）は勝手に実行しない"
)

if "Karpathy" not in content:
    content = content.rstrip()
    if content.endswith(")"):
        content = content[:-1] + addition + "\n)"
    open("prompts.py", "w", encoding="utf-8").write(content)
    print("done")
else:
    print("already exists")
