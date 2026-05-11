"""共享数据 IO + 模糊匹配。"""
from __future__ import annotations
import json
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def load_venues() -> dict:
    return json.load(open(DATA / "venues.json", encoding="utf-8"))


def load_orgs() -> dict:
    return json.load(open(DATA / "orgs.json", encoding="utf-8"))


def load_evidence() -> list[dict]:
    path = DATA / "evidence.jsonl"
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("//"):
            out.append(json.loads(line))
    return out


def append_evidence(rec: dict) -> None:
    with open(DATA / "evidence.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def next_evidence_id() -> str:
    today = datetime.date.today().strftime("%Y%m%d")
    existing = [e for e in load_evidence() if e.get("id", "").startswith(f"ev-{today}-")]
    return f"ev-{today}-{len(existing) + 1:03d}"


def match_org(name_raw: str | None, orgs: dict | None = None) -> str | None:
    """按 keywords 模糊匹配机构名 → org_id。"""
    if not name_raw:
        return None
    orgs = orgs or load_orgs()
    text = name_raw.lower()
    for org in orgs["orgs"]:
        for kw in org["keywords"]:
            if kw.lower() in text:
                return org["id"]
    return None


def match_venue(name_raw: str | None, venues: dict | None = None) -> str | None:
    """按酒店主名 + aliases 模糊匹配 → venue_id。"""
    if not name_raw:
        return None
    venues = venues or load_venues()
    text = name_raw.lower()
    for v in venues["venues"]:
        if v["name"].lower() in text or text in v["name"].lower():
            return v["id"]
        for alias in v.get("aliases", []):
            if alias.lower() in text:
                return v["id"]
    return None


def find_venue(venue_id: str, venues: dict | None = None) -> dict | None:
    venues = venues or load_venues()
    for v in venues["venues"]:
        if v["id"] == venue_id:
            return v
    return None


def find_org(org_id: str, orgs: dict | None = None) -> dict | None:
    orgs = orgs or load_orgs()
    for o in orgs["orgs"]:
        if o["id"] == org_id:
            return o
    return None
