# 多參照反應事實附層 0.1

獨立純數值函數 `core.evaluate(payload, as_of=...)`，不讀寫檔案／網路／資料庫、不呼叫任何分析或MACD引擎。`source.make_input(comparison_data, selection)`只讀原跨尺度圖契約並核指紋，依**明示來源選擇**組輸入；不用人工audit，不自動選關。CLI只做外部檔案讀寫，舊schema、圖表、參數、核心、來源、結果ID、庫及歷史不變。本輪沒有新增UI。

## 可用來源與使用

先在repo根依AGENTS執行 `python3 codex/bootstrap_m1.py --hydrate-missing`，成功後於 `股票系統M1_v0_18/` 執行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_reaction_facts.py -v
PYTHONDONTWRITEBYTECODE=1 python3 -m reaction_facts.build --data cross_scale_chart/generated/comparison-data.json --selection reaction_facts/examples/selection.json --as-of 2026-10-16 --output reaction_facts/output/my-query.json
PYTHONDONTWRITEBYTECODE=1 python3 -m reaction_facts.verify --data cross_scale_chart/generated/comparison-data.json --selection reaction_facts/examples/selection.json --result reaction_facts/output/my-query.json
```

例檔是**本次後來明示查詢fixture**，四個來源分別是原B77研究低界、指定完成K原高、原B88研究高界、另一完成K原高；沒有選關演算法。重新選取請另存新selection、記實際帶時區的 `selected_at`（不知道就null），不要把例檔本輪查詢時間改寫成歷史當時已選參照的證明。日期／價位只在例檔、測試及交付資料中，不在生產算法中。其他相同契約資料可明示查詢，但未作跨股統計／準確率驗證。

`explicit-reaction-reference-selection/0.1` 必含binding（code/source_id/price_basis_id/source_frame_id/source_prefix_fingerprint）及references。選項為 `{kind:"BAR_FIELD",date:"供應日",field:"open|high|low|close"}` 或 `{kind:"RESEARCH_BOUND",box_id:"原ID",field:"high|low"}`。不接受無來源任意價、manual audit或自動選擇。參照ID綁selector與來源，不把同價不同來源合併。對外CLI接受原 `cross-scale-real-chart/0.1`，核原artifact／core／bars前綴及選取binding；純函數低階輸入另為 `reaction-facts-input/0.1`，應由此adapter建立。研究界依外部保存來源證據的confirmed_at，不回跑graph_core。

## 輸出與精度

`multi-reference-reaction-facts/0.1` 保存全部原記錄、MACD及來源身分。每筆 `references[ID].fields.close/high/low` 各有ABOVE／BELOW／EQUAL、精確delta、相鄰三態轉換；`records`是完整位置路徑，`transitions`只是索引，從不刪除跌回。經相等只記ABOVE_TO_EQUAL／EQUAL_TO_BELOW等，不捏造直接ABOVE_TO_BELOW。沒有有效突破或成功／失敗交易評分。

`body`比開盤，`adjacent.close`比前一保存收盤，兩者可方向相反。`adjacent.high/low/range_direction/range_geometry`僅相鄰Raw記錄幾何，不是確認波段、正式跳空或壓力牆。`volume`保留原股數、前一保存記錄日期／股數及排除當日的描述比，不新增5／20或量增門檻；缺量、零分母不填0／無限。重用原graph_core的number／fingerprint／ratio；舊volume_observation的前1等價口徑另有對照測試，沒有修改舊函數。舊trace_reference只追close且相等後會依其舊語義命名，不能直接代替新三態多欄位路徑；舊函數與結果保留。

所有原值、有限十進位差值保存完整字串，方向比較不用float。前量比通常是無限小數，以原ratio的**50位有效數、ROUND_HALF_EVEN**保存，原分子／分母同存，不能把商當無限精確值。MACD完整原字串／null／原reason保留，另列原值對0、前一保存原值的比較，不重算指標。純數值結果不因顯示近零抹去負號。副程式不依全域Decimal精度或捨入模式改答案。

## 時間、缺口與未知

每參照分開 `occurred_at`、`known_on`、`selected_at`、`historical_selection_time`。known_on只表示供應完成日或原候選確認日的**保存序列資格**，不是已驗實際市場公布時刻；selected_at是本次後來選取，不證原歷史已選。`historical_signal_eligible`永不為true。早於known_on關係NOT_AVAILABLE；as_of尚未可知參照不輸出price。對as_of截短或追加／修改未來，既有records／transitions不回寫；來源全檔／frame／binding前綴可能不同，不能要求來源metadata也假裝相同。

MACD按原保存等長序列索引綁定，原有date若提供必相符，不製造日期。可用低階row.known_on表達延後可知記錄，當日未可知不能產生可用比較；原值留存供溯源，不當歷史訊號。

缺價格只讓相關欄位未知並斷開該路徑；恢復後SEGMENT_START。已知／待核日曆缺口保守切相鄰比較、量比及轉換，沒有假K，不證該日必為缺失交易日；原九待核與非窮盡日曆完整帶出。basis_break_dates使早於中斷的參照不可繼續比較，不因後續有價而恢復；新同源參照須另有來源。錯來源／基底／frame／前綴直接拒絕；日期重複／倒序、不完整K、非有限／float輸入拒絕，不偷偷整理。

primary_pressure_id及整體解除／有效突破保持null；正式區界、量口徑增量、強度衰減、重要性、合併直接承接、生命階段未知。Raw公司行動、五年Adjusted、歷史公布可得、九待核日／資料缺口、Darvas正文及SQLite根因未知保持；89版本／84幾何非獨立型態、不同後續窗不公平排名。日OHLC不能證日內先後、次數或回測完成。核心NOT_ESTABLISHED、分類NOT_VALIDATED、行動NOT_EVALUATED。

新Android **NOT_TESTED_NEW_BUILD**；file://不重試不繞過；無UI變更，本輪無瀏覽器回歸／手機驗收，不沿用舊7／47等數字。本輪實際驗收見 [報告](validation_20261020/驗收報告.md)，[成品及完整Work續接](../../deliveries/m1-v019-reaction-facts-20261020/README.md)。
