#!/usr/bin/env python3
"""ingest.py — 把 URL/正文/手填 转成一条 evidence 写入 data/evidence.jsonl

用法：
  python scripts/ingest.py <URL>                       # 自动分发 parser
  python scripts/ingest.py <URL> --text-file <path>    # 已 fetch 好的正文
  python scripts/ingest.py --manual                    # 手填
  python scripts/ingest.py <URL> --dry-run             # 只看抽取结果，不写入
"""
from __future__ import annotations
import argparse
import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import (
    append_evidence, next_evidence_id, load_orgs, load_venues,
    match_org, match_venue,
)
import parsers


def manual_input() -> dict:
    def q(label, default=None, cast=str):
        s = input(f"{label}{f' [{default}]' if default else ''}: ").strip()
        if not s:
            return default
        try:
            return cast(s) if cast is not str else s
        except ValueError:
            return default
    return {
        "org_name_raw":   q("主办机构"),
        "venue_name_raw": q("酒店名"),
        "room_name":      q("宴会厅名"),
        "event_name":     q("活动名"),
        "event_type":     q("活动类型 (training/salon/conference/private-board/release/other)", "training"),
        "course_tier":    q("课型 (public/private/board)", "private"),
        "event_date":     q("日期 (YYYY-MM-DD)"),
        "attendees":      q("人数", 0, int),
        "layout":         q("布局 (theater/classroom/round_table/u_shape/cocktail/unknown)", "classroom"),
        "source_url":     q("来源 URL", "manual://"),
        "source_type":    q("来源类型 (wechat/huodongjia/huodongxing/xhs/weibo/official/other)", "other"),
        "photo_urls":     [],
        "notes":          q("备注", ""),
        "ingested_by":    "manual",
    }


def postprocess(rec: dict) -> dict:
    """填补 id / verified / org_id / venue_id / ingested_at。"""
    orgs = load_orgs()
    venues = load_venues()
    if not rec.get("org_id"):
        rec["org_id"] = match_org(rec.get("org_name_raw"), orgs)
    if not rec.get("venue_id"):
        rec["venue_id"] = match_venue(rec.get("venue_name_raw"), venues)
    rec.setdefault("id", next_evidence_id())
    rec.setdefault("verified", False)
    rec.setdefault("verified_by", None)
    rec.setdefault("ingested_at", datetime.date.today().isoformat())
    rec.setdefault("event_type", "training")
    rec.setdefault("photo_urls", [])
    rec.setdefault("notes", "")
    return rec


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("url", nargs="?", help="活动 URL")
    ap.add_argument("--manual", action="store_true", help="手填")
    ap.add_argument("--text-file", help="已 fetch 好的正文（路径）")
    ap.add_argument("--dry-run", action="store_true", help="只打印不写入")
    args = ap.parse_args()

    if args.manual:
        rec = manual_input()
    elif args.url:
        text = None
        if args.text_file:
            text = Path(args.text_file).read_text(encoding="utf-8")
        parser = parsers.route(args.url)
        rec = parser.parse(args.url, text=text)
    else:
        ap.print_help()
        sys.exit(1)

    rec = postprocess(rec)

    print(json.dumps(rec, ensure_ascii=False, indent=2))

    warnings = []
    if not rec.get("org_id"):
        warnings.append(f"⚠ 机构未匹配（raw: {rec.get('org_name_raw')}）— 考虑加入 orgs.json 或人工指定 org_id")
    if not rec.get("venue_id"):
        warnings.append(f"⚠ 酒店未匹配（raw: {rec.get('venue_name_raw')}）— 考虑加入 venues.json 或加 alias")
    if not rec.get("event_date"):
        warnings.append("⚠ 日期缺失")
    for w in warnings:
        print(w, file=sys.stderr)

    if args.dry_run:
        print("\n(dry-run，未写入)", file=sys.stderr)
    else:
        append_evidence(rec)
        print(f"\n✓ 已 append 到 data/evidence.jsonl (id: {rec['id']})", file=sys.stderr)
        print(f"  verified=false，请人工 review 后改 verified=true", file=sys.stderr)


if __name__ == "__main__":
    main()
