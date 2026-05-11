"""活动家 huodongjia.com parser。重点抽取"近期会议"反查信息。"""
from . import _common


SOURCE_TYPE = "huodongjia"
SOURCE_HINT = "活动家 huodongjia.com 活动/酒店页面（含活动名、酒店、人数、近期会议列表）"


def parse(url: str, text: str | None = None) -> dict:
    if text is None:
        text = _common.fetch_text(url)
    rec = _common.extract(text, SOURCE_HINT)
    rec.update({
        "source_url": url,
        "source_type": SOURCE_TYPE,
        "ingested_by": "parser-huodongjia",
    })
    return rec
