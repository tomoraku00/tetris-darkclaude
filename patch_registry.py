import re

with open('tools/registry.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# _TOOLS に codegraph_explore を追加
content = content.replace(
    'from tools import bash, glob, read_file, str_replace, write_file',
    'from tools import bash, glob, read_file, str_replace, write_file, codegraph_explore'
)
content = content.replace(
    '\"str_replace\": str_replace.run,',
    '\"str_replace\": str_replace.run,\n    \"codegraph_explore\": codegraph_explore.run,'
)

# TOOL_SCHEMAS に追加（bash スキーマの後に追加）
codegraph_schema = '''
    {
        \"type\": \"function\",
        \"function\": {
            \"name\": \"codegraph_explore\",
            \"description\": \"コードベースのシンボル・関数・クラス・依存関係を検索する。grep/glob/read_file より高速で効率的。\",
            \"parameters\": {
                \"type\": \"object\",
                \"properties\": {
                    \"query\": {\"type\": \"string\", \"description\": \"検索クエリ (例: 'dispatch tool_call', 'chat_turn loop')\"},
                },
                \"required\": [\"query\"],
            },
        },
    },'''

content = content.replace('_PLAN_BLOCKED', codegraph_schema + '\n]\n_PLAN_BLOCKED_DUMMY = None\n_PLAN_BLOCKED', 1)
content = content.replace('_PLAN_BLOCKED_DUMMY = None\n', '')

with open('tools/registry.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
