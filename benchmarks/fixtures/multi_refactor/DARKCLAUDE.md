# multi_refactor

プロセッサパイプラインのリファクタリングタスク (T06) 用。

## ファイル構成

- pipeline.py: パイプラインエントリポイント (_REGISTRY でプロセッサを管理)
- processors/: 各フォーマットのプロセッサ
  - text_processor.py, csv_processor.py, json_processor.py
  - xml_processor.py, binary_processor.py

## 作業方針

glob で全プロセッサを確認 → read_file で共通パターンを把握 →
共通基底クラスへの切り出しや重複排除などのリファクタリングを実施。
変更後は既存の動作が壊れていないことを確認する。
