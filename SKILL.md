---
name: majia-match-the-venue
description: Match The Venue（MTV）— 给国内城市的"高端培训/商学院/咨询/私董会"事件匹配最合适的酒店宴会厅，靠公开活动证据导航。喂活动链接（微信公众号/活动家/活动行/任意 URL）即可抽取"哪家机构 在 哪家酒店 办了什么课"，入库打分后输出选址推荐报告。当用户提到"找培训酒店"、"高管培训场地"、"会场推荐"、"宴会厅选址"、"培训选址"、"高端培训去哪开"、"match the venue"、"majia-match-the-venue"、"/mtv" 时触发。首发覆盖上海 6 个区（浦东/静安/黄浦/徐汇/长宁/闵行虹桥），跟踪 19 家高端机构（长江/中欧/得到/混沌/麦肯锡/贝恩/BCG/正和岛等）。不做酒店预订、不做询价撮合，只做"前人选址经验证据库"。
---

# majia-match-the-venue：高端培训选址证据导航

## 一句话定位

把"长江/中欧/得到/混沌/麦肯锡"们的公开选址记录，整理成一个可查询的证据库。
**不重造会场搜索（会小二/Cvent 已成熟），只做"前人选址经验"这一层。**

## 何时触发本 Skill

- 用户问 "找培训酒店"、"上海有哪些适合 100 人课桌式的酒店"、"高管培训场地"、"会场推荐"、"宴会厅"、"venue radar"
- 用户喂来一条公开活动链接（公众号回顾文 / 活动家 / 活动行）希望"记下来"或"加入库"
- 用户提到 `/mtv`、`majia-match-the-venue`、"match the venue"

## 三种工作流

### 1. 录入证据（ingest）

把任意公开活动 URL 转成一条 evidence。

```bash
python scripts/ingest.py "<URL>"
# 自动按域名分发：
#   mp.weixin.qq.com   → parsers/wechat.py
#   huodongjia.com     → parsers/huodongjia.py
#   huodongxing.com    → parsers/huodongxing.py
#   其他               → parsers/llm_fallback.py（defuddle 取正文 + LLM 抽四元组）
```

抽取目标字段：`org` / `venue` / `event_date` / `event_type` / `attendees` / `layout` / `photo_urls`。
默认进入 `evidence.jsonl`，需要人工 review 后置 `verified: true`。

### 2. 查询候选（query）

```bash
python scripts/query.py \
  --city 上海 \
  --district 浦东 \
  --layout classroom \
  --attendees 100 \
  --screen LED \
  --budget-day-max 80000 \
  --top 5
```

输出：按"培训适配分"倒序的酒店清单，每家附 2-5 条证据 + 来源链接。

### 3. 出推荐报告（report）

```bash
python scripts/report.py \
  --query "上海 100 人 课桌式 LED" \
  --top 5 \
  --out ~/Downloads/venue-report-2026-05.md
```

输出一份给业务/客户/老板看的 .md，含：推荐酒店、证据、价格区间、风险点（如柱子/层高/屏幕遮挡）。

## 数据三件套

| 文件 | 内容 |
|---|---|
| `data/venues.json` | 酒店主库（含官方硬数据：容量、层高、屏） |
| `data/orgs.json` | 观察机构清单（含公众号名、关键词、权重） |
| `data/evidence.jsonl` | 活动证据流水（一行一条） |

详细字段说明见 `references/data-schema.md`。

## 打分

每家酒店在每次 query 时根据匹配维度算"培训适配分"（满分 100）：

- 高端机构使用次数 30 分
- 课型权重（总裁班/战略营/私董会 ≥ 公开课） 20 分
- 现场照片证据齐全 15 分
- 屏幕/层高/无柱信息齐 15 分
- 价格区间清楚 10 分
- 被 ≥3 家机构选过加成 10 分

细则见 `references/scoring-rules.md`。

## 该做 & 不该做

✅ 做：把高端机构公开活动记录变成可查证据；按场景给候选；写选址报告
❌ 不做：酒店预订、询价撮合、销售返佣、自动批量爬取（始终保留人工 review 节点）

## 引用

- 数据 schema → `references/data-schema.md`
- 打分细则 → `references/scoring-rules.md`
- 观察机构清单 → `references/observed-orgs.md`
- 录入工作流（含去重、审核、版权） → `references/ingest-workflow.md`
