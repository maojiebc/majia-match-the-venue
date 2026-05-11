# majia-match-the-venue

> **Match The Venue (MTV)** — matches Chinese executive-training / business-school / consulting / private-board events to the right hotel ballroom.
> Follow the venue choices of CKGSB, CEIBS, Dedao, Hundun, McKinsey & friends.

> 🇨🇳 Chinese readers: see [README.md](./README.md) for the full Chinese documentation.

## The problem this solves

**Venue search as a feature** is already a solved problem — Hui Xiao Er, Cvent, VenueHub handle it well. But there's one layer they don't cover:

> **"Which executive-training providers, business schools, consultancies, and private-board groups *repeatedly* host classes in which hotel ballrooms?"**

That layer is what real-world venue picking is built on. A 10K+ RMB-per-seat executive program isn't going to pick a bad room — they've already paid for the lesson.

`majia-match-the-venue` turns that hard-won knowledge into a queryable asset.

## What it does

1. **Capture evidence**: feed any public event URL (WeChat OA post-event recap / Huodongjia / Huodongxing / hotel landing page) → automatically extract "Org × Hotel × Date × Course type".
2. **Ingest**: writes a row into local `evidence.jsonl`; after manual review, the row is merged into the main store.
3. **Query**: filter venues by city / district / capacity / layout / budget / display-screen type.
4. **Score**: computes a "training fitness score" (0–100, transparent rules).
5. **Report**: emits a venue recommendation `.md`, ready to send to a client / boss / business owner.

## What it does *not* do

- No hotel booking.
- No quote brokering.
- No referral commissions.
- No automated mass scraping (we always keep a human-review checkpoint to respect copyright and avoid anti-bot pushback).

## v0.1 launch coverage

- City: **Shanghai**
- Districts: Pudong (6 venues), Jing'an (5), Huangpu (7), Xuhui (3), Changning (4), Minhang / Hongqiao (5)
- Observed orgs: **19** (5 business schools + 6 exec-training providers + 4 strategy consultancies + 2 private boards + 2 training operators)
- Seed venues: **30** (covering the 40K–280K RMB/day ballroom tier · 14 luxury + 12 upper-upscale + 4 upscale)
- Event evidence: 0 entries (v0.1 starts empty; grow incrementally via `python scripts/ingest.py <URL>`)

> Seed-data hardware / pricing fields default to `verified: false` — calibrate by phoning the venue or doing a site visit.

Beijing / Shenzhen / Hangzhou coverage will be added on demand.

## Install

```bash
# As a Claude Code / Codex skill
git clone https://github.com/maojiebc/majia-match-the-venue.git ~/.agents/skills/majia-match-the-venue
# Or
git clone https://github.com/maojiebc/majia-match-the-venue.git ~/.codex/skills/majia-match-the-venue
```

You can also clone into any directory and use it as a standalone Python tool.

## Three-step quick tour

```bash
# 1. Ingest a single public event
python scripts/ingest.py "https://mp.weixin.qq.com/s/xxx"

# 2. Query Shanghai Pudong, 100-pax classroom layout
python scripts/query.py --city 上海 --district 浦东 --layout classroom --attendees 100 --top 5

# 3. Emit a recommendation report
python scripts/report.py --query "上海 100 人 课桌式 LED" --top 5 --out report.md
```

## Data layout

Three human-readable JSON files:

- `data/venues.json` — main venue store.
- `data/orgs.json` — observed-org roster.
- `data/evidence.jsonl` — event-evidence stream.

Full schema in [references/data-schema.md](references/data-schema.md).

## Contributing

PRs welcome for:

- Seed venues in new cities.
- New observed orgs.
- New public event evidence.
- New parser templates (Xiaohongshu / Video Account / Bilibili event accounts, etc.).

Ingestion workflow: see [references/ingest-workflow.md](references/ingest-workflow.md).

## 👤 Author / Contact

**Majia (@maojiebc)** · 超级马甲 (Super Majia)

If this skill helps you, find me on any of these channels — happy to chat about field experience, take feature requests, hear bug reports, or trade notes on user operations / data platforms / BI engineering work:

| Channel | Link |
|---|---|
| 📧 Email | [m9224@163.com](mailto:m9224@163.com) |
| 🐙 GitHub | [github.com/maojiebc](https://github.com/maojiebc) |
| 🪝 ClawHub | [clawhub.ai/p/maojiebc](https://clawhub.ai/p/maojiebc) |
| 🐦 X | [@maojiebc](https://x.com/maojiebc) |
| 📕 Xiaohongshu | [Super Majia](https://xhslink.com/m/4fQMJeHHWKC) |
| 📰 WeChat Official Account | **超级马甲** |

> Built from 14 years of user-operations work and on-the-ground venue scouting.

## License

MIT
