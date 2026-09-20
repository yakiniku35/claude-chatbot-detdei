"""測試用的共用 fixture。

``src/app.py`` 是單檔 Streamlit 應用，模組層級就會呼叫 ``st.set_page_config()``
等介面函式，所以不能直接 ``import app``。這裡只擷取「# 5. 介面」之前的段落
（常數、提示詞組裝、API 呼叫層、選用功能），用 exec 載成一個獨立模組，
測試就能針對這些純邏輯函式做驗證，而不會啟動任何 UI。
"""

from __future__ import annotations

import types
from pathlib import Path

import pytest
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_FILE = PROJECT_ROOT / "src" / "app.py"

# 介面段落的起點；之前的內容全是定義，載入時不會產生副作用
SECTION_MARKER = "# 5. 介面"
BANNER_PREFIX = "# " + "-" * 10


def _load_app_logic() -> types.ModuleType:
    """把 app.py 介面段落以前的程式碼載成模組。"""
    source = APP_FILE.read_text(encoding="utf-8")
    marker_at = source.index(SECTION_MARKER)
    # 連同 marker 上方的分隔線一起切掉，避免殘留半截註解
    cut_at = source.rindex(BANNER_PREFIX, 0, marker_at)
    head = source[:cut_at]

    module = types.ModuleType("app_logic")
    # APP_DIR / PROJECT_ROOT / PROMPT_FILE 都由 __file__ 推算，必須指向真實路徑
    module.__dict__["__file__"] = str(APP_FILE)
    exec(compile(head, str(APP_FILE), "exec"), module.__dict__)
    return module


@pytest.fixture(scope="session")
def app() -> types.ModuleType:
    """整個測試階段只載入一次 app.py 的純邏輯部分。"""
    return _load_app_logic()


class FakeSessionState(dict):
    """dict 版的 st.session_state：支援屬性與鍵值兩種存取方式。

    沒有 ``streamlit run`` 時真正的 session_state 行為會隨版本而異，
    直接換成 dict 可以讓冷卻時間相關的測試穩定且互不影響。
    """

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        self[name] = value


@pytest.fixture(autouse=True)
def session_state(monkeypatch) -> FakeSessionState:
    """每個測試都拿到乾淨的 session_state（含空的 model_cooldowns）。"""
    state = FakeSessionState(model_cooldowns={})
    monkeypatch.setattr(st, "session_state", state)
    return state
