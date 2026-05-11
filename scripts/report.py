#!/usr/bin/env python3
"""report.py — 把 query 结果渲染成可发给客户/老板的 markdown 报告。

用法：
  python scripts/report.py --city 上海 --district 浦东 --layout classroom --attendees 100 --top 5
  python scripts/report.py --city 上海 --top 10 --out ~/Downloads/venue-report-2026-05.md
"""
from __future__ import annotations
import argparse
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import load_evidence, find_venue, find_org
from query import run_query


SCORE_LABEL = [
    (80, "🟢 强烈推荐"),
    (60, "🟡 推荐"),
    (40, "🟠 候补"),
    (0,  "🔴 不建议"),
]


def label_for(score: float) -> str:
    for threshold, label in SCORE_LABEL:
        if score >= threshold:
            return label
    return "🔴 不建议"


def render(results: list[dict], query: dict) -> str:
    today = datetime.date.today().isoformat()
    cond = " / ".join(f"{k}={v}" for k, v in query.items() if v is not None)

    lines = [
        "# 高端培训选址推荐报告",
        "",
        f"> 生成于 {today} · majia-match-the-venue v0.1",
        f"> 查询条件：{cond if cond else '（无）'}",
        "",
        "## 摘要",
        "",
        f'匹配候选 **{len(results)}** 家，按"培训适配分"倒序。',
        "分数由 6 个维度合成（机构使用 / 课型匹配 / 现场照片 / 硬件完整度 / 价格清晰度 / 跨机构加成），细则见 `references/scoring-rules.md`。",
        "",
    ]

    if not results:
        lines.append("（没有匹配的酒店。建议放宽筛选条件，或先 ingest 更多种子数据。）")
        return "\n".join(lines)

    lines.append("## 推荐清单")
    lines.append("")

    evidence = load_evidence()

    for r in results:
        venue = find_venue(r["venue_id"])
        if not venue:
            continue
        lines.append(f"### #{r['rank']} · {r['venue_name']}  {label_for(r['total_score'])}")
        lines.append("")
        lines.append(f"- **综合分**：{r['total_score']} / 100")
        lines.append(f"- **位置**：{venue.get('city','')} {venue.get('district','')} · {venue.get('address','')}")
        if r["room_name"]:
            lines.append(f"- **推荐厅**：{r['room_name']}")
            room = next((rm for rm in venue.get("rooms", []) if rm["name"] == r["room_name"]), None)
            if room:
                cap = room.get("capacity") or {}
                cap_str = "、".join(f"{k} {v}" for k, v in cap.items() if v)
                lines.append(f"- **容量**：{cap_str}")
                screen = room.get("screen") or {}
                if screen:
                    ceiling_str = f"{room['ceiling_m']}m" if room.get("ceiling_m") else "未知"
                    pillar_str = "是" if room.get("pillar_free") is True else ("否" if room.get("pillar_free") is False else "未知")
                    lines.append(f"- **屏幕**：{screen.get('type','?')} · 层高 {ceiling_str} · 无柱：{pillar_str}")
                price = room.get("price_range_cny") or {}
                if price.get("full_day"):
                    lines.append(f"- **场租（全天）**：¥{price['full_day'][0]:,}–¥{price['full_day'][1]:,}")
        if venue.get("official_source"):
            lines.append(f"- **官方信息**：{venue['official_source']}")
        lines.append("")

        # 分数拆分
        b = r["breakdown"]
        lines.append(
            f"**分数拆分**：机构使用 {b['org_usage']} · 课型匹配 {b['layout_match']} · "
            f"现场照片 {b['photo_evidence']} · 硬件 {b['hardware_completeness']} · "
            f"价格 {b['price_clarity']} · 跨机构加成 {b['multi_org_bonus']}"
        )
        lines.append("")

        # 证据
        evs = [e for e in evidence if e.get("venue_id") == r["venue_id"]]
        if evs:
            lines.append(f"**证据（{len(evs)} 条）**：")
            for e in evs[:5]:
                org = find_org(e.get("org_id") or "")
                org_name = org["name"] if org else (e.get("org_name_raw") or "未知机构")
                tier_label = {"private": "内训", "board": "私董", "public": "公开课", "salon": "沙龙"}.get(e.get("course_tier"), "")
                lines.append(
                    f"- {e.get('event_date','')} · **{org_name}** · {tier_label} · "
                    f"{e.get('event_name','')}（{e.get('attendees','?')} 人 · {e.get('layout','?')}）— "
                    f"[来源]({e.get('source_url','')})"
                )
            if len(evs) > 5:
                lines.append(f"- ... 另有 {len(evs)-5} 条证据")
        else:
            lines.append("**证据**：暂无（硬件信息为主要依据）")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## 使用说明")
    lines.append("")
    lines.append("- 本报告基于公开活动证据自动生成，价格区间为估算，**实际以销售报价为准**。")
    lines.append("- 建议在敲定前向酒店宴会部确认主屏离地高度、层高、柱位情况。")
    lines.append("- 数据更新或新证据补充：`python scripts/ingest.py <URL>` 后重跑本命令。")
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--city")
    ap.add_argument("--district")
    ap.add_argument("--layout", choices=["theater", "classroom", "round_table", "u_shape", "cocktail"])
    ap.add_argument("--attendees", type=int)
    ap.add_argument("--screen")
    ap.add_argument("--budget-day-max", type=int, dest="budget_day_max")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--out", help="输出文件路径；不指定则打印到 stdout")
    args = ap.parse_args()

    query = {k: v for k, v in vars(args).items()
             if v is not None and k not in ("top", "out")}
    results = run_query(query, top=args.top)
    md = render(results, query)

    if args.out:
        Path(args.out).expanduser().write_text(md, encoding="utf-8")
        print(f"✓ 报告写入 {args.out}", file=sys.stderr)
    else:
        print(md)


if __name__ == "__main__":
    main()
