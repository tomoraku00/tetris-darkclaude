content = open('tools/registry.py', encoding='utf-8', errors='replace').read()
# ]\n    { を ]\n→ 削除して { に修正
fixed = content.replace('],\n]\n_PLAN_BLOCKED', ']\n_PLAN_BLOCKED', 1)
fixed = fixed.replace('    },\n]\n    {\n        \"type\": \"function\",\n        \"function\": {\n            \"name\": \"codegraph_explore\"', '    },\n    {\n        \"type\": \"function\",\n        \"function\": {\n            \"name\": \"codegraph_explore\"', 1)
# 最初の ] を消す
fixed = fixed.replace(',\n]\n    {\n        \"type\": \"function\",\n        \"function\": {\n            \"name\": \"codegraph_explore\"', ',\n    {\n        \"type\": \"function\",\n        \"function\": {\n            \"name\": \"codegraph_explore\"', 1)
open('tools/registry.py', 'w', encoding='utf-8').write(fixed)
print('done')
