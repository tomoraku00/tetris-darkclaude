import os


class FileManager:
    def __init__(self, directory='.'):
        self.directory = directory

    def create_file(self, filename: str, content: str = '') -> None:
        """ファイルを作成します。"""
        filepath = os.path.join(self.directory, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    def read_file(self, filename: str) -> str:
        """ファイルの内容を読み込みます。"""
        filepath = os.path.join(self.directory, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"ファイル '{filename}' は存在しません。")
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def delete_file(self, filename: str) -> None:
        """ファイルを削除します。"""
        filepath = os.path.join(self.directory, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"ファイル '{filename}' は存在しません。")
        os.remove(filepath)


if __name__ == '__main__':
    fm = FileManager()

    # ファイル作成
    fm.create_file('test.txt', 'こんにちは、世界！')

    # ファイル読み込み
    print(fm.read_file('test.txt'))

    # ファイル削除
    fm.delete_file('test.txt')
    print('ファイルを削除しました。')
