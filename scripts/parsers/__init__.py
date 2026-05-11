"""Parser registry. 按 hostname 分发到对应模块。"""
from urllib.parse import urlparse
from . import wechat, huodongjia, huodongxing, llm_fallback

ROUTES = {
    "mp.weixin.qq.com":     wechat,
    "huodongjia.com":       huodongjia,
    "www.huodongjia.com":   huodongjia,
    "huodongxing.com":      huodongxing,
    "www.huodongxing.com":  huodongxing,
}


def route(url: str):
    host = (urlparse(url).hostname or "").lower()
    return ROUTES.get(host, llm_fallback)


__all__ = ["wechat", "huodongjia", "huodongxing", "llm_fallback", "route"]
