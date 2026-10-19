# M1 可執行圖形辨識研究核心 0.1

新增獨立純數值核心，依所選完成收盤的前綴自動找跨尺度轉折／反覆箱、左側相關壓力、父子包含、離箱跌回、破底後新箱及價量反證；人工答案不輸入核心。接上真實可縮放K／量／MACD、同步查詢、已算前綴回放與精確JSON。原引擎策略／庫／歷史／舊頁／0.4.3及圖片庫保留。

**工程可執行不代表圖形用途已認可。** 人工39筆前箱及完整月份主帶尚未精確重現，重要性／正式區界等仍未定，不調參湊答案、沒有訓練圖片模型或準確率。核心NOT_ESTABLISHED／分類NOT_VALIDATED／行動NOT_EVALUATED，Android NOT_TESTED_NEW_BUILD。

## 入口

- [下載研究主圖ZIP（5.04 MB）](https://raw.githubusercontent.com/blue1998-glitch/Twstockai/dev/m1-v018-chart-annotations/deliveries/m1-v019-graph-core-20261019/M1_v019_graph_recognition_v01.zip)
- [ZIP SHA256](SHA256SUMS.txt)、[實際CRC／9成員解壓核對](PACKAGE_VERIFICATION.json)
- [HTML原檔（13.75 MB，下載後開啟）](../../股票系統M1_v0_18/graph_core_chart/generated/M1_v019_graph_recognition_v01.html)
- [實測／畫面／失敗／辨識缺口](../../股票系統M1_v0_18/graph_core_chart/validation_20261019/驗收報告.md)
- [可直接讀的小型辨識差異及參數敏感度](../../股票系統M1_v0_18/graph_core_chart/generated/recognition-audit.json)
- [研究核心公式與限制](../../股票系統M1_v0_18/graph_core/README.md)、[重建與使用](../../股票系統M1_v0_18/graph_core_chart/README.md)
- [完整可貼Work指令](WORK_HANDOFF.md)、[source指紋](SOURCE_HASHES.json)、[GitHub實際下載收據](GITHUB_DOWNLOAD_VERIFICATION.json)（收據實際建立且PASS後才代表遠端核對）

ZIP **5,040,045 bytes**，SHA256 `934c54ec033de14d402cb4b8110ed53e9a99b311a934144f9139950c05046783`。
HTML **13,748,260 bytes**，SHA256 `fbca1e1d7e82d5dc9dcca8da0d3c8619f59431c1119d2cd8cb4c8ffc8293a724`。

解壓開`M1_v019_graph_recognition_v01.html`，標頭「M1 圖形辨識研究主圖 0.1」。1101／Raw／2026-10-16，已存收盤27.30，非即時今日。約五年／24月／＋−及移圖可瀏覽全部真實日線，預設拖曳查詢；研究箱選單可聚焦來源與讀中文反證。虛線是參照，不表示後續每根都屬同箱。人工對照預設折疊、明示非核心輸入。

四股4854根價格完整保留，**只預算每股15個、共60個分析前綴**，回放明示只播已算日，最近5日含10/12～16。交易日查詢不抽樣、不補休市K；其他分析日可CLI --as-of加算，UI不補算。下載graph-recognition-selection/0.1含完整原字串、source/frame/basis/prefix、核心版本／設定／反證；主圖約數不減JSON精度。

## 實際結果與未完成

- 本輪重新核3歷史ZIP，bootstrap成功0補檔／7差異保留，沒有沿用Work準備失敗為成功；沒有重讀101圖片或重開舊樣式。
- **21項定向Python PASS；60個辨識前綴全量重算／60 oracle PASS；最終HTML115項真實Chromium HTTP PASS，72次精確JSON核對。** 四尺寸含原生滑鼠／觸控、逐記錄／同步／回放／源點／反證／刻度不遮按鈕。失敗及修正保留；不是舊全套或準確率。
- 1101預設89箱／171轉折／25研究前緣。1/27同價來源出現在兩尺度但3/4、3/20才確認；**人工4/7～6/2／39筆無完全同起訖自動匹配，2023-06～2025-04大帶未完整重現**。較細／較嚴設定會改變候選，無唯一主壓力／正式重要性權重。
- Raw完整公司行動／五年Adjusted／歷史公布可得、原來源缺口／Darvas正文／SQLite根因未知保持。五年高不是完整歷史高，量與箱不代表精確套牢持股或沉澱。沒有模型訓練、獨立市場準確率／全市場或交易用途通過。
- Android NOT_TESTED_NEW_BUILD；原file://政策阻擋未重試／未繞過。沒有改main、部署、付費、交易、訊息或子代理。

下一步用**Work**看新自動結果相對已答大帶／前箱的實際結構差異，貼WORK_HANDOFF全文。不重問已答日期／代表，不重做101原圖或0.4.3樣式。小ZIP是自足研究結果與latest JSON，不冒充完整source備份；source保存在指定分支。
