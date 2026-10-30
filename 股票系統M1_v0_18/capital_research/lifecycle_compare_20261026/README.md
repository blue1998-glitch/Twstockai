# 保存摘要唯讀並列

純API：`lifecycle_compare.compare_saved(request)`。只讀檔CLI：

```bash
cd /workspace/Twstockai/股票系統M1_v0_18
python3 -B -m capital_research.lifecycle_compare_read \
  '等待=capital_research/quantity_replay_20261026/after-final/settled-not-reapproved/actual.json' \
  '原單續用=capital_research/conditional_quantity_review_20261026/after-final/valid-old-fact/actual.json'
```

加`--format json`可讀完整摘要與差異位置；不提供輸出檔、RUN、修復或選勝者路由。-B避免Python產生bytecode快取。

直接閱讀[合法並列表](views-final/wait-versus-reviewed.txt)、[容量不一致拒比](after-final/capacity-mismatch/readable.txt)、[CONTRACT](CONTRACT.md)、[REPORT](REPORT.md)、[21個保存結果](after-final/summary.json)。

只有COMPARABLE才列各欄，正式資格仍false。共同帳戶是同一期初資本／完整權利；期末成交及應付不同是結果。只有摘要、沒有原job／tape不能證明共同市場；停止前歷史帳不能冒成功結果。原件資料來源真偽與job→execution因果都沒有重新驗證，不代表策略績效。

initial保留第一批讀取結果；after-final JSON綁加入跨輪close proof一致性防線後的比較核心。最終views-final是從相同after-final JSON純顯示產生，補股票／方向／核准原單量；比較核心沒有再變，沒有再做市場比對或重算帳務。`tests-final.log`為11方法，顯示修改後只補2個相依方法於`tests-display.log`，11唯一／13次執行，不加歷史或案例數。
