"""活动行 huodongxing.com parser。报名页常带场地名、人数、价格。"""
from . import _common


SOURCE_TYPE = "huodongxing"
SOURCE_HINT = "活动行 huodongxing.com 报名页（含活动名、举办场地、人数、可能含费用）"


def parse(url: str, text: str | None = None) -> dict:
    if text is None:
        text = _common.fetch_text(url)
    rec = _common.extract(text, SOURCE_HINT)
    rec.update({
        "source_url": url,
        "source_type": SOURCE_TYPE,
        "ingested_by": "parser-huodongxing",
    })
    return rec
