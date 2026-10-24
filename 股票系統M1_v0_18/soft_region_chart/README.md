# K線淡底色主圖0.4.1

此版本從凍結0.4載入相同payload，只更新view_version／artifact_id與畫法；原OHLCV、指標、人工案例、顯示extent、JSON契約與未知值全等。原0.4 source／HTML／ZIP不改。

G1／G2價圖與量圖只畫3%背景色，不畫區域周邊線。G1九月近似起緣漸淡，精確日仍未定；C後仍開放參照。MACD與pane間隙不染色。原點價虛線／來源點保留。3%是助手可逆顯示選擇，不是策略參數或使用者已認可濃度。

根目錄依AGENTS跑bootstrap --hydrate-missing；在股票系統M1_v0_18執行：

```bash
python3 -m soft_region_chart.build --output-dir soft_region_chart/output/rebuild-v041
python3 -m soft_region_chart.package --html soft_region_chart/output/rebuild-v041/M1_v0_19_soft_regions_v041.html --output-dir soft_region_chart/output/package-v041
```

verify_browser.cjs用既有Playwright及Chromium做HTTP實頁檢查，環境變數M1_SOFT_DIR／M1_SOFT_CHECKS／CODEX_BROWSER_EXECUTABLE_PATH／CODEX_PRIMARY_RUNTIME_NODE_MODULES／M1_QA_FONT。QA-only固定本地繁中字體，不寫入自足成品或連外取字體。測試僅針對本次樣式與原值保持，沒有重驗整套舊功能。

[交付ZIP／指紋](../../deliveries/m1-v019-soft-regions-v041-20261019/README.md)；[實測報告](validation_20261019/驗收報告.md)。HTML放在ZIP內，source可重建；不另外重複提交36MB未壓縮HTML。新版Android NOT_TESTED_NEW_BUILD，核心用途NOT_ESTABLISHED，所有原策略／Raw／Adjusted／歷史／來源缺口／SQLite限制保留。
