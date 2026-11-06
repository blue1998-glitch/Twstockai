# 個股技術分析主圖 0.1：下載入口

使用分支 `dev/m1-v018-chart-annotations`，接續3dcfcf6；保留main及原策略／歷史。新頁Android尚未實機驗收，以下是雲端實測交付。

## 只開啟成品

[下載單頁小ZIP](https://github.com/blue1998-glitch/Twstockai/raw/refs/heads/dev/m1-v018-chart-annotations/deliveries/m1-v019-technical-chart-20261017/M1_v019_chart_page.zip) → 解壓 → 用瀏覽器開啟 `M1_v0_19_technical_chart.html`。

[直接下載HTML](https://github.com/blue1998-glitch/Twstockai/raw/refs/heads/dev/m1-v018-chart-annotations/deliveries/m1-v019-technical-chart-20261017/M1_v0_19_technical_chart.html)。若連結顯示原始碼，請使用瀏覽器「下載連結」或GitHub檔案頁的 Download raw file。這是離線檔案交付，沒有部署網站。

## 完整專案：三個普通ZIP

| 檔案 | 下載 |
|---|---|
| 第1包 | [M1_v019_chart_full_01.zip](https://github.com/blue1998-glitch/Twstockai/raw/refs/heads/dev/m1-v018-chart-annotations/deliveries/m1-v019-technical-chart-20261017/M1_v019_chart_full_01.zip) |
| 第2包 | [M1_v019_chart_full_02.zip](https://github.com/blue1998-glitch/Twstockai/raw/refs/heads/dev/m1-v018-chart-annotations/deliveries/m1-v019-technical-chart-20261017/M1_v019_chart_full_02.zip) |
| 第3包 | [M1_v019_chart_full_03.zip](https://github.com/blue1998-glitch/Twstockai/raw/refs/heads/dev/m1-v018-chart-annotations/deliveries/m1-v019-technical-chart-20261017/M1_v019_chart_full_03.zip) |

**三包各自解壓至同一新的空資料夾**；不要覆蓋已有修改。每包小於32MiB，實際大小、CRC／全檔解壓SHA核對見 [PACKAGE_VERIFICATION.json](PACKAGE_VERIFICATION.json)。完整ZIP包含已準備歷史資產、可編輯source、原頁、新主圖、測試證據、根目錄交接；不需下載舊ZIP或再bootstrap。入口是 `股票系統M1_v0_18/technical_chart/generated/M1_v0_19_technical_chart.html`。

[檔案SHA清單](SHA256SUMS.txt) · [完整專案檔案清單](PROJECT_FILE_MANIFEST.json) · [GitHub下載讀回核對](GITHUB_DOWNLOAD_VERIFICATION.json)。GitHub核對檔在第一次推送後另提交，核對實際遠端檔案，不把本機打包當上傳完成。

## 這次實際可用及限制

開啟直接看到個股日K；最早／全段／近期、縮放平移、同步K／量／MACD及游標、切股／Raw或Adjusted候選、逐日回看／重播、點保存結構及事件查來源證據、下載當時前綴與歷史事件。初始1101 Raw／2026-09-30是固定保存入口，非今日行情。

1101／2884只有2026-01-02～09-30各179根；6488／8069是2025-08-01～2026-09-30各283根。沒有多年或9/30後資料、真實盤中，沒有硬套101／106、自動左區或正式買點。原候選數值逐值全等，原核心未改。

本輪Python336全套通過，最後下載修改後11項focused通過，不與336相加；舊Node介面16項／18真實對照通過；新頁真實Chromium87項／60精度下載通過；1490時點成品來源／前綴核對通過。手機模擬不是Android實機。分類、交易績效／全市場／資金閉環及原SQLite事故根因未完成／未證實。

[手機簡單步驟](../../M1_V019_TECHNICAL_CHART_ANDROID_ACCEPTANCE.md) · [接續交接](../../CONTINUE_IN_WORK_MODE.md) · [完整契約及命令](../../股票系統M1_v0_18/technical_chart/README.md) · [實測報告](../../股票系統M1_v0_18/technical_chart/validation_20261017/驗收報告.md)。

下一步：**工作模式**引導新主圖Android實測及真實用途回饋；可重現工程問題或更長真實資料接入交Codex，成果更新同一分支。
