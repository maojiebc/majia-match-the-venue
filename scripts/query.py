#!/usr/bin/env python3
"""query.py — 按条件筛酒店并按培训适配分倒序排。

用法：
  python scripts/query.py --city 上海 --district 浦东 --layout classroom --attendees 100 --top 5
  python scripts/query.py --city 上海 --screen LED --budget-day-max 80000 --top 10
  python scripts/query.py --city 上海 --json    # 输出 JSON

筛选维度：
  --city        城市（精确）
  --district    区（精确）
  --layout      theater | classroom | round_table | u_shape | cocktail
  --attendees   人数（按 layout 对应的 capacity 过滤）
  --screen      LED | projector | LED+projector
  --budget-day-max  全天场租上限（CNY）
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import load_venues, load_orgs, load_evidence
from score import score_venue, best_room


def venue_matches(venue: dict, query: dict) -> bool:
    if query.get("city") and venue.get("city") != query["city"]:
        return False
    if query.get("district") and venue.get("district") != query["district"]:
        return False

    layout = query.get("layout")
    n = query.get("attendees")
    screen_want = query.get("screen")
    budget = query.get("budget_day_max")

    # 至少一个 room 满足所有硬约束
    for room in venue.get("rooms", []):
        if n and layout:
            cap = (room.get("capacity") or {}).get(layout)
            if cap is None or cap < n:
                continue
        if screen_want:
            stype = ((room.get("screen") or {}).get("type") or "").lower()
            if screen_want.lower() not in stype:
                continue
        if budget:
            full_day = (room.get("price_range_cny") or {}).get("full_day")
            if full_day and full_day[0] > budget:
                continue
        return True
    return False


def run_query(query: dict, top: int = 5) -> list[dict]:
    venues = load_venues()["venues"]
    orgs = load_orgs()
    evidence = load_evidence()
    candidates = [v for v in venues if venue_matches(v, query)]
    scored = [score_venue(v, query, evidence, orgs) for v in candidates]
    scored.sort(key=lambda x: x["total_score"], reverse=True)
    out = []
    for i, s in enumerate(scored[:top], start=1):
        s["rank"] = i
        out.append(s)
    return out


def format_text(results: list[dict], query: dict) -> str:
    if not results:
        return "（没有匹配的酒店；尝试放宽筛选条件或先 ingest 更多种子数据）"
    lines = []
    cond = " / ".join(f"{k}={v}" for k, v in query.items() if v is not None)
    lines.append(f"查询条件：{cond}")
    lines.append(f"匹配 {len(results)} 家，按培训适配分倒序：\n")
    for r in results:
        lines.append(f"#{r['rank']}  {r['venue_name']}  —  {r['total_score']}/100  ({r['evidence_count']} 条证据)")
        if r["room_name"]:
            lines.append(f"     推荐厅：{r['room_name']}")
        b = r["breakdown"]
        lines.append(
            f"     拆分：org {b['org_usage']} / layout {b['layout_match']} / "
            f"photo {b['photo_evidence']} / hw {b['hardware_completeness']} / "
            f"price {b['price_clarity']} / multi {b['multi_org_bonus']}"
        )
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
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    query = {k: v for k, v in vars(args).items()
             if v is not None and k not in ("top", "json")}
    results = run_query(query, top=args.top)

    if args.json:
        print(json.dumps({"query": query, "results": results}, ensure_ascii=False, indent=2))
    else:
        print(format_text(results, query))


if __name__ == "__main__":
    main()
