"""Windows タスクバーアイコン進捗制御 (ITaskbarList3 / ctypes)

pywin32 不要。ctypes (組み込み) のみで ITaskbarList3 COM インターフェースを操作する。
Windows 以外では全関数が no-op になり、エラーは起きない。
"""
import sys

_AVAILABLE = sys.platform == "win32"
_ctrl: "object | None" = None

if _AVAILABLE:
    try:
        import ctypes
        import ctypes.wintypes

        _TBPF_NOPROGRESS    = 0x0
        _TBPF_INDETERMINATE = 0x1
        _TBPF_NORMAL        = 0x2
        _TBPF_ERROR         = 0x4

        class _GUID(ctypes.Structure):
            _fields_ = [
                ("Data1", ctypes.c_ulong),
                ("Data2", ctypes.c_ushort),
                ("Data3", ctypes.c_ushort),
                ("Data4", ctypes.c_ubyte * 8),
            ]

        def _make_guid(d1: int, d2: int, d3: int, d4: list[int]) -> "_GUID":
            g = _GUID()
            g.Data1, g.Data2, g.Data3 = d1, d2, d3
            for i, b in enumerate(d4):
                g.Data4[i] = b
            return g

        # ITaskbarList3
        _CLSID_TaskbarList = _make_guid(
            0x56FDF344, 0xFD6D, 0x11D0,
            [0x95, 0x8A, 0x00, 0x60, 0x97, 0xC9, 0xA0, 0x90],
        )
        _IID_ITaskbarList3 = _make_guid(
            0xEA1AFB91, 0x9E28, 0x4B86,
            [0x90, 0xE9, 0x9E, 0x9F, 0x8A, 0x5E, 0xEF, 0xAF],
        )

        # vtable オフセット
        _V_HrInit           = 3
        _V_SetProgressValue = 9
        _V_SetProgressState = 10

        _ole32   = ctypes.windll.ole32
        _kernel32 = ctypes.windll.kernel32

        class _TaskbarCtrl:
            """ITaskbarList3 の薄いラッパー。失敗時は全メソッドが no-op。"""

            def __init__(self) -> None:
                self._ptr: int | None = None
                self._vtbl = None
                self._hwnd: int = 0
                self.ok: bool = False
                try:
                    _ole32.CoInitialize(None)
                    p = ctypes.c_void_p()
                    hr = _ole32.CoCreateInstance(
                        ctypes.byref(_CLSID_TaskbarList),
                        None,
                        1,  # CLSCTX_INPROC_SERVER
                        ctypes.byref(_IID_ITaskbarList3),
                        ctypes.byref(p),
                    )
                    if hr != 0 or not p.value:
                        return
                    self._ptr = p.value
                    vptr = ctypes.cast(self._ptr, ctypes.POINTER(ctypes.c_void_p))[0]
                    self._vtbl = ctypes.cast(vptr, ctypes.POINTER(ctypes.c_void_p))
                    # HrInit を呼んで有効化
                    _FT = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p)
                    _FT(self._vtbl[_V_HrInit])(self._ptr)
                    # コンソール (Windows Terminal) の HWND を取得
                    self._hwnd = _kernel32.GetConsoleWindow()
                    self.ok = bool(self._hwnd)
                except Exception:
                    pass

            def set_state(self, state: int) -> None:
                if not self.ok:
                    return
                try:
                    _FT = ctypes.WINFUNCTYPE(
                        ctypes.HRESULT, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint
                    )
                    _FT(self._vtbl[_V_SetProgressState])(self._ptr, self._hwnd, state)
                except Exception:
                    pass

            def set_value(self, value: int, total: int = 100) -> None:
                if not self.ok:
                    return
                try:
                    _FT = ctypes.WINFUNCTYPE(
                        ctypes.HRESULT,
                        ctypes.c_void_p, ctypes.c_void_p,
                        ctypes.c_ulonglong, ctypes.c_ulonglong,
                    )
                    _FT(self._vtbl[_V_SetProgressValue])(self._ptr, self._hwnd, value, total)
                except Exception:
                    pass

        _ctrl = _TaskbarCtrl()
        _AVAILABLE = _ctrl.ok  # type: ignore[attr-defined]

    except Exception:
        _AVAILABLE = False


def working() -> None:
    """作業中: タスクバーアイコンをオレンジの不確定進捗に。"""
    if _ctrl and _AVAILABLE:
        _ctrl.set_state(_TBPF_INDETERMINATE)  # type: ignore[name-defined]


def done() -> None:
    """完了: タスクバーアイコンを緑 100% に。"""
    if _ctrl and _AVAILABLE:
        _ctrl.set_state(_TBPF_NORMAL)          # type: ignore[name-defined]
        _ctrl.set_value(100)


def error() -> None:
    """エラー: タスクバーアイコンを赤に。"""
    if _ctrl and _AVAILABLE:
        _ctrl.set_state(_TBPF_ERROR)           # type: ignore[name-defined]
        _ctrl.set_value(100)


def clear() -> None:
    """通常状態に戻す。"""
    if _ctrl and _AVAILABLE:
        _ctrl.set_state(_TBPF_NOPROGRESS)      # type: ignore[name-defined]
