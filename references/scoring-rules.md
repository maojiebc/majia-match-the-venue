# 培训适配分 Scoring Rules

每次 query 时，给每家酒店在该 query 下算一个分（满分 100）。

**核心理念**：分数不是酒店的内在属性，而是 **(酒店 × 查询条件)** 的匹配度。同一家酒店在"100 人课桌式 LED"和"300 人剧院式发布会"两个 query 下分数会不同。

## 维度与配分

| # | 维度 | 满分 | 计分规则 |
|---|---|---|---|
| 1 | 高端机构使用 | 30 | 看 `evidence` 里命中观察机构的条数 + 机构 tier 权重 |
| 2 | 课型匹配 | 20 | 用户查询的 layout/attendees 是否被证据覆盖过 |
| 3 | 现场照片证据 | 15 | 有 photo_urls 的 evidence 数量 |
| 4 | 硬件信息完整度 | 15 | room 的 screen / ceiling / pillar 字段是否齐 |
| 5 | 价格区间清晰度 | 10 | price_range_cny 字段是否填全（半天+全天+茶歇+午餐） |
| 6 | 跨机构使用加成 | 10 | 同一酒店是否被 ≥3 个不同 org 选过 |

## 详细公式

### 1. 高端机构使用（30 分）

```
score_1 = min(30, sum(org.weight × course_tier_multiplier for ev in evidence))
```

`course_tier_multiplier`：
- `private`（内训/闭门）→ 1.0
- `board`（私董会）→ 1.0
- `public`（公开课）→ 0.7
- `salon`（沙龙）→ 0.5

例：长江商学院（weight=1.0）私董会 + 得到（1.0）内训 + 混沌（0.95）公开课 = 1.0 + 1.0 + 0.95×0.7 = **2.665** → ×10 截顶 = **26.65** 分

### 2. 课型匹配（20 分）

```
if query.layout in [ev.layout for ev in evidence]: +10
if |query.attendees - any(ev.attendees)| / query.attendees < 0.3: +10
```

### 3. 现场照片证据（15 分）

```
score_3 = min(15, count(ev with photo_urls) × 5)
```

### 4. 硬件信息完整度（15 分）

针对查询条件命中的那个 `room`：

- `screen.type` 非 none → +5
- `ceiling_m` ≥ 5 → +3，≥ 7 → +5（总分 5 上限）
- `pillar_free == true` → +3
- `screen.ground_clearance_m` 不为 null → +2

### 5. 价格区间清晰度（10 分）

`price_range_cny` 四个字段（half_day / full_day / tea_break / lunch）每填一个 +2.5。

### 6. 跨机构使用加成（10 分）

```
unique_orgs = len(set(ev.org_id for ev in evidence))
score_6 = min(10, max(0, (unique_orgs - 2)) × 5)
```

3 个机构 +5，4 个机构 +10。

## 输出

query.py 返回每家酒店时附带：

```json
{
  "venue_id": "...",
  "total_score": 78,
  "breakdown": {
    "org_usage": 26.65,
    "layout_match": 20,
    "photo_evidence": 10,
    "hardware_completeness": 15,
    "price_clarity": 5,
    "multi_org_bonus": 5
  },
  "rank": 1
}
```

让用户看得见为什么这家排第一。

## 阈值建议

| 分数 | 含义 |
|---|---|
| ≥80 | 强烈推荐：硬件 + 经验 + 价格三齐 |
| 60-79 | 推荐：有信息缺口但核心证据够 |
| 40-59 | 候补：作为备选，需补充询价 |
| <40 | 不建议：证据不足或硬件不达标 |

## 调参原则

- 配分总和 = 100，调任何一维都要同步调其他维
- 不引入"网友评分"这类主观数据，所有分数都来自客观证据
- 调整规则后，跑 `scripts/score.py --recompute-all` 重新生成历史快照
