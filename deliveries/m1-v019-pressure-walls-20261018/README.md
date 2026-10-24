# 五年Raw／左側壓力來源主圖：下載入口

分支dev/m1-v018-chart-annotations，接續a3a58d4；main與原引擎／策略／資料庫／歷史頁未改。這是獨立候選與檔案交付，沒有部署網站。

## 先下載成品

[下載單頁小ZIP](https://github.com/blue1998-glitch/Twstockai/raw/refs/heads/dev/m1-v018-chart-annotations/deliveries/m1-v019-pressure-walls-20261018/M1_v019_pressure_page.zip) → 解壓 → 用瀏覽器開 `M1_v0_19_pressure_chart.html`。

[直接下載HTML](https://github.com/blue1998-glitch/Twstockai/raw/refs/heads/dev/m1-v018-chart-annotations/deliveries/m1-v019-pressure-walls-20261018/M1_v0_19_pressure_chart.html)。HTML解壓約35MiB，需上傳工作模式時建議小ZIP；若連結只顯示原碼，用下載連結／GitHub Download raw file，不在原碼預覽驗收。

## 完整專案三個普通ZIP

| 檔案 | 下載 |
|---|---|
| 第1包 | [M1_v019_pressure_full_01.zip](https://github.com/blue1998-glitch/Twstockai/raw/refs/heads/dev/m1-v018-chart-annotations/deliveries/m1-v019-pressure-walls-20261018/M1_v019_pressure_full_01.zip) |
| 第2包 | [M1_v019_pressure_full_02.zip](https://github.com/blue1998-glitch/Twstockai/raw/refs/heads/dev/m1-v018-chart-annotations/deliveries/m1-v019-pressure-walls-20261018/M1_v019_pressure_full_02.zip) |
| 第3包 | [M1_v019_pressure_full_03.zip](https://github.com/blue1998-glitch/Twstockai/raw/refs/heads/dev/m1-v018-chart-annotations/deliveries/m1-v019-pressure-walls-20261018/M1_v019_pressure_full_03.zip) |

**三包各自解壓到同一新的空資料夾，不覆蓋已有修改。** 每包小於32MiB，實際大小與CRC／全檔解壓SHA見[PACKAGE_VERIFICATION.json](PACKAGE_VERIFICATION.json)。入口：`股票系統M1_v0_18/pressure_chart/generated/M1_v0_19_pressure_chart.html`。資產已齊，不需舊包或bootstrap；包含原頁、新主圖、source、官方原檔、證據與最新交接，不含Git物件庫／遞迴備份ZIP。

[SHA清單](SHA256SUMS.txt) · [完整檔案清單](PROJECT_FILE_MANIFEST.json) · [GitHub下載讀回收據](GITHUB_DOWNLOAD_VERIFICATION.json)。收據在第一次推送、實際遠端下載核對後另提交；不把本機打包當遠端保存。

## 本輪實際可用

四檔約五年真實Raw：1101／2884各1213、6488／8069各1214，2021-10-18～2026-10-16；每檔61個官方月回應、12份市場年曆及抓取時間／SHA。新主圖預設24日曆月日K，可看18月／約5年、縮放平移／近期、K量MACD共用窗與游標，K面板右下44px＋−，畫外價量來源仍提示／定位。

原source／snapshot綁定的1101①→④與新來源後續真實量／收盤事實分開，增量未定；點看來源區間的真實high、總量／最高日量、後續日曆／K數與每日路徑。價格牆與量牆是兩維證據，月份不是已認可整理區；不自動認定正式高牆／魔王，不當精確未解套持股或分價籌碼。

實測357 Python通過，最後修正後21專項再測；新頁Chromium194檢查／100精度下載通過；實際HTML4854新Raw時點及244源檔核對，原1490frame數值全等。原1011檔僅3份說明入口更新，其餘1008檔SHA不變。

**尚未完成**：完整公司行動／歷史公布時刻及五年Adjusted、6日休市／停牌主證、新頁Android實機、正式區界／自動重要性／魔王／時間衰減／異常與增量規則。Raw跨期高點不當已校正壓力；五年不等於完整歷史新高。分類NOT_VALIDATED、交易NOT_EVALUATED，全市場／換股／資金閉環及SQLite原事故根因未完成／未證實。

[資料缺口與範圍](DATA_GAPS.md) · [新版手機步驟](../../M1_V019_PRESSURE_CHART_ANDROID_ACCEPTANCE.md) · [完整契約／重現](../../股票系統M1_v0_18/pressure_chart/README.md) · [本輪實測](../../股票系統M1_v0_18/pressure_chart/validation_20261018/驗收報告.md) · [繼續工作模式](../../CONTINUE_IN_WORK_MODE.md)。

下一步用**工作模式**做新頁實機／用途回饋；可重現問題交Codex，同一開發分支保存，不改main。舊technical頁PARTIAL_EVIDENCE_OBSERVED不能沿用成新版通過。
