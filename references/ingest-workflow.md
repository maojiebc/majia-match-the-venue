# Ingest Workflow

录入流程的完整规则。所有 evidence 必须经过这条流水线，**没有自动批量抓取**。

## 核心原则

| 原则 | 为什么 |
|---|---|
| 只录公开信息 | 公众号文章、活动家、活动行、酒店官网都是机构主动公开的内容 |
| 不存原图 | 只存 `photo_urls` 外链，避免版权问题 |
| 始终保留人工 review | 模板抽取 + LLM 兜底都可能错；`verified` 默认 false |
| Append-only | evidence.jsonl 只追加，修订用 `revises` 字段 |
| 透明可追溯 | 每条 evidence 必带 `source_url` |

## 四种入口

### A. 微信公众号（mp.weixin.qq.com）

```bash
python scripts/ingest.py "https://mp.weixin.qq.com/s/xxx"
```

分发到 `parsers/wechat.py`，内部复用 [wechat-article-extractor](../) skill 抽出标题/正文/封面/发布时间，再做四元组抽取。

适合：培训机构的"活动回顾"、"开学典礼"、"结业典礼"文章。

### B. 活动家（huodongjia.com）

```bash
python scripts/ingest.py "https://www.huodongjia.com/event-xxx/"
```

活动家的酒店反查页（每家酒店列出"近期举行的会议"）是高价值入口。

### C. 活动行（huodongxing.com）

```bash
python scripts/ingest.py "https://www.huodongxing.com/event/xxx"
```

活动行的报名页通常包含详细的场地名、容量、时间，价格信息也偶有公开。

### D. LLM 兜底（任意 URL）

```bash
python scripts/ingest.py "https://xhslink.com/xxx"
```

分发到 `parsers/llm_fallback.py`：
1. 用 defuddle 取正文
2. 喂 LLM，请求结构化输出 `{org, venue, room, event_date, attendees, layout}`
3. 输出存到 evidence.jsonl，标 `ingested_by: parser-llm` 和 `verified: false`

适合：小红书、微博、酒店官网、第三方报道。

## 抽取后的四步审核

每条新 evidence 默认 `verified: false`。审核流程：

### Step 1 — 机构匹配

抽取出的"主办机构"文本 → 用 `orgs.json[].keywords` 模糊匹配 → 写入 `org_id`。
匹配失败 → 留 `org_id: null` + `notes: "未匹配到观察机构"`，等待人工判断是否要新增机构到 orgs.json。

### Step 2 — 酒店匹配

抽取出的"酒店名"文本 → 用 `venues.json[].name` + 自定义别名表模糊匹配 → 写入 `venue_id`。
匹配失败 → 留 `venue_id: null`、`venue_name_raw: "<原文>"`，等待决定：
- 是新酒店？→ 在 venues.json 加 record
- 是已有酒店的别名？→ 在 venues.json 加 `aliases` 字段

### Step 3 — 字段补全

LLM 抽取的 `attendees` / `layout` / `event_date` 可能不准。人工检查后修订。

### Step 4 — 置 verified=true

`verified: true` + `verified_by: "<你的 github handle>"` + `verified_at: <date>`。

## 去重

新 evidence 进入前先查：

```
exists if all match:
  - same event_date
  - same org_id
  - same venue_id
  - room_name 相似度 >0.8
```

命中则 skip，并在已有 record 的 `notes` 里 append `"另见 source: <new_url>"`。

## 数据治理（每月 1 次）

```bash
# 跑全量校验
python scripts/validate.py

# 跑去重
python scripts/dedupe.py --dry-run

# 重算所有酒店在通用 query 下的快照分
python scripts/score.py --recompute-snapshot
```

把跑出来的报告 PR 提交，让其他贡献者复核。

## 版权与合规

- 只引用 `source_url`，不复制粘贴文章原文
- `photo_urls` 只存外链，不下载图片到仓库
- 抽取出的"价格区间"标 `note: 估算区间，实际以销售报价为准`
- 收到酒店/机构的删除请求 → 立即把对应 evidence 的 `redacted: true`，保留行但隐藏字段

## 触发 ingest 的几种自然场景

- 看到一篇培训机构的"活动回顾"文章 → 喂 URL
- 在活动家上随手翻到一家酒店的"近期会议"列表 → 逐条喂
- 朋友发来一条小红书链接 → 喂 URL（走 LLM 兜底）
- 自己参加完一个活动 → 手填一条（用 `scripts/ingest.py --manual`）

## 不该做的事

- ❌ 写爬虫定时跑全网抓取
- ❌ 把抓到的现场照片下载到仓库
- ❌ 把酒店销售报价单原文 commit 到仓库
- ❌ 录入未公开的内部活动（即使你知道）
