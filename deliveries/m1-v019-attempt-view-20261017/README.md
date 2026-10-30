# M1 v0.19 嘗試關卡／量先價：已接入候選畫面

儲存庫 blue1998-glitch/Twstockai；分支 `dev/m1-v018-chart-annotations`。接續45aaeec，新增 `attempt-view-adapter/0.1`；原 `attempt-evidence-candidate/0.1`、原策略／引擎／schema／歷史／舊候選頁不改，main保留。

本輪完成明確啟用、來源／時點明選、101／106價格子條件、量先價／先後未知、盤中／收盤與跌回事件的畫面、逐前綴重播、當時K／量與完整下載。先勾選啟用、選來源及觀察時點，再讀取；沒有自動選最新、選區、股票或買賣指令。

**只接7個假想工程來源／28個觀察，不是真實股票、全市場選股或績效驗收。** 真實資料需來源／基底／公司行動／當時可得認證，尚未接入；自動選取、正式生命階段／型態／重要性／強勢延續、持倉與資金閉環仍未完成。Android實機未測，SQLite原事故原因未知。

## 可下載檔案

以下是GitHub實際檔案連結，沒有使用工作區或sandbox網址：

- [新單頁小ZIP](https://github.com/blue1998-glitch/Twstockai/raw/refs/heads/dev/m1-v018-chart-annotations/deliveries/m1-v019-attempt-view-20261017/M1_v019_attempt_page.zip)：解壓後開啟 `M1_v0_19_attempt_candidate.html`；新版Android本機開檔仍需實機驗收。
- [完整專案01](https://github.com/blue1998-glitch/Twstockai/raw/refs/heads/dev/m1-v018-chart-annotations/deliveries/m1-v019-attempt-view-20261017/M1_v019_attempt_full_01.zip)
- [完整專案02](https://github.com/blue1998-glitch/Twstockai/raw/refs/heads/dev/m1-v018-chart-annotations/deliveries/m1-v019-attempt-view-20261017/M1_v019_attempt_full_02.zip)
- [完整專案03](https://github.com/blue1998-glitch/Twstockai/raw/refs/heads/dev/m1-v018-chart-annotations/deliveries/m1-v019-attempt-view-20261017/M1_v019_attempt_full_03.zip)
- [獨立候選JSON](https://github.com/blue1998-glitch/Twstockai/raw/refs/heads/dev/m1-v018-chart-annotations/deliveries/m1-v019-attempt-view-20261017/attempt-candidate.json)／[下載SHA-256清單](SHA256SUMS.txt)

三個完整ZIP是普通ZIP，各含部分檔案，請全部解壓至**同一個資料夾**，不需舊包。先讀 `OFFLINE_PROJECT_README.txt`、`CONTINUE_IN_WORK_MODE.md` 最新節；新頁在 `股票系統M1_v0_18/product_candidate/generated/`。該資料夾也保留舊v0.19 K／量／MACD候選頁。完整source、核心、測試、實測及歷史資產已包含；Git checkout才需root bootstrap --hydrate-missing，完整離線包不用重新覆蓋來源。

`PROJECT_FILE_MANIFEST.json`為本包實際檔案指紋；原output指紋保留為歷史基準，不掩蓋合法source差異。`PACKAGE_VERIFICATION.json`記錄三包實際大小、逐檔解壓／原位元組核對及零重複；`GITHUB_DOWNLOAD_VERIFICATION.json`記錄實際發送提交與GitHub HTTP讀回hash，只以實際成功結果為準。

## 實測與來源界線

- 325項Python全套通過（270＋16＋24＋15），不加總先行重測或歷史數字。
- 7來源／28個成品時點與未修改核心逐前綴相符，晚期資料不改早期輸入、K量、frame／event ID或下載文字；只提供完成日線時不造盤中點。
- 真實Chromium桌面／手機模擬87檢查、56次下載原始位元組SHA核對通過，含原精度／大整數、條件分離、未知狀態、來源清除、canvas／DPR、共同游標、時間窗、原生捲動、全螢幕、備援與旋轉。未見JS錯誤／外部HTTP請求／橫向溢位。
- 84個受保護原檔SHA不變，含舊引擎／庫／頁面／成品、原嘗試核心與原候選計算／UI。新下載直接用Python預序列化文字，避免JavaScript大整數損失，不改原數字型別。
- 首輪高速自動下載逾時保留為FAIL診斷；縮小探針可重現同秒下載抑制，採150ms間隔後完整重跑全數成功，沒有減少案例、放寬斷言或關閉瀏覽器保護。

完整命令與契約：[ATTEMPT_VIEW.md](../../股票系統M1_v0_18/product_candidate/ATTEMPT_VIEW.md)；原始log、前綴／保護報告及直橫向截圖：[本輪驗收](../../股票系統M1_v0_18/product_candidate/validation_attempt_view_20261017/驗收報告.md)。假想資料、工程檢查、瀏覽器模擬、Android實機、分類及交易價值分開；NOT_VALIDATED、NOT_EVALUATED、NOT_CLASSIFIED、null勝率與原SQLite根因未知均保留。

## 如何接續

下一步使用**工作模式對話**，先讀root最新CONTINUE、PROJECT_VISION、ATTEMPT_CORE_HANDOFF、VISUAL_RULE_NOTES及本新頁契約／實測。用新頁確認原已裁決例的呈現，並可引導Android實測；真正未定核心仍用圖處理，不重問101必須等106。規則明確或有可重現程式問題後交回Codex。沒有GitHub工具時改用本三個完整ZIP，不能只讀摘要就說已讀source。

環境 `start_skill` 已更新草稿，未發布環境。若日後要建立新快照，請在環境設定檢視、儲存後自行發布；不等同本次GitHub檔案交付，也未宣稱新環境還原已驗證。
