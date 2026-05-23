import time


class Timer:
    """シンプルなタイマークラス"""
    
    def __init__(self):
        self._start_time = None
        self._elapsed = 0.0
        self._running = False
    
    def start(self) -> None:
        """タイマーを開始する"""
        if self._running:
            return
        self._start_time = time.time() - self._elapsed
        self._running = True
    
    def stop(self) -> float:
        """タイマーを停止し、経過時間を秒単位で返す"""
        if not self._running:
            return self._elapsed
        self._elapsed = time.time() - self._start_time
        self._running = False
        return self._elapsed
    
    def reset(self) -> None:
        """タイマーをリセットする"""
        self._start_time = None
        self._elapsed = 0.0
        self._running = False
    
    @property
    def elapsed(self) -> float:
        """現在の経過時間（実行中の場合はリアルタイムで計測）"""
        if self._running:
            return time.time() - self._start_time
        return self._elapsed
