# 台泥財報第58頁：獨立日期角色觀察0.1（本地未提交）

基線／已核遠端 `41c82485e5b7056657cc1ac1e069a91ea1957b9e`，原唯一Codex／原工作區／指定分支，起始tracked/index/untracked均0。使用者只授權本頁來源增補及必要定向驗證，先不commit/push。資金框架維持0.8、來源catalog維持0.10與全部parents；本附錄為獨立來源觀察0.1。

## 實際完成

先保存 `source-inventory-before.json`（13項原件／原模組／原catalog／根文件指紋）、`input.json`、`expected.json`及`intake.json`，再新增純核心 `rotation_research/treasury_date_roles.py`、有限IO接線 `build.py`及本頁測例。IO只讀既存PDF、全文、metadata、舊抽字紀錄與原0.7觀察；沒有新官方請求、OCR、全文重抽或舊producer呼叫。

原文（實體PDF／印刷第58頁首段）：

> 本公司於115年1月經董事會通過註銷庫藏股28,000仟股，並於115年2月辦理變更登記完成。

|保存欄位|值|角色|
|---|---|---|
|board_approval_month|2026-01|董事會通過月份，非確切生效日|
|registration_completed_month|2026-02|公司報告的登記完成月份，非主管機關直接核定原件|
|cancellation_quantity|28000／THOUSAND_SHARES|公司庫藏股數量，非個人受配／減資比例|
|確切董事會日／登記日／生效日|全部null|原段未明載確切日，不補1日、月底或用登記月代替生效日|
|announced_at、個人換股比例／現金／權利|全部null|沒有歷史公開可得或個人影響證明|

`actual.json`是原保存來源的新獨立觀察，明確連回原0.7觀察 `sha256:2416ebd2dd3f52971a48df9af53ab491393797fc0aa3220e29b81871972a9b89`。不另算公司行動、帳務事件或市場樣本，不回寫舊月份欄位／舊選頁。保留family、公司庫藏股持有人及instrument角色，不能借給一般股東個人帳。

## 原件與時間證據

原PDF仍位於 `../source_followup_20261023/raw/tcc-2026-q2-consolidated-report.response`：3320224bytes，SHA256 `e8a8ca682a242180a908a68030dc80ee0321ddf92217586f59230b1d3e584d2d`。原全文410402bytes，SHA256 `b3bf4f18757b595a8019cf304fd3e72c61deb2c31c8d50a29ea1ea9954bb6ce8`；第58頁2229bytes，SHA256 `2e6bcab6a95d1d284011167e40a3c9e40227fd1c30b813c7bf4c61013e72493c`。

`verification.json`核實原PDF／metadata／抽字紀錄／124頁全文／精確第58頁及原觀察綁定。原選頁仍只有7、52、54、55、57，沒有修改原evidence.json或source0.7 parser。原PDF捕捉2026-10-23T08:33:10.538370+00:00、原讀回08:33:10.538392+00:00保留；新本機讀取及來源觀察時間存在input，之後的檔案核驗時間另外記錄，不冒稱新官方擷取。

只另轉繪同一保存PDF第58頁成 `page58-source.png`，pdftoppm return0、stderr空；已實讀圖中首段及頁碼，與native text相符。`visual-render.json`保留轉繪前後收據，`visual-review.json`另記實讀時間與PNG指紋；沒有覆寫先前input／actual／observed_at，也沒有新UI。全文其他123頁沒有因此冒稱本輪全部視讀。

新觀察可知時間晚於原捕捉、原讀回及本輪讀取。`resolve`沿既有精確來源／持有人／instrument／日期角色／單位／觀察截止helper；早於新觀察、FINAL_LEDGER、歷史訊號及null欄位均拒用。公司報告日期或月份不當作當時公開時間；不能讓2026年10月才保存／觀察到的附錄自動成為一月決策證據。

## 實際驗證

`tests-final.log`：**本輪13個唯一方法PASS，舊suite執行0**。一個真實保存來源正例；負例全部為記憶體內明標工程變體，不改原件。沒有失敗或中間批次可累加，也不累加歷史22等PASS。

範圍涵蓋：凍結oracle、PDF／native／頁碼與issuer綁定、頁面篡改、缺句／重複句／單位／明示日／無效月份拒絕、精確角色解析、未知欄位不補零、FINAL_LEDGER／歷史用途拒絕、禁止回填一月可知時間、重新指紋仍不能升格日期或資格、實際原件reader、原catalog及舊模組保全、純核心不開檔或執行帳務。

純核心無網路／檔案／資料庫IO，不呼叫帳務或窗口資格；IO接線只保存一項新觀察。`build.log`記新單筆觀察builder執行1次，不等於原來源producer或窗口producer。原始輸入及預期在實作前已保存，沒有以actual改寫oracle。

## 尚不能證明／未執行

確切董事會、登記及生效日；個人股數轉換、退資、權利、淨額；一月窗口是否存在其他公司行動；完整覆蓋及歷史公布可得，仍未證。此段不是主管機關登記完成日的直接原件，也不證1/2～1/9已生效或未生效。

未修改舊catalog、原件、原資格／帳務／策略／圖形；未新增來源catalog0.11或資金框架版本；所有data/execution/historical/accounting/policy/live資格false、主壓力null。70拒算／2不足／其中8換股未支援／真實總淨合格0仍是保存狀態，本輪未重算。

無窗口producer、舊suite、真實績效／六方案、UI／Android、樣本外、bootstrap/hydrate、封包、commit/push、部署／交易／付費／訊息或子代理。R2/F及原未支援帳務不擴張。Astra與第一工作區救援原件仍未取得／未讀，不重建或推定890檔。Work尚未取得本地未提交附錄，不冒稱獨立驗收。
