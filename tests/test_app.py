"""src/app.py 純邏輯函式的測試。

重點放在曾經出過問題、且只靠人工 review 才抓到的行為：
1. classify_error 不能用裸數字比對狀態碼（429 訊息裡本來就含有 "413"）
2. detect_language 必須先判斷假名，否則純漢字的日文會被當成中文
3. available_models 全部冷卻時不能退回完整清單（會形成活鎖）
"""

from __future__ import annotations

import time
import types

import groq
import httpx
import pytest


# ---------------------------------------------------------------------------
# 測試用的小工具
# ---------------------------------------------------------------------------

REQUEST = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")


def api_error(status: int, message: str = "error") -> groq.APIStatusError:
    """建立帶有真實 HTTP 狀態碼的 Groq 例外。

    一定要透過 httpx.Response 建立，status_code 屬性才會被填好；
    只傳訊息字串的假例外無法驗證「狀態碼優先於文字比對」這條規則。
    """
    return groq.APIStatusError(
        message,
        response=httpx.Response(status, request=REQUEST),
        body=None,
    )


def make_chunk(content: str | None = None, finish_reason: str | None = None):
    """模擬 Groq 串流回傳的 chunk。"""
    choice = types.SimpleNamespace(
        delta=types.SimpleNamespace(content=content),
        finish_reason=finish_reason,
    )
    return types.SimpleNamespace(choices=[choice])


class FakeGroqClient:
    """假客戶端：記錄被呼叫過的模型，由 responder 決定成功或丟例外。"""

    def __init__(self, responder):
        self.calls: list[str] = []
        self._responder = responder
        self.chat = types.SimpleNamespace(
            completions=types.SimpleNamespace(create=self._create)
        )

    def _create(self, *, model, messages, **kwargs):
        self.calls.append(model)
        result = self._responder(model)
        if isinstance(result, Exception):
            raise result
        return result


# ---------------------------------------------------------------------------
# classify_error
# ---------------------------------------------------------------------------

class TestClassifyError:
    def test_rate_limit_message_containing_413_is_not_too_large(self, app):
        """迴歸測試：429 的訊息本身就含有 413 這串數字。

        真實的 Groq 429 內容像是 "Used 11413" 與 "try again in 2.413s"，
        若用 `"413" in message` 判斷會被歸類成 too_large 而直接中止，
        整條模型降級鏈都不會被嘗試。
        """
        exc = api_error(
            429,
            "Rate limit reached for model `openai/gpt-oss-120b`: Limit 12000, "
            "Used 11413, Requested 900. Please try again in 2.413s.",
        )
        assert app.classify_error(exc) == "rate_limit"

    def test_too_large_uses_status_code(self, app):
        exc = api_error(413, "Request too large for model")
        assert app.classify_error(exc) == "too_large"

    @pytest.mark.parametrize("status", [401, 403])
    def test_auth(self, app, status):
        assert app.classify_error(api_error(status, "Invalid API Key")) == "auth"

    def test_model_gone(self, app):
        exc = api_error(404, "The model `foo` does not exist")
        assert app.classify_error(exc) == "model_gone"

    @pytest.mark.parametrize("status", [500, 502, 503])
    def test_server_error(self, app, status):
        assert app.classify_error(api_error(status, "upstream error")) == "server_error"

    def test_timeout_is_transient(self, app):
        """APITimeoutError 的字串是 "Request timed out."，並不含 "timeout"。"""
        exc = groq.APITimeoutError(request=REQUEST)
        assert "timeout" not in str(exc).lower()  # 說明為何不能只比對 "timeout"
        assert app.classify_error(exc) == "transient"

    def test_connection_error_is_transient(self, app):
        exc = groq.APIConnectionError(request=REQUEST)
        assert app.classify_error(exc) == "transient"

    def test_all_models_cooling(self, app):
        assert app.classify_error(app.AllModelsCoolingError(42)) == "cooling"

    def test_unknown_error_is_fatal(self, app):
        assert app.classify_error(ValueError("something odd")) == "fatal"

    def test_status_parsed_from_message_when_attribute_missing(self, app):
        """沒有 status_code 屬性時才退回文字解析，且只認 "error code: NNN"。"""
        assert app.http_status(Exception("Error code: 429 - rate limited")) == 429
        # 訊息裡夾帶的數字（配額、秒數）不能被當成狀態碼
        assert app.http_status(Exception("Used 11413 tokens in 2.413s")) is None

    def test_plain_rate_limit_text_without_status(self, app):
        exc = Exception("Rate limit exceeded, Used 11413 tokens")
        assert app.classify_error(exc) == "rate_limit"


