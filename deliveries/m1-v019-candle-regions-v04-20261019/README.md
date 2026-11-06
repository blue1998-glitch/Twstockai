# M1 K線範圍價量區域主圖 0.4

本版修正價量區域的畫法：價框包所選真實日K影線，量框獨立，MACD不再填區域。縮放／平移只裁切完整選段extent，不重取可見子窗高低、不拉伸價軸、不假貼邊。新增獨立版本，原0.1／0.2／0.3、數值引擎／策略／庫／歷史／原案例與手機證據保留。

## 成品入口

- [下載小ZIP（4.37 MB）](https://raw.githubusercontent.com/blue1998-glitch/Twstockai/d83f92cb47fe581ee76ee05a6f944cd5abc56434/deliveries/m1-v019-candle-regions-v04-20261019/M1_v019_candle_regions_v04.zip)
- [ZIP SHA256](SHA256SUMS.txt)、[CRC／解壓原檔SHA核對](PACKAGE_VERIFICATION.json)
- [HTML原檔（36.78 MB，下載後開啟）](https://raw.githubusercontent.com/blue1998-glitch/Twstockai/d83f92cb47fe581ee76ee05a6f944cd5abc56434/%E8%82%A1%E7%A5%A8%E7%B3%BB%E7%B5%B1M1_v0_18/candle_region_chart/generated/M1_v0_19_candle_regions_v04.html)
- [修正前後實際畫面／實測報告／失敗及未測](../../股票系統M1_v0_18/candle_region_chart/validation_20261019/驗收報告.md)
- [完整可貼Work指令，只驗新版外框差異](WORK_HANDOFF.md)、[來源指紋清單](SOURCE_HASHES.json)
- [GitHub實際下載核對收據](GITHUB_DOWNLOAD_VERIFICATION.json)：已實際PASS，固定成品提交145檔共56,224,224 bytes下載逐字比對；遠端ZIP的CRC／全部解壓SHA亦核對。此後README／Work指令／收據另存交接提交，不宣稱收據自我包含於成品提交。

ZIP：4,372,484 bytes；SHA256 `0a759763dbebf562fa009097de3dc580a5ea296dc307b048366eaf0c0ca60cfc`。
HTML：36,783,169 bytes；SHA256 `8642986a70a1c315046327b4ec97452eae19ba78fbe619a713ce2965de42d44f`。

解壓開`M1_v0_19_candle_regions_v04.html`，標頭「M1 K線範圍區域主圖 0.4」。1101／Raw｜新官方日線／10/16，日收27.30、24月486根。按G2看1/16～8/16的136筆來源：影線外包35.90～40.25、原5/2／40.25保留；量框在量圖獨立，MACD無底色。按G1看九月虛線未閉合左緣→C；C後無假封閉框。＋／−及移圖看裁切，24月返回近期視窗，分析日不變。查詢、原OHLCV、草稿與舊標籤功能保留。

**35.90～40.25是display extent，不是已定正式壓力上下界。** G1精確起日未知，近似97筆顯示錨不是正式歸屬；C後終點仍未定。整區量／量口徑、自動分區選關、增量、強度衰減與生命階段未定，沒有新增策略門檻。量框最高柱不等於整帶量／分價／套牢持股。

## 本輪實際證據與限制

本輪15定向及完整398 Python PASS；同一最終HTML真實Chromium208 HTTP／44標籤／55原操作／32外框檢查PASS，四尺寸含真實觸控、全精度下載、MACD像素／裁切及實際前後截圖。不是沿用前輪數字；首次新測試匯入失敗已保存並修正。整體runner仍PASS_WITH_KNOWN_BLOCKER，原file://政策阻擋未重試／繞過。244來源／4854新Raw與1490原frame／50oracle、凍結0.3 payload、ZIP CRC及解壓SHA已核。

0.4 Android **NOT_TESTED_NEW_BUILD**；0.3-family兩張圖PARTIAL_EVIDENCE_OBSERVED_VERSION_UNCONFIRMED與0.2原部分證據保留，不重索同檔或搬作新通過。HTTP模擬不是Android／手機本機開檔；下一步Work只驗新外框差異，只有要驗本版新下載才收新JSON。核心用途NOT_ESTABLISHED／NOT_VALIDATED／NOT_EVALUATED維持。

Raw完整公司行動／五年Adjusted／歷史公布可得、原來源缺口／SQLite未知根因、Darvas正文未完整閱讀等限制保留。原庫／歷史／舊頁不變，main不改，無部署／付費／交易／訊息／子代理。

[舊0.3成品入口](../m1-v019-manual-regions-v03-20261018/README.md)保留。完整source在指定分支；小ZIP是自足頁面與原案例，不冒充整個專案備份。下一步用**Work**，貼上本目錄WORK_HANDOFF.md全文；可重現工程問題再回Codex。

固定成品提交：`d83f92cb47fe581ee76ee05a6f944cd5abc56434`。GitHub已實際保存並下載核對；最新交接沿同一分支。main仍`9c5b168c09ba80010c74f03b9c537e8b7474256a`，未變。固定下載入口不隨後續分支修改而漂移。
