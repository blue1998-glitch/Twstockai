# M1 v0.19 獨立候選下載與接續

分支：`dev/m1-v018-chart-annotations`，main 保留。專案資料夾仍叫 `股票系統M1_v0_18`，新 source 在 `product_candidate/`。本輪先做需求／程式對照，再補確定缺口；**核心分析用途尚未獲使用者認可**。

新候選提供已保存波段／區域的證據主線、逐日鏈與重播、支持／反證／缺證、任意可用日期及價格尺度、共用時間軸的K線／原股數量／獨立MACD。生命階段、正式修正／三種整理、盤中及籌碼仍未知；不是用多畫點線宣稱完成。舊引擎、策略、門檻、共同schema、庫及頁面保留。

## 下載

點下列連結下載；若瀏覽器只顯示檔案，可用「下載／另存連結」。這些是GitHub實際檔案連結，沒有使用先前失效的工作區／sandbox下載。

- [候選單頁小ZIP](https://github.com/blue1998-glitch/Twstockai/raw/refs/heads/dev/m1-v018-chart-annotations/deliveries/m1-v019-context-20261017/M1_v019_candidate_page.zip)：解壓後開啟 `M1_v0_19_candidate.html`，明選股票／模式與分析日。新頁Android本機開檔尚未測試。
- [完整專案01](https://github.com/blue1998-glitch/Twstockai/raw/refs/heads/dev/m1-v018-chart-annotations/deliveries/m1-v019-context-20261017/M1_v019_full_01.zip)
- [完整專案02](https://github.com/blue1998-glitch/Twstockai/raw/refs/heads/dev/m1-v018-chart-annotations/deliveries/m1-v019-context-20261017/M1_v019_full_02.zip)
- [完整專案03](https://github.com/blue1998-glitch/Twstockai/raw/refs/heads/dev/m1-v018-chart-annotations/deliveries/m1-v019-context-20261017/M1_v019_full_03.zip)
- [獨立候選JSON](https://github.com/blue1998-glitch/Twstockai/raw/refs/heads/dev/m1-v018-chart-annotations/deliveries/m1-v019-context-20261017/candidate.json)／[完整精度與三包SHA-256](SHA256SUMS.txt)

三個完整ZIP各含部分檔案，請**全部解壓到同一資料夾**。這是普通ZIP，不是需特殊工具的分割卷；全部合併就是完整離線專案，無需舊ZIP。先讀 `OFFLINE_PROJECT_README.txt` 與 `CONTINUE_IN_WORK_MODE.md`。候選HTML／JSON在 `股票系統M1_v0_18/product_candidate/generated/`，規則、測試及截圖在 `product_candidate/`。

完整ZIP已內附歷史資產，直接使用，不需跑bootstrap。從Git checkout接續才要在repository root跑 `python3 codex/bootstrap_m1.py --hydrate-missing`，保留source修改、補缺資產；不要使用舊ZIP覆蓋新版。`PROJECT_FILE_MANIFEST.json`是本次實際檔案指紋，原 `output/交付檔案指紋.json` 保留為舊基準，已知合法差異不可掩蓋。

## 實際證據及限制

- 286 Python通過；最後純顯示明細調整後16項候選重測通過。
- 6組1490真實保存frame、12組截短前綴核對通過；同事件／同錨定、無未來資料、原股數與完整精度。
- 最後HTML真實Chromium66檢查、48次精確JSON下載通過；桌面／手機模擬、手勢、旋轉、全螢幕、原生捲動、共同日期及無JS錯誤／外部請求／橫向溢位。
- 51項原引擎、庫及舊HTML歷史指紋相符，既有src與開始時Git HEAD相符。
- 實體Android未測；正式分類／交易價值未驗證；SQLite原事故原因未證實。完整時點、原始log、失敗工具初稿及最終成功證據見 [驗收報告](../../股票系統M1_v0_18/product_candidate/validation_20261017/驗收報告.md)。

`PACKAGE_VERIFICATION.json`記錄三包實際大小、解壓後全檔逐位元組核對及零重複項目；不是單憑壓縮成功就認定完整。`GITHUB_DOWNLOAD_VERIFICATION.json`會記錄發佈成品提交、HTTP讀回及每個檔案SHA；只以實際成功結果為準。

## 下一步

使用**工作模式對話**，先讀根目錄 `CONTINUE_IN_WORK_MODE.md`、`M1_V019_REQUIREMENTS_TRACE.md` 與 `M1_V019_CORE_RULE_DECISIONS.md`，針對具體1101／2884保存時點整理生命階段、修正、關鍵低點與三種整理的必要／排除／失效條件。不要自行發明門檻。可引導新版Android實機操作驗收；有明確規則或可重現錯誤後交回Codex。若工作模式無GitHub工具，使用上方三個完整ZIP，不得宣稱已讀未存取的source。

本環境依 cloud-environment-onboarding:setup 保存了更新後的 `start_skill` 草稿，未改網路／金鑰、未發布環境。若日後要將它用於新環境快照，需在環境設定檢視、儲存變更後自行發布；這與本次GitHub檔案交付不同，亦未宣稱新工作階段還原已驗證。
