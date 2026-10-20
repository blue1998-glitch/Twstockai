# M1 既有診斷單一來源反查 0.1

已新增既有graph_diagnostics內的純數值來源反查、原封包adapter及CLI；沒有新UI、圖表、反應事實或自動大帶合併。

- [下載／讀取查詢JSON](../../股票系統M1_v0_18/graph_diagnostics/source_query_generated/source-query.json)：30,584 bytes，含原結果／context／完整query、17個原轉折、8個原箱來源、3個明示點的箱引用與座標對照、一條完整9點路徑。
- JSON SHA256：`4a43a8c0f03bbffacb86306f064b7c807a7a83bdaf7e737bc76cd654a2c1dbb0`；[來源與逐值核對](../../股票系統M1_v0_18/graph_diagnostics/source_query_validation_20261020/verification.json)。
- [明示request例檔](../../股票系統M1_v0_18/graph_diagnostics/source_query_examples/request.json)、[模組契約／CLI](../../股票系統M1_v0_18/graph_diagnostics/SOURCE_QUERY.md)、[實測報告](../../股票系統M1_v0_18/graph_diagnostics/source_query_validation_20261020/驗收報告.md)、[完整Work續接](WORK_HANDOFF.md)。

[沿用原真實互動圖入口](../m1-v019-cross-scale-real-20261020/README.md)，本輪沒有新HTML或樣式驗收。

原A點反查B16／B17／B18及全部原source_turn_ids，保留六月前來源與40.25，但不認定為人工大帶成員。例檔另查10/24、11/28原3%來源，列同座標6%原ID及各自較晚確認，不合併或獨立計票。9點路徑保留全部中間點及末段反彈；119點／前33後77只是原完整序列背景，不是自動起訖或接續規則。

每次CLI實際記selected_at；原發生／確認、關係not_before_original_confirmations與後來查詢時間分開，historical_selection_time=null、historical_signal_eligible=false。comparison內diagnostics只有摘要，明示未驗完整diagnostic_id。fingerprint與原K核對是來源自洽驗證，並非外部行情或歷史公開可得認證。

本環境重新bootstrap成功（0補檔／7差異保留）；新14項Python契約測試PASS，CLI／精確JSON再讀與衝突拒絕實測；固定原診斷ZIP CRC／SHA、原bars／MACD／SMA／source／basis／core／manual audit逐值核對。原系統、reaction_facts、圖表及策略參數保留。不重跑舊22／47／35／60等套件；無新瀏覽器／Android測試或ZIP，舊包不改。

primary_pressure_id=null；正式成員、整體區界／代表、重要性衰減、量權重／增量、合併直接承接、解除及生命階段未知。Raw公司行動／五年Adjusted／歷史可得／九待核非窮盡日曆／Darvas／SQLite未知保持；核心NOT_ESTABLISHED／分類NOT_VALIDATED／行動NOT_EVALUATED。Android NOT_TESTED_NEW_BUILD，file://不重試不繞過。

下一步 **Work** 用可查來源研究正式整體歸屬；工具完成不等主壓力辨識完成。不重問三個已確認概念或舊案例，不因未挑戰舊帶高點前的低位整理先降本例重要性。不自動串接／合併／排名，不將39.25／35.50／35.45／40.25指定整體代表。不改main，不部署付費交易訊息子代理。新成品固定提交及逐檔GitHub回讀收據另由後續交接保存。
