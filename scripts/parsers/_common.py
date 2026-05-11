"""共享：取正文 + LLM 抽四元组 + 规则兜底。

设计原则：fetch 链路尽量软依赖，缺失时清晰报错并提示用户用其他 skill 先取文本。
"""
from __future__ import annotations
import json
import os
import re
import subprocess


FIELDS = {
    "org_name_raw": "主办机构原文",
    "venue_name_raw": "酒店原文",
    "room_name": "宴会厅名",
    "event_name": "活动名",
    "event_date": "YYYY-MM-DD",
    "attendees": "数字或null",
    "layout": "theater|classroom|round_table|u_shape|cocktail|unknown",
    "course_tier": "public|private|board",
}


def extract_prompt(text: str, source_hint: str) -> str:
    schema = "\n".join(f'  "{k}": "{v}"' for k, v in FIELDS.items())
    return f"""从下面的{source_hint}文本里抽出一条"高端培训/咨询/商学院/私董会"活动的证据。
返回严格的 JSON 对象，字段：
{{
{schema}
}}
- 缺失的字段填 null。
- attendees 是整数。
- 不要输出多余的解释，只输出 JSON。

文本：
\"\"\"
{text[:6000]}
\"\"\"
"""


def fetch_text(url: str) -> str:
    """优先 defuddle，回退 curl。失败返回空串。"""
    # 优先：defuddle CLI（用户的 defuddle skill 提供 npx 包装）
    for cmd in (
        ["npx", "-y", "@etodd/defuddle-cli", url, "--md"],
        ["defuddle", url, "--md"],
    ):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    # 兜底 curl
    try:
        r = subprocess.run(
            ["curl", "-sL", "-A", "Mozilla/5.0", url],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode == 0:
            return r.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return ""


def extract_with_claude(text: str, source_hint: str) -> dict | None:
    """用 Claude Haiku 抽四元组。需要 ANTHROPIC_API_KEY。失败返回 None。"""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
    except ImportError:
        return None
    try:
        client = anthropic.Anthropic()
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": extract_prompt(text, source_hint)}],
        )
        body = resp.content[0].text
        m = re.search(r"\{[\s\S]*\}", body)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        print(f"⚠ Claude 抽取失败: {e}")
    return None


VENUE_BRAND_HINTS = [
    "香格里拉", "柏悦", "君悦", "丽思卡尔顿", "半岛", "JW万豪", "万豪",
    "威斯汀", "凯悦", "希尔顿", "金茂", "文华东方", "璞丽", "璞麗",
    "阿纳迪", "建国", "朗廷", "锦江", "和平饭店", "国际饭店", "外滩茂悦",
    "宝格丽", "瑞吉", "四季", "华尔道夫", "费尔蒙",
]


def _load_org_keywords() -> list[tuple[str, str]]:
    """读 orgs.json，返回 [(keyword, display_name), ...]，长 keyword 优先。"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from _lib import load_orgs
    pairs = []
    for org in load_orgs()["orgs"]:
        for kw in org["keywords"]:
            pairs.append((kw, org["name"]))
    pairs.sort(key=lambda p: -len(p[0]))
    return pairs


def rule_extract(text: str) -> dict:
    """规则兜底：正则 + 关键词。"""
    out: dict = {k: None for k in FIELDS}
    out["layout"] = "unknown"
    # 日期
    m = re.search(r"(\d{4})[\-/年\.](\d{1,2})[\-/月\.](\d{1,2})", text)
    if m:
        out["event_date"] = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    # 酒店
    for hint in VENUE_BRAND_HINTS:
        m = re.search(r"([^\s，。、,\n]{0,20}" + hint + r"[^\s，。、,\n]{0,20})", text)
        if m:
            out["venue_name_raw"] = m.group(1).strip()
            break
    # 机构（反扫 orgs.json keywords）
    try:
        for kw, name in _load_org_keywords():
            if kw.lower() in text.lower():
                out["org_name_raw"] = name
                break
    except Exception:
        pass
    # 人数
    m = re.search(r"(\d{2,4})\s*(?:位|名|人|学员|嘉宾|学友)", text)
    if m:
        out["attendees"] = int(m.group(1))
    # 课型
    if any(k in text for k in ["私董会", "私享会", "闭门"]):
        out["course_tier"] = "board"
    elif any(k in text for k in ["公开课", "开放报名", "招生"]):
        out["course_tier"] = "public"
    else:
        out["course_tier"] = "private"
    # 布局
    if "课桌式" in text or "classroom" in text.lower():
        out["layout"] = "classroom"
    elif "剧院式" in text or "theater" in text.lower():
        out["layout"] = "theater"
    elif "圆桌" in text:
        out["layout"] = "round_table"
    return out


def extract(text: str, source_hint: str = "通用") -> dict:
    """主入口：优先 Claude，回退规则。"""
    rec = extract_with_claude(text, source_hint)
    if rec:
        return rec
    return rule_extract(text)
