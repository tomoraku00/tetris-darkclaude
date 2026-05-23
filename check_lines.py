with open('prompts.py', encoding='utf-8-sig') as f:
    lines = f.readlines()

# 例3の末尾を探す
for i, line in enumerate(lines):
    if 'get_user(' in line and 'fetch_user' in line:
        print(f'Line {i}: {repr(line)}')
    if 'ファイル更新' in line or 'file' in line.lower():
        print(f'Line {i}: {repr(line[:50])}')
