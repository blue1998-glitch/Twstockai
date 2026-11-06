# K線淡底色主圖0.4.2

本輪使用者回報上一版「看不到底色區域」。本模組獨立建立較清楚的12%底色，以及較淡8%／標準12%／明顯20%的顯示選項，仍無區域邊框。原0.4.1／0.4／舊頁及案例不改。

[成品入口](../../deliveries/m1-v019-soft-regions-v042-20261019/README.md)、[28項HTTP／原圖／實測與限制](validation_20261019/驗收報告.md)。HTML僅交付ZIP內，不另提交36MB檔。

在股票系統M1_v0_18執行：

```bash
python3 -m soft_region_chart_v042.build --output-dir soft_region_chart_v042/output/final-v042
python3 -m soft_region_chart_v042.package --html soft_region_chart_v042/output/final-v042/M1_v0_19_soft_regions_v042.html --output-dir ../deliveries/m1-v019-soft-regions-v042-20261019
```

固定父ZIP在deliveries/m1-v019-soft-regions-v041-20261019，build驗SHA後使用；只有payload view_version／artifact_id更新，原值無損核對。填色函式由fill_patch.js在父頁初始化後覆寫，選項只重畫本地UI，不保存策略或案例。

verify_browser.cjs需要Playwright／Chromium，環境變數M1_SOFT_DIR、M1_SOFT_CHECKS、CODEX_BROWSER_EXECUTABLE_PATH、CODEX_PRIMARY_RUNTIME_NODE_MODULES及M1_QA_FONT；具體實測條件見報告。父頁可從固定父ZIP解壓至soft_region_chart/output/soft-v041供前後比對。

G2 2023-01-16～08-16／136筆及35.90～40.25只作原全選段顯示外包，非正式壓力區界或分價持股；原5/2／40.25代表點保留。G1精確起日未知，九月起緣漸淡，不把9/1當正式起日；C後終點未知，不固定4/30或分類全部後續K。整區量／量口徑／增量／自動分區選關／強度衰減／生命階段仍未定。Raw公司行動、五年Adjusted、歷史公布可得、原資料缺口與SQLite未知根因保持；Darvas箱型正文未完整讀取。UI接入不是核心用途認可，核心用途NOT_ESTABLISHED、分類NOT_VALIDATED、行動NOT_EVALUATED。