# ---------------------------------------------------------------------------
# detect_language
# ---------------------------------------------------------------------------

class TestDetectLanguage:
    @pytest.mark.parametrize(
        "text",
        [
            "我們這樣寫可以嗎？",
            "請問繁體中文的政策需要調整嗎",
            "台灣台北的分公司要辦女性領導力培訓",  # 「台」是繁體標準用字
            "我們在臺北與台中都有據點",
        ],
    )
    def test_traditional_chinese(self, app, text):
        assert app.detect_language(text) == "zh-TW"

    @pytest.mark.parametrize(
        "text",
        [
            "我们这样写可以吗？",
            "请问简体中文的政策需要调整吗",
        ],
    )
    def test_simplified_chinese(self, app, text):
        assert app.detect_language(text) == "zh-CN"

    @pytest.mark.parametrize(
        "text",
        [
            "開発部門でDEI研修を開始したい",   # 有假名
            "公開前に確認してください",         # 有假名
            "ダイバーシティ研修について教えて",  # 片假名
        ],
    )
    def test_japanese(self, app, text):
        """迴歸測試：「開」是日文常用漢字，不能列入繁體標記。

        漢字比對若排在假名之前，這些句子會被判成 zh-TW。
        """
        assert app.detect_language(text) == "ja"

    def test_korean(self, app):
        assert app.detect_language("다양성 정책을 검토해 주세요") == "ko"

    def test_english(self, app):
        assert app.detect_language("Is this hiring notice compliant?") == "en"

    def test_han_only_defaults_to_traditional(self, app):
        """沒有假名也沒有繁簡特徵的漢字句子，預設繁體。"""
        assert app.detect_language("人事政策審查") == "zh-TW"


# ---------------------------------------------------------------------------
# build_api_messages
# ---------------------------------------------------------------------------

