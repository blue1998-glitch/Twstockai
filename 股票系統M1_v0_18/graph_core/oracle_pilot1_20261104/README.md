# M-ORACLE-PILOT1｜合成隔離測試版

**工程已完成；Oracle／私人手機網址受帳戶存取阻塞，未部署。**

[下載合成HTML與ZIP](../../../deliveries/m1-oracle-pilot1-20261104/README.md) · [手機圖](validation/synthetic-chart-390.png) · [橫向比較](validation/synthetic-compare-844.png) · [接續](WORK_HANDOFF.md)

本輪重用原LITE1／viewer／COMP1、core0.2、MA／MACD及OBS1／DU1既存合成案例。搜尋5個合成代號，切換兩個合成日期，點股看互動日K、量、MA／MACD及原判定，選甲／乙作同期並排。短史／來源拒用仍明示；全部頁面及圖上標記「合成測試資料／非真實交易訊號」。兩日期只是工程序列，包含非交易日，不是市場日曆。

不連接FM3、不讀真實行情、不輸出收益、不選主壓力或買賣策略。完整真實工作台及原owner服務未改。首版固定底部導覽會遮圖，隔離版改為頁首正常流，不改原LITE1程式。

|驗收項|本輪結果|
|---|---|
|隔離合成產品／可下載包|完成|
|定向Python|16唯一方法PASS|
|實際Chromium|15最終流程，390直／844橫／1280桌面；手機尺寸含觸控模擬|
|原數值／來源綁定|7合成快照對原引擎與MA／MACD精確相同|
|獨立包與來源隔離|無repo PYTHONPATH驗證、啟動與owner HTTP讀回通過；無引擎重算|
|Oracle實際建立資源|0，本輪未建立；帳戶既有資源UNKNOWN|
|Home Region／配額／整套免費資格|未取得帳戶管理權，UNKNOWN|
|私人HTTPS／外部Android網址|未建立，不提供推測網址|
|使用者Android實機|NOT_TESTED_NEW_BUILD|
|Oracle重啟恢復／日排程|未測／未啟用|

HTML 1,190,644B；ZIP 345,616B。同Cloud冷頁約0.649～0.650秒，JS heap約2.68MiB，開圖87～102ms、比較62～63ms、切日期190～194ms；非Android網路／效能保證。獨立服務RSS／完整資源見[resources](resources.json)，不是Oracle實測。封裝1.094秒；獨立重建全部封包bytes與ZIP完全相同。最終容量見[資源](resources.json)，原512MiB保留有效；沒有刪原件或擴容。

證據：[資格](qualification.json)、[摘要](summary.json)、[原件保全](preservation.json)、[16方法](tests-release-16.log)、[瀏覽器](browser-verification.json)、[重現](reproducibility.json)、[失敗](FAILURES.md)。初次14／修正批與相同瀏覽器流程不累加；不重跑原全市場驗收。

## 真正阻礙與最短接續

本對話runtime雖正常，但沒有Oracle控制台瀏覽器工具、OCI CLI／SDK／profile或授權的帳戶連線。使用者已授權零付費部署；缺的是**可由本唯一Codex操作的正式Oracle管理通道**，不是重複部署同意。單在手機登入Oracle不會把登入會話授予本Codex；不能要求貼密碼、OTP或私鑰，也不假設不存在的「Oracle連接」按鈕。

唯一下一個對象：總監協調一條正式支援、可由此Codex操作的Oracle控制台／OCI管理連線；不重啟／換掉可能持有唯一FM3的原Cloud。若目前平台沒有這種通道，維持BLOCKED，不要求手機搬檔或假裝登入即可自動部署。

[免費資格及部署邊界](QUALIFICATION.md)載明取得連線後的確切核對順序。只允許獨立Oracle合成根／服務；原Cloud不可安裝或啟VPN，沒有Tailscale帳戶新建同意就不代建。未經配額、整套零費用及私人存取核實，禁止Create；Funnel／公開匿名網站始終禁止。

## 工程重現（由既有Codex執行，不要求使用者開終端）

在根治理鎖下，以原專案PYTHONPATH執行：

```text
python3 -m graph_core.oracle_pilot1_20261104.build --output <全新隔離合成目錄>
PILOT_BUNDLE=<該目錄> PILOT_WORK=<獨立測試根> python3 -m unittest -v graph_core.oracle_pilot1_20261104.test_pilot
```

不得指向FM3／舊成品或覆蓋已存在目錄。測試使用獨立臨時合成副本；只刪除自己建立的測試臨時集合，不清理舊來源。ZIP內serve.py僅重用原owner和codec；`verify`檢完整SHA／長度／路徑，`init-auth`透過安全提示建立Git外0600憑證，`serve`只綁127.0.0.1。這些不是自動建機腳本、公開部署或已建立的私人網址。收據另存GITHUB_READBACK，避免自指。
