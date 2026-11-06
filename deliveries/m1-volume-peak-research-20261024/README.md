# 獨立密集量峰候選研究：九組探針、全部最大群與同票

本輪有實際新模組與可重現數值輸出，並非只新增文件收據。純核心在[volume_peak_research](../../股票系統M1_v0_18/volume_peak_research/README.md)，與正式產品分離；**正式representative_volume_line仍NOT_IMPLEMENTED/null**，沒有UI接入、預設／最適參數、買賣或績效旗標。原graph_core、P0-3、band_volume.py、指標、策略／庫／歷史及main不改。

## 查看新結果

- [全部九組摘要](artifacts/summary.json)：序號只為序列化，不是參數排名。
- [k=3／r=1.15完整研究輸出](artifacts/probe-08.json)：21確認峰、13不能再擴張群、全部5個最多票群各7筆，所有重疊與原始OHLCV／原量柱、端點、來源與時點都保存。
- [純輸入](artifacts/research-input.json)、[實際研究request](artifacts/research-request.json)、[12月原料來源鏈](artifacts/source-lineage.json)、[輸出manifest](artifacts/MANIFEST.json)。每個研究JSON均小於512KiB，無需重取舊大檔／分片。
- [六個合成反例](../../股票系統M1_v0_18/volume_peak_research/validation_20261024/synthetic-cases.json)：平台拒判、重疊同票、零／缺量、右窗待確認及極大量，明標非市場樣本。
- [本輪37項新測試log](../../股票系統M1_v0_18/volume_peak_research/validation_20261024/tests-final-37.log)、[執行與診斷](../../股票系統M1_v0_18/volume_peak_research/validation_20261024/execution.json)。舊32／88及其他歷史測試未重跑，31／36中間批不累加。
- [新離線來源／程式／研究包](M1_volume_peak_research_20261024.zip)、[SHA256](M1_volume_peak_research_20261024.zip.sha256)、[封包及新解壓數值重現](package-verification.json)。只含公開小原料及必要依賴，不包含舊ZIP／圖／大產品JSON。
- [固定提交逐檔原bytes收據](GITHUB_READBACK.md)／[JSON](GITHUB_READBACK.json)，在固定工程之後另存避免自指。

|k|r研究探針|確認峰|不能再擴張群|最多票群數|右窗待確認|完整結果|
|---:|---:|---:|---:|---:|---:|---|
|1|1.10|45|25|1|1|[probe-01.json](artifacts/probe-01.json)|
|1|1.15|45|20|2|1|[probe-02.json](artifacts/probe-02.json)|
|1|1.20|45|23|3|1|[probe-03.json](artifacts/probe-03.json)|
|2|1.10|32|18|4|0|[probe-04.json](artifacts/probe-04.json)|
|2|1.15|32|17|3|0|[probe-05.json](artifacts/probe-05.json)|
|2|1.20|32|17|2|0|[probe-06.json](artifacts/probe-06.json)|
|3|1.10|21|12|1|1|[probe-07.json](artifacts/probe-07.json)|
|3|1.15|21|13|5|1|[probe-08.json](artifacts/probe-08.json)|
|3|1.20|21|12|2|1|[probe-09.json](artifacts/probe-09.json)|

上述都是同一來源的研究參數版本，不能當九個獨立市場樣本，也不能按結果選一組升正式策略。全部群都保存，未以排序或貪婪去重選唯一贏家。

## 真實1101／Raw／B88對照

保存明示來源2025-11-19～2026-07-14共155根，reference_known_on=2026-09-01，formal_price_bounds／formal_region_membership=null。本輪真正後來選取時間另存request；不冒歷史當時已選或官方發布已知。

k=3、r=1.15的5個最多票群各7筆，範圍依次為43882131～49699249、44638336～50595969、45105494～51860722、46730970～52859340、48157632～54198777股。最後一群只是使用者展示對照；沒有單獨選它或設定anchor，所有5群candidate_anchor=null。

最後一群原日：2025-11-28、2026-02-02、03-05、03-20、05-29、06-08、07-01。10/16量57437884對其上端54198777為ABOVE／+3239107，對原最大量98217134為BELOW／-40779250。兩者並存，不產生好壞或突破成敗。原最大量1/12及全部155原K保留，異常量不刪除或降權。共用柱不能把5×7當35個獨立反應；group overlap_pairs有原日期。

k=3來源內7/9尚少一筆右窗，保持PENDING_RIGHT_RECORDS；左邊不足也另列。13群只對這個已確認峰集合做完整跨度列舉，不宣稱最終完整峰宇宙。沒有借來源外7/15資料或改155根成員。

## 驗證與界線

本輪37項新測試PASS（33合成工程方法＋4真實保存來源方法）；包含全部最大群的獨立窮舉子集合oracle、同票／重疊、平台拒判、異常量、零／缺量／來源及基底衝突、精確邊界、可知時間與整個結果的未來前綴隔離。也測原料／meta竄改拒用、純核心不做IO或呼叫舊graph分析。這不是辨識品質或市場績效驗證；合成案例不算真行情。

既有原碼／資料未變，舊helper透過本輪新測直接覆蓋；沒有重跑舊32／88、全套測試、數值producer、P0-3或指標。無新UI，沒有瀏覽器／Android驗收；Android NOT_TESTED_NEW_BUILD、file://未重試。原圖10張、五JSON及完整band-volume讀取已結清並沿用，不重新取得或驗證。

來源0.10及全部parent、不回寫null、不新增來源0.11／catalog；全部來源與個人權利缺口、Raw／五年Adjusted／歷史公布／主檔／SQLite未知保持。execution_qualified=false、imputed_close／valuation=null、historical_signal_eligible=false、primary_pressure_id=null、policy_authorized=false。私人原件不公開，不補零、行情、前價或估值；受拒入口不重試或繞過，不跑每日淨帳／六方案，不稱獲利已驗。不部署、付費、交易、訊息或子代理。

## 下一步只Work

全文可貼指令見[本輪接續](../../M1_VOLUME_PEAK_RESEARCH_HANDOFF.md)。只唯讀檢視本輪新研究輸出及未定資格，不重跑測試、不重抓舊來源／圖／ZIP或重開已結清讀取。明確研究輸出缺陷交回原唯一Codex，不另開工程／子代理，不強迫選單線或把參數當正式策略。
