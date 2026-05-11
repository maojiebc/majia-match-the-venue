"""LLM 兜底 parser：任意 URL（小红书、微博、酒店官网、第三方报道）。"""
from . import _common


SOURCE_TYPE = "other"
SOURCE_HINT = "任意网页正文（培训/咨询/商学院/私董会活动）"


def parse(url: str, text: str | None = None) -> dict:
    if text is None:
        text = _common.fetch_text(url)
    rec = _common.extract(text, SOURCE_HINT)
    src_type = SOURCE_TYPE
    if "xiaohongshu" in url or "xhslink" in url:
        src_type = "xhs"
    elif "weibo.com" in url:
        src_type = "weibo"
    rec.update({
        "source_url": url,
        "source_type": src_type,
        "ingested_by": "parser-llm",
    })
    return rec


def parse_text(text: str, url: str = "manual://") -> dict:
    rec = _common.extract(text, SOURCE_HINT)
    rec.update({
        "source_url": url,
        "source_type": SOURCE_TYPE,
        "ingested_by": "parser-llm",
    })
    return rec
