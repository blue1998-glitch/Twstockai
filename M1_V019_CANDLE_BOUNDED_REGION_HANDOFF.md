# 0.4貼合K線修正已實作（2026-10-19 Codex最新）

狀態IMPLEMENTED_DEFINED_RENDERING_SCOPE；下方READY_FOR_IMPLEMENTATION為原Work交接歷史。從指定570bfd4接續，獨立candle-region-chart-view/0.4，沒有覆寫原0.3／案例／來源／歷史。G2精確日期、136筆及影線35.90～40.25核實，量圖最高來源柱82,247,780股另框；這些只作display geometry，formal price_bounds／volume_measure保持null。G1九月近似錨以虛線未閉合左緣顯示，精確起日仍null；C後無封閉外框／固定終點。影線與量柱範圍只在各自pane裁切，不跨MACD、不拉伸價軸、不以可見子窗重算。

[新成品／SHA／ZIP／遠端下載核對／完整Work指令](deliveries/m1-v019-candle-regions-v04-20261019/README.md)；[實作契約與重現](股票系統M1_v0_18/candle_region_chart/README.md)；[本輪實測／前後原尺寸畫面／失敗及未測](股票系統M1_v0_18/candle_region_chart/validation_20261019/驗收報告.md)。主下載schema manual-region-chart-selection/0.2另加region_display；原manual_regions／manual_hurdles、OHLCV、SMA／MACD及其他舊欄位值不變。指紋、代表點、同步查詢／移圖、分析日／前綴、草稿與軸內外提示已回歸。

本輪實際398 Python（含15新外框資料測試）、真實Chromium208 HTTP／44標籤／55操作／32外框均PASS；既有file://政策阻礙照記未重試，HTTP不是全環境或Android通過。244源檔／4854新Raw及1490原frame、50oracle與凍結0.3全欄位核對、ZIP CRC及逐檔SHA已實測。最初測試匯入順序失敗保留，修正後通過；沒有策略／資料錯誤證據或新增門檻。

**新0.4 Android NOT_TESTED_NEW_BUILD**；0.3-family兩張原圖與不確定身份紀錄保留，不重索；0.2原部分證據保留。下一步Work只驗新版影線外包、量框分離、MACD無區域填色、縮放裁切不假貼邊的差異。不是重新驗整套手勢／草稿；只有必要手機新下載精度驗證才收本版新JSON。Core用途NOT_ESTABLISHED、策略／來源／Raw公司行動／Adjusted／歷史／缺口／SQLite與Darvas限制不變。不改main、部署、付費、交易、發訊息或啟動子代理。

---

# 價量區域貼合真實K線範圍：Codex修正交接（2026-10-19）

狀態READY_FOR_IMPLEMENTATION；本輪Work尚未改產品。沿blue1998-glitch/Twstockai、dev/m1-v018-chart-annotations；目前讀取基線996dbdec068918cf81b344234c12d77082a2750a，須保留本檔之後所有成果。原0.3成品31d80971b265942eb3d7573fddf00f6782f20a55不覆寫。

## 必讀與重現

讀AGENTS、CONTINUE最上方、本檔、PROJECT_VISION／VISUAL_RULE_NOTES最新節、region_chart README與原驗收、validation_android_20261019/evidence-0851.md及visual-review-0851.json／兩份原圖；保留原G1／G2案例及端點文件。完整checkout依AGENTS先bootstrap --hydrate-missing，失敗明示，不覆寫差異。
在0.3選1101／Raw新官方日線／分析2026-10-16，按G2價量帶：底色由price.top一路跨量圖至macd.bottom。使用者要求「標記真實的k線範圍區域，而不是將整個圖垂直空間框起來」。這是新增呈現要求，先前工程可通過而新呈現不獲接受；不用怪罪原資料或擅補策略。

已實讀的直接位置是region_chart/regions_viewer.js的drawRegionBands/span，fillRect及不確定斜線跨price.top～macd.bottom。由regions.py提供顯示索引，正式price_bounds／total_volume仍null。不要把unknown保護測試刪掉，應另外保存顯示幾何。

## 具體實作

