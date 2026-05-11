"""微信公众号文章 parser。"""
from . import _common


SOURCE_TYPE = "wechat"
SOURCE_HINT = "微信公众号文章（mp.weixin.qq.com 培训机构活动回顾/招生/开学/结业）"


def parse(url: str, text: str | None = None) -> dict:
    if text is None:
        text = _common.fetch_text(url)
    rec = _common.extract(text, SOURCE_HINT)
    rec.update({
        "source_url": url,
        "source_type": SOURCE_TYPE,
        "ingested_by": "parser-wechat",
    })
    return rec
