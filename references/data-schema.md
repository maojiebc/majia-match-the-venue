# Data Schema

majia-match-the-venue 用三个文件存全部数据，全部 JSON / JSONL，人类可读、git diff 友好。

## `data/venues.json` — 酒店主库

一个酒店一条 record。

```jsonc
{
  "schema_version": "0.1",
  "updated_at": "YYYY-MM-DD",
  "venues": [
    {
      "id": "shanghai-jinganshangrila",   // 小写 + 短横线，城市拼音前缀
      "name": "上海静安香格里拉大酒店",
      "city": "上海",
      "district": "静安区",               // 上海六区之一：浦东/静安/黄浦/徐汇/长宁/闵行
      "address": "上海市静安区华山路1218号",
      "location": {"lat": 31.224, "lng": 121.443},
      "brand": "Shangri-La",
      "star": 5,
      "venue_class": "luxury",            // luxury | upper-upscale | upscale | midscale
      "rooms": [
        {
          "name": "静安大宴会厅",
          "area_sqm": 1100,
          "ceiling_m": 10,                // 层高（米），关键指标
          "pillar_free": true,            // 无柱与否，关键指标
          "capacity": {
            "theater": 1695,              // 剧院式
            "classroom": 770,             // 课桌式（培训场景重点）
            "round_table": 600,
            "u_shape": null,
            "cocktail": 1800
          },
          "screen": {
            "type": "LED+projector",      // LED | projector | LED+projector | none
            "main_screen_size_m": null,   // 主屏宽度（米），未知留 null
            "ground_clearance_m": null,   // 主屏离地高度（米），关键指标
            "obstruction_risk": "low",    // low | medium | high
            "notes": "宴会厅层高 10 米，主屏抬升空间充足"
          },
          "price_range_cny": {
            "half_day": [40000, 80000],   // [min, max]
            "full_day": [60000, 150000],
            "tea_break_per_pax": [80, 150],
            "lunch_per_pax": [380, 680],
            "note": "估算区间，实际以销售报价为准"
          }
        }
      ],
      "official_source": "https://...",    // 酒店官方活动空间页
      "tags": ["大屏", "高层高", "无柱"],   // 自由标签，用于查询
      "training_fit_notes": "...",         // 1-2 句话总结为什么适合培训
      "verified": false,                   // 是否人工审核通过
      "verified_by": null,
      "updated_at": "YYYY-MM-DD"
    }
  ]
}
```

### 关键字段口径

- `ceiling_m`：层高决定主屏能不能抬高，<5 米的厅基本不适合 100 人以上 PPT 培训
- `pillar_free`：有柱子的厅在课桌式布局下会大量损失有效座位
- `screen.ground_clearance_m`：主屏离地 ≥1.5 米基本能避免被前排遮挡
- `capacity.classroom`：培训场景重点看这个，不是 theater

## `data/orgs.json` — 观察机构清单

被观察的高端培训/咨询/商学院/私董会机构。

```jsonc
{
  "schema_version": "0.1",
  "updated_at": "YYYY-MM-DD",
  "orgs": [
    {
      "id": "ckgsb",
      "name": "长江商学院",
      "category": "business-school",   // business-school | premium-training | consulting | private-board | training-contractor
      "tier": "S",                      // S | A | B（决定打分权重）
      "wechat_official": "长江商学院",   // 公众号名（用于关键词搜索/订阅）
      "website": "https://...",
      "keywords": ["长江商学院", "CKGSB", "EMBA"],  // 抓取/匹配用
      "weight": 1.0,                    // 0-1，S=1.0 / A=0.85 / B=0.65 默认
      "notes": "..."
    }
  ]
}
```

### tier × weight 默认对应

| tier | weight | 含义 |
|---|---|---|
| S | 1.0 | 头部机构，单条证据即显著加分 |
| A | 0.85 | 次头部 |
| B | 0.65 | 中腰部，需多条证据交叉验证 |

## `data/evidence.jsonl` — 活动证据流水

**一行一条 JSON**，append-only。

```jsonc
{
  "id": "ev-20260511-001",               // 自增 ID
  "org_id": "dedao",                      // 关联 orgs.json
  "venue_id": "shanghai-anadi",           // 关联 venues.json（未入库的酒店可临时填 null + venue_name_raw）
  "venue_name_raw": null,                 // 抽取出来但尚未匹配到 venue_id 时存原文
  "room_name": "大宴会厅",                 // 哪个厅
  "event_name": "得到·X计划第三期开学",
  "event_type": "training",               // training | salon | conference | private-board | release | other
  "course_tier": "private",               // public（公开课） | private（内训/闭门） | board（私董会）
  "event_date": "2025-09-15",
  "attendees": 120,
  "layout": "classroom",                  // theater | classroom | round_table | u_shape | cocktail | unknown
  "source_url": "https://mp.weixin.qq.com/s/...",
  "source_type": "wechat",                // wechat | huodongjia | huodongxing | xhs | weibo | official | other
  "photo_urls": ["..."],                  // 现场照片 URL（不直接保存图片，只存外链）
  "notes": "现场照片显示课桌式、LED 主屏、有前排桌椅",
  "verified": false,                      // 默认 false，人工 review 后置 true
  "verified_by": null,
  "ingested_at": "2026-05-11",
  "ingested_by": "manual"                 // manual | parser-wechat | parser-huodongjia | parser-llm
}
```

### ID 约定

- `venue_id`：城市拼音 + 短横线 + 酒店关键词，例如 `shanghai-jinganshangrila`
- `org_id`：见 `orgs.json`
- `evidence.id`：`ev-YYYYMMDD-NNN`，按入库日期顺序

### Append-only 原则

evidence.jsonl 永远只追加，不修改既有行。需要修订时新增一行 `revises: <old_id>` 字段。
这样所有变更都有 git diff 可追踪。

## 版本演进

`schema_version` 字段独立。v0.1 → v0.2 时写一个 `scripts/migrate_v0.1_to_v0.2.py`，旧数据可平滑迁移。
