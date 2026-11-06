# 獨立密集量峰候選研究

這是新的有限研究實作，與正式產品分離；沒有接UI或改原band_volume.py。`core.evaluate(payload, config=...)`是無IO／時計的純數值函式；`build.py`才讀庫內小型月原件並保存新結果。正式`representative_volume_line`永遠`NOT_IMPLEMENTED/value=null`。

重用既有`reaction_facts.core.BINDING/compare/day/timestamp`、`graph_core.core.fingerprint/number`與`pressure_chart.facts.volume_facts`；最大量及全部同量日直接由原helper提供，不呼叫原graph分析、P0-3、band_volume或指標producer。原`reaction_facts.source.make_input`／band_volume.prepare依賴完整comparison/core大檔，故本輪不呼叫它們或重取大檔；新外部adapter使用相同binding欄位與指紋函式建立明示小原料集合／截止prefix。原完整歷史artifact binding另存來源鏈，只作原案例連結，不假冒新source_frame等於舊frame、也不冒本輪重新驗證舊整包。

## 輸入與時間

見交付的`research-input.json`及本目錄`examples/request.json`：完整明示member_dates、candidate_id、原OHLCV數值字串、source/code/basis/mode/adjustment_version、`SHARES_REPORTED`、as_of、reference_known_on、actual_selected_at及必填config。k/r沒有預設值或最佳化；例檔九組僅使用者指定研究探針。

context的source_prefix_fingerprint只對所選截止prefix，selection.binding須完全相符。先切as_of再檢查；追加或修改截止後原K不影響該次結果，包括result_id。完整來源另有member_fingerprint，缺日、來源／基底／版本／單位衝突、基底中斷或指紋不符拒用。這些指紋是明示資料一致性檢查，不是獨立官方簽章或完整行動認證。

known_on前reference、群及峰均不輸出。之後保存原量日、右比較窗末記錄日、該窗所有原值可知後的確認日、群確認／可知日、來源評估截止、完整來源起訖，以及真正後來選取時間。Raw資料未單獨記known_on時沿既有「保存完成日記錄」日期語義作數值觀察；歷史公告可得仍UNVERIFIED，不能升歷史訊號。後來選取不倒填historical_selection_time。

## 研究規則及保守拒判

1. 非平台峰：當量嚴格大於左k筆最大值，且大於或等於右k筆最大值。只使用明示來源成員內記錄，不借來源外K補比較窗。右邊尚不足而已見條件仍可能成立，保留`PENDING_RIGHT_RECORDS`；左窗不足另列。每筆原K及判讀資格均保留。
2. 比較窗中等量的潛在頂部保留所有等量原日，包括相鄰及附近非連續同量；平台範圍／代表尚未定，不以`>左／>=右`偷偷取第一日。全群辨識`REFUSED_PLATFORM_AMBIGUITY`，仍保留原量柱、非平台診斷及合格原最大量比較。這是拒判資格，不是新平台辨識策略。
3. 只在已確認非平台峰中列舉所有不能再加入其他峰的群，精確條件`max <= min*r`。先按量及日期作列舉序，不作重要性排序；每個不同最小量找最遠可容納上端，若仍能向左擴張則不是最大群。所有相同端值原峰皆包含，單筆極大量群也保留。相鄰連鎖近似不代替整群跨度。輸出鄰接群外峰與不可擴張證據。
4. 全部群都輸出，不只最多票群；最多票群ID全留，不挑唯一贏家。票數是該群不同原峰日數，不是獨立反應／市場樣本數。重疊群另列共用日期，不能把各群票數相加當獨立反應。
5. 不生成均值、中位數或比例單線。各群只列min/max原值、全部端點同量日及所有原K；最新量對兩端及原最大量各自用既有精確compare保存ABOVE/BELOW/EQUAL與差額，未超原最大量不判壞、不取消價格過線。
6. candidate_anchor缺省null。只有明示精確群成員日期集合、該群原柱日期及有效實際選取時點才可標`PROPOSAL_NOT_APPROVED`，錯配另列拒用；正式代表線仍null。
7. 零／缺量／負值／非法精度保留原值並拒判完整來源群，不刪該日繼續推部分群或補零。若只有最新量缺漏或為零，可保留合格來源群但拒做最新量比較。已知來源缺日／基底中斷拒用；只保存成員完整，不認證官方市場日曆完整或Raw已共同校正。

有待確認右窗時，已確認峰集合的最大群仍可作當次研究候選，但不宣稱完整峰宇宙最終不變。真實k=3例來源尾端7/9仍少一筆右窗；不借來源外7/15補足、不改155根來源，診斷明示。

## 實際保存案例與重現

1101 Raw B88明示保存來源155根，2025-11-19～2026-07-14，參照可知9/1。formal_price_bounds／formal_region_membership仍null。k=3、r=1.15：21個確認研究峰、13個完整跨度最大群，其中全部5個最多票群各7筆；98,217,134股異常大量保留於單筆群及原最大量來源。它們不是13個獨立型態或5個獨立反應。

五群範圍43882131～49699249、44638336～50595969、45105494～51860722、46730970～52859340、48157632～54198777股。最後一群只有展示意義，未選為正式群或代表；10/16最新量57437884對其上端差3239107，對原最大量差-40779250，兩個事實並存。以上答案僅出現在案例、輸出、測試及文件，不在通用core／builder常數。

在`股票系統M1_v0_18`重現（一般使用者直接看GitHub JSON，不要求開終端）：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest volume_peak_research.test_core -v
PYTHONDONTWRITEBYTECODE=1 python3 -m volume_peak_research.build --raw-dir pressure_chart/data/history-20261018/raw --selection structure_state_chart/examples/band-volume-selection.json --request volume_peak_research/examples/request.json --out NEW_EMPTY_DIRECTORY
```

所有輸出拒覆寫。原料只讀庫內12月JSON／meta，核原SHA、URL及parse_twse_month之身份／月份／欄位；meta未記HTTP狀態就保留null，不假定200。原捕捉、當前local reuse observed_at、原角色選取及新研究選取分存，announced_at仍null。重建的source-lineage新本地讀取時點自然不同；研究輸入及九組純數值結果可逐byte重現。

本輪實測及離線包見root `deliveries/m1-volume-peak-research-20261024/`；Work沒有替Codex跑測試。合成反例另存並明標，不當市場樣本；無新UI，Android仍NOT_TESTED_NEW_BUILD，file://不重試。

原graph_core、reaction_facts/band_volume.py、P0-3、UI、指標、策略／資料庫／行情、舊產物及main不變。來源0.10及全部parent契約不改，不新增來源0.11或catalog，不回寫null，不重抓分片／大檔／舊來源／PNG／ZIP，不重開完整JSON讀取已結清項。全部受拒入口不重試或繞過，私人原件不公開，不補零／行情／前價／估值。

完整公司行動及個人權利等缺口、Raw／五年Adjusted／歷史公布／主檔／SQLite未知保持。execution_qualified=false、imputed_close／valuation=null、historical_signal_eligible=false、primary_pressure_id=null、policy_authorized=false；不跑每日淨帳／六方案、不宣稱辨識品質或獲利已驗。不部署、付費、交易、訊息或子代理。
