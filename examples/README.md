# Examples

这个目录里的所有内容都是 **demo 数据**，用来展示 majia-match-the-venue 的输出样子。
真实的活动证据请通过 `scripts/ingest.py` 录入。

## 文件清单

### `demo-evidence.jsonl`

10 条**虚构的**活动证据，用来演示打分系统的区分能力：

| org | venue | 课型 | 用途 |
|---|---|---|---|
| 得到 | 阿纳迪 | board | 集中在阿纳迪触发跨机构加成 |
| 长江商学院 | 阿纳迪 | private | 同上 |
| 混沌学园 | 阿纳迪 | board | 同上 |
| 麦肯锡 | 文华东方浦东 | private | 单一咨询机构 |
| 中欧 | 金茂君悦 | private | 商学院 EMBA |
| 正和岛 | 静安瑞吉 | board | 私董会 |
| 贝恩 | 半岛 | private | 客户答谢 |
| 领教工坊 | 璞丽 | board | 小规模私董 |
| 长江商学院 | 静安香格里拉 | private | DBA 开学 |
| 得到 | 嘉里浦东 | public | 年度大会 1200 人 |

**所有证据的 `source_url` 都是 example.com 假链接，photo_urls 都不可访问**。
仅用于报告样例，不构成任何真实业务参考。

### `report-shanghai-classroom-100.md`

场景：**上海全市 100 人课桌式培训**。
阿纳迪夺冠（87.5/100，强烈推荐）— 3 家高端机构集中使用 + 课型完全匹配 + 跨机构加成。

### `report-jingan-board-80.md`

场景：**静安区 80 人圆桌私董会**。
瑞吉（正和岛证据）与璞丽（领教工坊证据）排在前面，香格里拉（长江商学院证据）紧随。

### `report-shanghai-launch-1000.md`

场景：**上海全市 1000 人剧院式发布会**。
嘉里浦东（得到 1200 人大会证据）夺冠，其他大型宴会厅按硬件分数排。

## 如何复现这些报告

```bash
# 1. 加载 demo 数据
cp examples/demo-evidence.jsonl data/evidence.jsonl

# 2. 跑你想看的场景
python scripts/report.py --city 上海 --layout classroom --attendees 100 --top 5

# 3. 清空 demo 数据，回到干净状态
: > data/evidence.jsonl
```

## 注意

这些 demo 数据**不应**保留在 `data/evidence.jsonl` 里。
fork 仓库或部署到自己项目时，请用真实的公开活动链接 ingest，从零开始积累。
