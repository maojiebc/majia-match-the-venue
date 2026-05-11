#!/usr/bin/env python3
"""score.py — 算 (酒店 × 查询) 的培训适配分。

可独立 CLI：
  python scripts/score.py --venue-id shanghai-jinganshangrila --layout classroom --attendees 100

也作为 query.py / report.py 的内部模块。
打分细则见 references/scoring-rules.md。
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import load_venues, load_orgs, load_evidence, find_venue, find_org


COURSE_TIER_MULTIPLIER = {"private": 1.0, "board": 1.0, "public": 0.7, "salon": 0.5}
CAP_ORG_USAGE = 30
CAP_LAYOUT_MATCH = 20
CAP_PHOTO = 15
CAP_HARDWARE = 15
CAP_PRICE = 10
CAP_MULTI_ORG = 10


def evidences_for_venue(venue_id: str, evidence: list[dict]) -> list[dict]:
    return [e for e in evidence if e.get("venue_id") == venue_id]


def best_room(venue: dict, query: dict) -> dict | None:
    """从 venue.rooms 里挑最符合 query 的厅。"""
    rooms = venue.get("rooms", [])
    if not rooms:
        return None
    n = query.get("attendees")
    layout = query.get("layout")
    if not n or not layout:
        return rooms[0]

    def fit_distance(room):
        cap = room.get("capacity", {}).get(layout)
        if cap is None or cap < n:
            return float("inf")
        return cap - n
    return min(rooms, key=fit_distance)


def score_org_usage(evs: list[dict], orgs: dict) -> float:
    s = 0.0
    for ev in evs:
        org = find_org(ev.get("org_id") or "", orgs)
        if not org:
            continue
        mult = COURSE_TIER_MULTIPLIER.get(ev.get("course_tier") or "private", 0.7)
        s += org["weight"] * mult
    return min(CAP_ORG_USAGE, s * 10)


def score_layout_match(evs: list[dict], query: dict) -> float:
    s = 0
    layout = query.get("layout")
    n = query.get("attendees")
    if layout and any(e.get("layout") == layout for e in evs):
        s += 10
    if n:
        for e in evs:
            ev_n = e.get("attendees")
            if ev_n and abs(ev_n - n) / n < 0.3:
                s += 10
                break
    return s


def score_photo(evs: list[dict]) -> float:
    n = sum(1 for e in evs if e.get("photo_urls"))
    return min(CAP_PHOTO, n * 5)


def score_hardware(room: dict | None) -> float:
    if not room:
        return 0
    s = 0
    screen = room.get("screen") or {}
    if screen.get("type") and screen["type"] != "none":
        s += 5
    ceiling = room.get("ceiling_m")
    if ceiling:
        if ceiling >= 7:
            s += 5
        elif ceiling >= 5:
            s += 3
    if room.get("pillar_free") is True:
        s += 3
    if screen.get("ground_clearance_m") is not None:
        s += 2
    return min(CAP_HARDWARE, s)


def score_price(room: dict | None) -> float:
    if not room:
        return 0
    p = room.get("price_range_cny") or {}
    keys = ["half_day", "full_day", "tea_break_per_pax", "lunch_per_pax"]
    filled = sum(1 for k in keys if p.get(k))
    return filled * 2.5


def score_multi_org(evs: list[dict]) -> float:
    unique = len({e.get("org_id") for e in evs if e.get("org_id")})
    return min(CAP_MULTI_ORG, max(0, (unique - 2)) * 5)


def score_venue(venue: dict, query: dict, evidence: list[dict] | None = None, orgs: dict | None = None) -> dict:
    evidence = evidence if evidence is not None else load_evidence()
    orgs = orgs or load_orgs()
    evs = evidences_for_venue(venue["id"], evidence)
    room = best_room(venue, query)

    breakdown = {
        "org_usage":             round(score_org_usage(evs, orgs), 2),
        "layout_match":          score_layout_match(evs, query),
        "photo_evidence":        score_photo(evs),
        "hardware_completeness": score_hardware(room),
        "price_clarity":         score_price(room),
        "multi_org_bonus":       score_multi_org(evs),
    }
    return {
        "venue_id": venue["id"],
        "venue_name": venue["name"],
        "room_name": room["name"] if room else None,
        "total_score": round(sum(breakdown.values()), 2),
        "breakdown": breakdown,
        "evidence_count": len(evs),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--venue-id", required=True)
    ap.add_argument("--city")
    ap.add_argument("--district")
    ap.add_argument("--layout", default="classroom")
    ap.add_argument("--attendees", type=int)
    ap.add_argument("--screen")
    args = ap.parse_args()

    venue = find_venue(args.venue_id)
    if not venue:
        print(f"未找到 venue_id: {args.venue_id}", file=sys.stderr)
        sys.exit(1)
    q = {k: v for k, v in vars(args).items() if v is not None and k != "venue_id"}
    print(json.dumps(score_venue(venue, q), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
