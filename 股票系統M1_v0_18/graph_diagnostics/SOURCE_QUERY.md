# 既有診斷的單一來源反查 0.1

`source_query.inspect_sources(result, query)`直接讀已保存graph_core結果的完整pivots／boxes，不改diagnose輸出，不呼叫diagnose、analyze、_pivots、_boxes或MACD。純函式無I/O／內建時鐘。這是來源引用與明示切片工具，不是第二套辨識、整體歸屬或主壓力選取。

## 執行

先在repo根按AGENTS實跑 `python3 codex/bootstrap_m1.py --hydrate-missing`，成功後於 `股票系統M1_v0_18/`：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_source_query.py -v
PYTHONDONTWRITEBYTECODE=1 python3 -m graph_diagnostics.source_query_cli --input cross_scale_chart/generated/comparison-data.json --query graph_diagnostics/source_query_examples/request.json --output graph_diagnostics/output/my-source-query.json
```

請用新的output葉檔，不覆寫舊報告。CLI在**每次實際查詢**生成帶時區selected_at，例檔的null只供CLI填入；純函式則要求明示時區時間，不自己讀時鐘。要逐值重現已保存報告，將其完整query傳回inspect_sources／inspect_packet（同一selected_at）；再次CLI查詢會得到新時間與report_id。既有publish_immutable拒絕不同bytes，不覆寫用戶檔。

## 輸入與驗證

請求schema=`graph-source-query-request/0.1`，必含binding、pivot_ids、path_requests、selected_at。binding由 `binding_for(result)` 取得，含精確result_id／source_prefix_fingerprint／完整context；不能混用其他股票、基底、來源或前綴。pivot_ids不得重複；path_requests每筆只能有from_id／to_id，不能省略終點、自動猜下一點、加入人工月份或價位條件。同一ID作兩端為一點明示路徑，倒序則拒絕。

純函式核原schema／result指紋、pivot ID原生欄位指紋、確認資格、索引及時點／完整有序source_dates、原箱ID與全部來源引用／序位／同尺度同段連續性。確認晚於as_of、未知／未確認ID、錯序或混合來源明確拒絕；沒有重新辨識或證明原研究演算法的效用。轉折／箱ID不是外部簽章；自洽fingerprint不認證行情或真實歷史公開可得時間。

`source_query_adapter.inspect_packet(packet, query)`額外核既有artifact／core、原OHLCV前綴與context，**重用原graph_core._validate**作來源驗證，逐原轉折核真實K日期／欄位／完整同價source_dates與確認索引、原箱來源rows指紋、MACD序列軸。它不重算確認／MACD或新反應事實。

支援既有 `cross-scale-real-chart/0.1` 及保存的 `graph-recognition-chart-bundle/0.1`／`graph-diagnostic-chart-bundle/0.1` JSON。bundle只選binding指定result_id，缺少或不唯一即拒絕，不選latest、不檢查／回寫其他未選前綴。追加或改未選未來封包不改所選舊前綴報告。comparison只含一個原core，不能憑此選不存在的歷史結果。內嵌diagnostics若為摘要，輸出明示SUMMARY_ONLY；完整診斷也不在本查詢重算或重驗diagnostic_id，不能冒稱完整診斷驗證通過。輸入JSON必為實際核過的原封包，外部來源真偽仍需各自證據。

## 輸出

schema=`graph-source-query/0.1`，含原result/context/prefix、原研究參數／資料資格、完整query及report_id。新報告不更動任何原ID／數值／schema。

- `requested_sources`只對明示pivot_ids反查全部原箱引用及0起算source_turn_position、1起算原箱編號，不按月份裁箱。`boxes`保存這些原箱起末／確認／尺度／完整來源ID及原research_bounds，沒有整體成員批准。
- `coordinate_correspondences`要求同segment、種類、發生日、精確Decimal價值、**完整有序source_dates**全等；保留不同原ID及各自確認。價位字串尾零不影響精確數值相等；只有同價、同日或同確認不夠。對照不合併、不獨立計票。
- `paths`是同scale／segment原有序轉折的含端點完整子序列，所有中間點保留；提供sequence_records／records_before／records_after作背景，不自動延伸或決定正式起訖。跨尺度座標對照另列，不跨尺度拼路徑。
- `not_before_original_confirmations`：路徑取所有來源確認最大值，座標對照取雙方較晚確認，原箱引用保留箱及來源確認下限。這些是原保存確認的下限，歷史公布可得仍未核，不能回填成歷史選關。
- `pivots`按原ID提供完整記錄，含明示點、其對照／原箱來源及路徑中間點；**不對額外點遞迴反查箱**。每條關係仍保留原ID，不因座標相同刪除。

historical_selection_time=null、historical_signal_eligible=false；primary_pressure_id及正式成員／合併／代表／直接承接／整體解除null，重要性／生命階段UNKNOWN。原確認／來源末點不當人工整體終點。原89版本／84幾何不是獨立型態；價格重疊、相鄰路徑、共同來源不直接認證大帶、父子或承接，沒有傳遞閉包聚類。

本輪新工程無UI、圖表或reaction_facts變更，無新瀏覽器／Android驗收；Android NOT_TESTED_NEW_BUILD，file://不重試不繞過。保留Raw公司行動／五年Adjusted／歷史可得／九待核非窮盡日曆／Darvas／SQLite未知，原五月十月反例、拒絕餘量、相等與日OHLC限制、核心NOT_ESTABLISHED／分類NOT_VALIDATED／行動NOT_EVALUATED。例檔日期價位／編號只作既有fixture，不進生產常數。

[本輪實測](source_query_validation_20261020/驗收報告.md)、[成品／完整Work交接](../../deliveries/m1-v019-source-query-20261020/README.md)。工程完成不代表正式整體歸屬或主壓力辨識完成。
