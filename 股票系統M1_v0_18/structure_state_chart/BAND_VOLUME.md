# 明示研究帶的最大量對照（顯示0.3）

本輪只接明示候選的完整保存來源段；不是自動選箱、完整帶切段、密集量峰估計或主要壓力算法，不是公司來源0.11。原P0-3純核心0.1及顯示0.1／0.2、五份JSON、角色／狀態／事件／ID／原量／K／MA／MACD與人工模式路由保持。

## 對照後真正缺口與重用

|既有程式|本輪處理|
|---|---|
|graph_core/core.py `_volume`／保存candidate.volume|原研究候選已有最大量／同量日、來源根數與缺量資訊；只讀保存值核對，未重跑analyze、_volume、選箱或參數|
|pressure_chart/facts.py `volume_facts`|直接重用其完整段最大單日量與全部同量日；返回的總量不拿作代表量線|
|candle_region_chart/extents.py `envelope`|重用來源極值／缺量與同量日核對；沒有另做最大量算法或把顯示外包升正式箱界|
|reaction_facts/core.py `compare`、source.py `make_input`|重用精確ABOVE／BELOW／EQUAL／差額及code/source/basis/frame/prefix指紋驗證，不改原函式|
|新增reaction_facts/band_volume.py|只補明示候選、完整成員、可知時間、來源完整資格及既有helper一致性；純函式無UI／IO／時計|

原程式沒有同等「明示候選完整段＋候選／量參照可知＋目前量精確對照＋主圖／下載」接線，故有本輪工程實益。沒有平行最大量估計器。原最大價K與最大量K分開，不排除異常量，不用可見圖窗代替完整來源。

## 有限輸入與輸出

`explicit-research-band-volume-selection/0.1`明示candidate_id、來源／股票／基底／frame／prefix binding、價格模式／版本、完整member_dates、reference_known_on、實際selected_at及RESEARCH_CANDIDATE資格。真實案例選取檔在examples/band-volume-selection.json，繼承既有P0-3研究候選ID，但量查詢有本輪新選取時間；原角色選取檔未改。生產程式不寫死股票、日期、數量或答案。

`prepare(data, selection)`重用make_input核原comparison與core指紋，解析明示保存候選，核完整範圍／根數。`evaluate(payload, as_of=...)`只讀所選截止前資料，回傳：

- analysis_as_of、同源／基底／版本／股數單位、已分析prefix指紋；後來選取原artifact binding另標LATER_SELECTION_ARTIFACT_NOT_HISTORICAL_FRAME，不能冒歷史已選frame。
- reference：研究候選ID、完整保存來源起訖、預期／實際成員、原指紋、最大單日量／全部同量日與各原K，完整原始155列可追溯。formal_price_bounds與formal_region_membership仍null。
- comparison：分析日原量相對最大量ABOVE／BELOW／EQUAL、完整精確差額及reason。相等不是嚴格越過，真零保留，缺量不補零；不產生買賣／成功旗標或重寫P0-3。
- 原量發生日、候選確認、量參照可知、實際後來選取分欄；historical_selection_time=null、historical_signal_eligible=false。保存Raw／歷史公布可得等舊限制。
- representative_volume_line.value=null、status=NOT_IMPLEMENTED，原因為量峰群組及視覺估計法未定；不借平均、中位數或固定比例。

缺成員日／已知待核日曆缺口／缺量／未完整可知／原段指紋或helper衝突、基底中斷就不提供完整段最大量，也不拿已知部分充數。分析日缺量或來源段至分析日間有待核缺日可保留合格原段參照，但比較不可用。直接來源／基底／版本不符、非法選擇或宣告指紋遭竄改明示拒用。完整是**明示保存成員完整**，不是官方市場交易日曆及公司行動已完整核實。

候選／參照當時尚不可知時整個reference=null，不提前露完整帶最大量、同量日或來源列。追加或修改截止後數值不改舊參照／比較／當日原量／已分析prefix；後來選取來源整檔binding metadata或result_id可因新版本而不同，不能冒稱整個來源版本也相同。日OHLC不推盤中先後。

## 主圖與實際案例

沿固定顯示0.2主圖加入「完整研究段最大量對照」，與原「前筆量觀察」分開。量圖紫虛線只表示本次明示來源段的最大單日量；不是密集量峰代表線。最大量來源在畫外仍保留參照，不假畫成當日來源；量軸外只提示，不改量軸／錯貼高度，線不穿MACD。來源抽屜保留全部同量原K及完整來源列，定位不改分析日。

1101 Raw／B88來源2025-11-19～2026-07-14共155根；最高日量2026-01-12的98,217,134股，原K開23.85／高25.10／低23.80／收24.95。這與原突破研究高26.95的1/27不是同根K。10/16原量57,437,884股，BELOW、差額-40,779,250股；只是尚未越過，不判壞，不取消當日轉強。10/12量可高於最大量，但返回角色仍未知而P0-3不足，原突破仍保留。10/13整理→14轉強→15整理→16轉強完全不變。B88仍研究候選，非核定正式原箱／完整帶。

## 工程重現（一般查看直接用GitHub新PNG）

根依AGENTS bootstrap後，在股票系統M1_v0_18：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_explicit_band_volume.py -v
PYTHONDONTWRITEBYTECODE=1 python3 -m structure_state_chart.build_volume --output-dir structure_state_chart/output/NEW_EMPTY_LEAF --selection structure_state_chart/examples/band-volume-selection.json
BAND_VOLUME_DIR=structure_state_chart/output/NEW_EMPTY_LEAF BAND_VOLUME_EVIDENCE=structure_state_chart/validation_band_volume_20261024/NEW_RUN node structure_state_chart/test_band_volume.cjs
```

沒有網頁也可直接呼叫純prepare／evaluate；建置才做標準庫外部JSON讀寫，UI只查已保存結果與像素轉換，不算參照／量關係。不同現有輸出拒覆寫。HTML自含、不需行情網路；瀏覽器測試只臨時127.0.0.1 HTTP，不部署，不重試file://。Android NOT_TESTED_NEW_BUILD。

本輪實測數、失敗／修正、PNG與封包收據見validation_band_volume_20261024及root deliveries/m1-explicit-band-volume-20261024。無新來源GET、graph_core／P0-3／指標／每日淨帳／六方案／績效重算。全部原來源0.10及parent、庫、Raw null／UNKNOWN、舊成品、main、Fontconfig／xref警告與來源／個人權利缺口保持，不建0.11或catalog、不回寫null、不公開私人原件、不補行情／零／前價／估值，不重試受拒入口。

execution_qualified=false；imputed_close／valuation=null；historical_signal_eligible=false；primary_pressure_id=null；policy_authorized=false。最大量工程不等密集量峰、全自動完整帶、主要壓力、全市場、換股或資金飛輪完成。不部署、付費、交易、訊息或子代理。下一步只Work做新圖用途差異檢視。