1. 新獨立版本／新入口／小ZIP，不覆寫0.1／0.2／0.3或原JSON／證據。以清楚細框／低透明底色標記**所選真實K線的日期×價格範圍**，僅在價圖內；上下含影線，不用收盤或K實體漏掉真實最高低，也不能用整個畫面最高低代替所選段。
2. G2採已核2023-01-16～2023-08-16含端點原交易記錄。Work原檔重核136筆、最高40.25(5/2)、最低35.90(1/17)。以此為可逆顯示外包框是助手實作選擇，**display_extent與formal price_bounds分開**；不是正式壓力價格區界已定為35.90～40.25、不是每個價位均成交或剩餘持股分布。仍保持原代表點5/2／40.25，價軸不因圖框額外拉伸。
3. 由獨立producer／準備層提供來源可追溯顯示extent或必要原列索引，瀏覽器只做座標映射／裁切。精確數字保留原字串／Decimal，比較不破壞儲存精度。正式未知欄位保持null，舊schema／數值payload及原case bytes不變。
4. 整個已選段的顯示上下限在平移／放大／裁切時保持，不因當前可見子窗另取高低而跳動；被裁出畫面的真實界線不假貼邊當新價位。不要為外框擠掉K線／軸刻度／來源標籤／縮放鈕。日期左右邊界對齊實際起終日K寬。
5. 若保留量圖區域，按**同段實際量柱**另行框／底線／弱底色，限制在volume pane，零基線到該段真實最高柱的顯示高度，不把單日量當整區量／策略最大量。K與量框各自獨立，不用連續色帶穿過MACD；MACD只保留原指標與查詢游標，不用價格／量區域塗滿。量缺值不造0或假高度，顯示資料不足；原真0與缺值分開。
6. G1仍約2023年9月至C(2024-01-19)，起日null。沿原資料的display month anchors呈現近似外包範圍時，九月為未定起緣（柔化／虛線等），不能硬定9/1正式歸屬、算正式整區量或把近似外框價位寫進pressure bounds。原11/28／35.50、9/14同高與10/18／11/30原日量保留。若某種包框需要假定精確日期，改用清楚未閉合近似邊界，不造確定結果。
7. C後終點未定仍開放參照，不將閱讀窗4/26／4/30當區域終點，不把全部後續K自動分類為新平緩帶。沒有完整起訖時不畫假封閉確定箱。原人工覆核資格及來源指紋保持。
8. 保留查詢／移圖模式、同步K量MACD、日期前綴、24月486與分析10/16、端點證據、草稿未提交／逆序與清空、原①④／G3五日及軸內外標籤。查詢白點與人工來源點仍分開，不因框形修正改策略。

## 實測與交付

- 定向資料檢查：G2 extent只取真實選段（含兩端），窗口外更高低不納入；滾動裁切不重新選段；G1未知、C開放、不匹配來源／日期不套、量缺值及舊case／引擎／payload不變。顯示extent不變成正式price_bounds或強度公式。
- 最終HTML實際Chromium HTTP在390／320直向、844橫向及桌面查看G2／G1；實際截圖目視框上／下影線、量圖獨立與MACD無色帶、低透明不遮K／刻度／線標籤／＋−，測聚焦／縮放／平移裁切與查詢不改分析日。原file://拒絕未重試／不繞過，雲端不是Android。
- 跑與變更相稱必要Python／瀏覽器回歸及下載oracle，報告實際數／最終HTML SHA，不複製前版383／208／44／55為新通過；新JSON若增加display_extent須另契約版本且完整精度。
- 保存真實修正前後畫面、失敗／未測、新HTML／ZIP、SHA／CRC／讀回收據與文件同分支並確認GitHub；新手機起始NOT_TESTED_NEW_BUILD。返Work只驗新的外框呈現差異，已收0.3原圖保留不重索；若驗手機新JSON下載才收新版新檔。
- 新Android證據是0.3-family PARTIAL_EVIDENCE_OBSERVED_VERSION_UNCONFIRMED（兩張無版號頁頂／HTML指紋），不是全通過。G2端點證據、手勢、橫向、草稿未由此驗到；既有file阻擋、來源／Raw公司行動／五年Adjusted／歷史公布可得／資料缺口及SQLite根因保持。
- 結束給入口、最新SHA、實際完成／未完成與完整可貼Work指令。不改main、原引擎策略／庫／歷史／舊頁，不部署／付費／交易／訊息／子代理。一般可逆工程直接處理，不再追問G2已定日期或把UI修正當核心用途認可。
