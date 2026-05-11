# majia-match-the-venue

> **Match The Venue（MTV）** — 给"高端培训/商学院/咨询/私董会"事件匹配最合适的酒店宴会厅。
> 跟着长江、中欧、得到、混沌、麦肯锡的脚步选会场。

## 它解决什么问题

**会场搜索这件事**，会小二、Cvent、VenueHub 已经做得很成熟。
但有一层东西它们没做：

> **"哪些高端培训机构、商学院、咨询公司、私董会，反复在哪些酒店宴会厅办课？"**

这一层才是真正有价值的"选址经验"。
价格上万的总裁班选场地基本不会错——他们已经踩过坑了。

majia-match-the-venue 把这层经验做成可查询资产。

## 它做什么

1. **抓证据**：喂任意公开活动链接（公众号回顾文 / 活动家 / 活动行 / 酒店官网） → 自动抽出"机构 × 酒店 × 时间 × 课型"
2. **入库**：写入本地 `evidence.jsonl`，人工 review 后入主库
3. **查询**：按城市/区/人数/课型/预算/屏类型筛酒店
4. **打分**：算"培训适配分"（满分 100，规则透明）
5. **报告**：出选址推荐 .md，可直接发给客户/老板/业务方

## 不做什么

- 不做酒店预订
- 不做询价撮合
- 不做销售返佣
- 不做自动批量爬取（始终保留人工 review 节点，避免侵犯版权和反爬）

## 首发范围（v0.1）

- 城市：**上海**
- 区：浦东（6）、静安（5）、黄浦（7）、徐汇（3）、长宁（4）、闵行/虹桥（5）
- 观察机构：**19 家**（5 商学院 + 6 高端培训 + 4 战略咨询 + 2 私董会 + 2 培训承接）
- 种子酒店：**30 家**（覆盖 4 万–28 万/天宴会厅档位 · luxury 14 + upper-upscale 12 + upscale 4）
- 活动证据：0 条（v0.1 待录入；通过 `python scripts/ingest.py <URL>` 增量积累）

> 种子数据的硬件/价格字段默认 `verified: false`，需要使用者通过询价或现场踏勘校准。

后续会按需扩到北京、深圳、杭州。

## 安装

```bash
# 作为 Claude Code / Codex skill
git clone https://github.com/maojiebc/majia-match-the-venue.git ~/.agents/skills/majia-match-the-venue
# 或
git clone https://github.com/maojiebc/majia-match-the-venue.git ~/.codex/skills/majia-match-the-venue
```

也可以直接 clone 到任意目录当独立 Python 工具用。

## 三步快速试用

```bash
# 1. 录入一条公开活动证据
python scripts/ingest.py "https://mp.weixin.qq.com/s/xxx"

# 2. 查上海浦东 100 人课桌式候选
python scripts/query.py --city 上海 --district 浦东 --layout classroom --attendees 100 --top 5

# 3. 出推荐报告
python scripts/report.py --query "上海 100 人 课桌式 LED" --top 5 --out report.md
```

## 数据结构

三件套，全是人类可读 JSON：

- `data/venues.json` — 酒店主库
- `data/orgs.json` — 观察机构清单
- `data/evidence.jsonl` — 活动证据流水

详细 schema 见 [references/data-schema.md](references/data-schema.md)。

## 贡献

欢迎 PR 补充：
- 新城市种子酒店
- 新观察机构
- 新公开活动证据
- 新 parser 模板（小红书/视频号/B站活动账号 等）

录入流程见 [references/ingest-workflow.md](references/ingest-workflow.md)。

## 联系

- 公众号：超级马甲
- 小红书：https://xhslink.com/m/4fQMJeHHWKC
- X / Twitter：https://x.com/maojiebc
- GitHub：https://github.com/maojiebc
- Email：majia9224@gmail.com

## License

MIT
