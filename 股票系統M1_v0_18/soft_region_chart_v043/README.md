# K線淡底色主圖0.4.3

只再加深背景：預設18%，較淡12%／標準18%／明顯26%，無區域框；K線／量柱原色及100%前景不透明度不改，背景先繪，前景後繪。正式標準為背景一眼可辨且K線實體／影線同時清楚，尚待新實機回報。

[新成品](../../deliveries/m1-v019-soft-regions-v043-20261019/README.md)、[本輪32項HTTP、失敗修正、原尺寸圖與限制](validation_20261019/驗收報告.md)。原0.4.2等所有舊來源不改。

```bash
python3 -m soft_region_chart_v043.build --output-dir soft_region_chart_v043/output/final-v043
python3 -m soft_region_chart_v043.package --html soft_region_chart_v043/output/final-v043/M1_v0_19_soft_regions_v043.html --output-dir ../deliveries/m1-v019-soft-regions-v043-20261019
```

build讀固定0.4.1 ZIP並核SHA，不依賴舊可變源頁；原payload僅view_version／artifact_id變更。HTTP before對照0.4.2，先從其ZIP解壓到soft_region_chart_v042/output/final-v042。verify_browser.cjs使用CODEX_PRIMARY_RUNTIME_NODE_MODULES、CODEX_BROWSER_EXECUTABLE_PATH、M1_SOFT_DIR、M1_SOFT_CHECKS與M1_QA_FONT，繁中字體僅QA。不執行file://。

G2 2023-01-16～08-16／136筆及35.90～40.25只作原全選段顯示外包，非正式壓力區界或分價持股；原5/2／40.25代表點保留。G1精確起日未知，九月起緣漸淡，不把9/1當正式起日；C後終點未知，不固定4/30或分類全部後續K。整區量／量口徑／增量／自動分區選關／強度衰減／生命階段仍未定。Raw公司行動、五年Adjusted、歷史公布可得、原資料缺口與SQLite未知根因保持；Darvas箱型正文未完整讀取。UI接入不是核心用途認可，核心用途NOT_ESTABLISHED、分類NOT_VALIDATED、行動NOT_EVALUATED。