class TestBuildApiMessages:
    def test_system_prompt_is_first(self, app):
        result = app.build_api_messages([{"role": "user", "content": "你好"}], "SYS")
        assert result[0] == {"role": "system", "content": "SYS"}
        assert result[1] == {"role": "user", "content": "你好"}

    def test_trims_to_max_history_messages(self, app):
        messages = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"訊息{i}"}
            for i in range(30)
        ]
        result = app.build_api_messages(messages, "SYS")

        assert len(result) == app.MAX_HISTORY_MESSAGES + 1  # 再加上 system
        assert [m["content"] for m in result[1:]] == [
            f"訊息{i}" for i in range(30 - app.MAX_HISTORY_MESSAGES, 30)
        ]

    def test_drops_greeting(self, app):
        messages = [
            {"role": "assistant", "content": app.DEFAULT_ASSISTANT_MESSAGE},
            {"role": "user", "content": "請評估這份公告"},
        ]
        result = app.build_api_messages(messages, "SYS")

        assert len(result) == 2
        assert app.DEFAULT_ASSISTANT_MESSAGE not in [m["content"] for m in result]

    def test_drops_transient_messages(self, app):
        messages = [
            {"role": "user", "content": "第一個問題"},
            {"role": "assistant", "content": "⏱️ 呼叫太頻繁", "transient": True},
            {"role": "user", "content": "第二個問題"},
        ]
        result = app.build_api_messages(messages, "SYS")

        assert [m["content"] for m in result[1:]] == ["第一個問題", "第二個問題"]

    def test_drops_empty_messages(self, app):
        messages = [
            {"role": "assistant", "content": ""},
            {"role": "user", "content": "有內容"},
        ]
        result = app.build_api_messages(messages, "SYS")

        assert [m["content"] for m in result[1:]] == ["有內容"]

    def test_truncates_oversized_newest_message(self, app):
        """最新一則是使用者剛送出的內容，太長要截斷而不是丟掉。"""
        long_text = "政" * (app.MAX_HISTORY_CHARS + 500)
        result = app.build_api_messages([{"role": "user", "content": long_text}], "SYS")

        assert len(result) == 2
        sent = result[1]["content"]
        assert sent != long_text
        assert sent.startswith("政" * 100)
        assert len(sent) < len(long_text)
        assert sent[:app.MAX_HISTORY_CHARS] == long_text[:app.MAX_HISTORY_CHARS]
        assert "已截斷" in sent

    def test_stops_adding_older_messages_over_char_budget(self, app):
        """字元預算用完時，只捨棄較舊的訊息。"""
        chunk = "字" * (app.MAX_HISTORY_CHARS // 2 + 100)
        messages = [
            {"role": "user", "content": chunk + "最舊"},
            {"role": "assistant", "content": chunk + "中間"},
            {"role": "user", "content": chunk + "最新"},
        ]
        result = app.build_api_messages(messages, "SYS")

        assert len(result) == 2
        assert result[1]["content"].endswith("最新")


# ---------------------------------------------------------------------------
# available_models / request_stream 的冷卻行為
# ---------------------------------------------------------------------------

class TestCooldownBehaviour:
    def test_all_models_cooling_stops_further_api_calls(self, app):
        """迴歸測試：全部冷卻時不能再打 API。

        舊版在全部冷卻時退回完整模型清單，於是每次提問都重打一輪已限流的
        模型，而每個 429 又把冷卻往後推 90 秒，永遠無法恢復。
        """
        client = FakeGroqClient(lambda model: api_error(429, "Rate limit reached"))
        api_messages = [{"role": "system", "content": "SYS"}]

        # 第一輪：四個模型各被試一次，最後拋出原始的 429
        with pytest.raises(groq.APIStatusError):
            app.request_stream(client, api_messages)
        assert client.calls == app.MODEL_CHAIN

        # 第二輪：沒有可用模型，直接中止，不再打任何 API
        assert app.available_models() == []
        with pytest.raises(app.AllModelsCoolingError) as excinfo:
            app.request_stream(client, api_messages)
        assert client.calls == app.MODEL_CHAIN  # 呼叫次數沒有增加
        assert 0 < excinfo.value.seconds <= app.RATE_LIMIT_COOLDOWN

    def test_recovers_after_cooldown_expires(self, app, session_state):
        stream = object()
        client = FakeGroqClient(lambda model: stream)

        session_state["model_cooldowns"] = {m: time.time() - 1 for m in app.MODEL_CHAIN}

        assert app.available_models() == app.MODEL_CHAIN
        assert app.cooldown_seconds_left() == 0

        model, returned = app.request_stream(client, [{"role": "system", "content": "SYS"}])
        assert model == app.MODEL_CHAIN[0]
        assert returned is stream
        assert client.calls == [app.MODEL_CHAIN[0]]

    def test_skips_cooling_models_but_still_serves(self, app):
        """只有部分模型冷卻時，仍然要用剩下的模型回答。"""
        stream = object()
        client = FakeGroqClient(lambda model: stream)

        for model in app.MODEL_CHAIN[:2]:
            app.mark_model_unavailable(model, app.RATE_LIMIT_COOLDOWN)

        assert app.available_models() == app.MODEL_CHAIN[2:]

        model, _ = app.request_stream(client, [{"role": "system", "content": "SYS"}])
        assert model == app.MODEL_CHAIN[2]
        assert client.calls == [app.MODEL_CHAIN[2]]

    def test_falls_back_to_next_model_on_rate_limit(self, app):
        stream = object()

        def responder(model):
            if model == app.MODEL_CHAIN[0]:
                return api_error(429, "Rate limit reached. Used 11413")
            return stream

        client = FakeGroqClient(responder)

        model, returned = app.request_stream(client, [{"role": "system", "content": "SYS"}])

        assert model == app.MODEL_CHAIN[1]
        assert returned is stream
        assert client.calls == app.MODEL_CHAIN[:2]  # 429 之後不重試同一個模型
        assert app.MODEL_CHAIN[0] not in app.available_models()

    def test_too_large_aborts_without_trying_other_models(self, app):
        """輸入過長換模型也沒用，必須立刻中止。"""
        client = FakeGroqClient(lambda model: api_error(413, "Request too large"))

        with pytest.raises(groq.APIStatusError):
            app.request_stream(client, [{"role": "system", "content": "SYS"}])

        assert client.calls == [app.MODEL_CHAIN[0]]
        assert app.available_models() == app.MODEL_CHAIN  # 沒有被加上冷卻

    def test_model_gone_gets_long_cooldown(self, app, session_state):
        def responder(model):
            if model == app.MODEL_CHAIN[0]:
                return api_error(404, "The model does not exist")
            return object()

        client = FakeGroqClient(responder)
        model, _ = app.request_stream(client, [{"role": "system", "content": "SYS"}])

        assert model == app.MODEL_CHAIN[1]
        cooling_until = session_state["model_cooldowns"][app.MODEL_CHAIN[0]]
        assert cooling_until - time.time() > app.RATE_LIMIT_COOLDOWN


# ---------------------------------------------------------------------------
# iter_stream_text
# ---------------------------------------------------------------------------

class TestIterStreamText:
    def test_clean_finish_records_no_notice(self, app):
        stream = iter([
            make_chunk("這份公告"),
            make_chunk("沒有明顯風險。"),
            make_chunk(None, finish_reason="stop"),
        ])
        notice_state: dict = {}

        text = "".join(app.iter_stream_text(stream, notice_state))

        assert text == "這份公告沒有明顯風險。"
        assert notice_state == {}

    def test_ignores_chunks_without_choices(self, app):
        stream = iter([
            types.SimpleNamespace(choices=[]),
            make_chunk("內容"),
        ])
        assert "".join(app.iter_stream_text(stream, {})) == "內容"

    def test_mid_stream_error_keeps_partial_text_and_records_notice(self, app):
        """串流中斷時要保留已輸出的內容，並把提示記在 notice_state。

        提示不是模型的發言，呼叫端要靠 notice_state 把它從結尾切掉再存檔。
        """
        def exploding():
            yield make_chunk("風險評估：")
            yield make_chunk("第一項")
            raise RuntimeError("connection dropped mid-stream")

        notice_state: dict = {}
        text = "".join(app.iter_stream_text(exploding(), notice_state))

        notice = notice_state["notice"]
        assert "回覆中斷" in notice
        assert text.endswith(notice)
        assert text[: -len(notice)] == "風險評估：第一項"

    def test_length_finish_reason_appends_truncation_notice(self, app):
        stream = iter([
            make_chunk("很長的分析"),
            make_chunk(None, finish_reason="length"),
        ])
        notice_state: dict = {}

        text = "".join(app.iter_stream_text(stream, notice_state))

        notice = notice_state["notice"]
        assert "長度上限" in notice
        assert text == "很長的分析" + notice

    def test_works_without_notice_state(self, app):
        """呼叫端不需要提示時，傳 None 也不能出錯。"""
        def exploding():
            yield make_chunk("半句")
            raise RuntimeError("boom")

        text = "".join(app.iter_stream_text(exploding(), None))
        assert text.startswith("半句")
        assert "回覆中斷" in text
