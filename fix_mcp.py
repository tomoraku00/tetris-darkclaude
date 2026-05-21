import json
path = r'C:\Users\tomo_rrow\.claude.json'
with open(path, 'r', encoding='utf-8') as f:
    config = json.load(f)
config['projects']['C:/Users/tomo_rrow/Documents/nanoclaude']['mcpServers']['codegraph'] = {
    'type': 'stdio',
    'command': 'codegraph',
    'args': ['serve', '--mcp']
}
with open(path, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
print('Done')
