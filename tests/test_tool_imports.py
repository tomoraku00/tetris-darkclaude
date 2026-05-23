"""tools の import テスト - 起動時バリデーション用"""
import sys
sys.path.insert(0, r"C:\Users\tomo_rrow\Documents\nanoclaude")

def test_tool_imports():
    from tools import read_file, write_file, bash, glob, str_replace
    assert callable(read_file.run)
    assert callable(write_file.run)
    assert callable(bash.run)
    assert callable(glob.run)
    assert callable(str_replace.run)

def test_registry_import():
    from tools.registry import TOOL_SCHEMAS, dispatch
    assert isinstance(TOOL_SCHEMAS, list)
    assert len(TOOL_SCHEMAS) > 0
    assert callable(dispatch)

def test_path_import():
    from pathlib import Path
    from tools import read_file, str_replace
    import inspect
    assert "Path" in inspect.getsource(read_file)
    assert "Path" in inspect.getsource(str_replace)

if __name__ == "__main__":
    test_tool_imports()
    test_registry_import()
    test_path_import()
    print("All tests passed!")