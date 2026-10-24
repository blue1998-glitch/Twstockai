# 獨立密集量峰候選研究已實作：只交Work看有限研究結果

分支`dev/m1-v018-chart-annotations`，起點`3b6fe93fe582ba943451374491f081f23af42f59`；固定結清`0df19d88abb20ae89b9082beb42433de9c394225`及全部後續保留。固定本輪工程與最新已核SHA見最終回覆及`deliveries/m1-volume-peak-research-20261024/GITHUB_READBACK.md／JSON`，收據另存避免自指。

## 本輪完成

新增`股票系統M1_v0_18/volume_peak_research/`：純數值core、庫內小型月原件adapter／builder、明示九組request、37項新測試、獨立合成反例、來源鏈／診斷及可重現離線包。重用binding欄位、原fingerprint、compare與volume_facts最大量／全部同量來源。因舊make_input／band_volume.prepare依賴大comparison/core檔，本輪不讀它們；新明示小原料binding與原案例artifact連結分開，不冒同一frame或本輪重新核全史artifact。沒有改graph_core、P0-3、原band_volume.py、UI／指標／策略／庫／行情或舊產物。

完整明示來源內非平台峰嚴格大於左k且大於等於右k，右窗不足保留待確認；左邊不足另列。等量潛在頂部保留全部原日，平台規則未定就拒判完整群，不用首日替代。群依完整跨度max<=min*r精確列舉全部不能擴張的集合，不用相鄰鏈近似、貪婪去重或唯一贏家。全部群及所有最多票ID、重疊共用日期、原K／原量、min/max端點、確認／可知／實際選取時點、來源截止、maximality證據及精確比較保留。共用柱不算獨立反應；不刪極大量，不生成平均／中位數或比例單線。

正式representative_volume_line=NOT_IMPLEMENTED/null。明示合法原柱anchor才可PROPOSAL_NOT_APPROVED，真實九組沒有提供anchor所以全null。k=1/2/3、r=1.10/1.15/1.20僅明示研究探針，沒有預設、最適化、正式壓力解除或交易旗標。

真實1101 Raw B88保存155成員／2025-11-19～2026-07-14，reference_known_on=2026-09-01；正式區界及成員資格仍null。k=3、r=1.15重現21確認峰、13最大群，其中5群各7筆，全部保留。5範圍43882131～49699249、44638336～50595969、45105494～51860722、46730970～52859340、48157632～54198777股。最後一群只是展示，不是正式選取；10/16量57437884對它上端差+3239107、對原最大98217134差-40779250。原極大量及完整原柱保留。7/9在k=3仍少一筆來源內右窗，保持待確認，不能把21確認峰稱最終完整峰宇宙，也不借來源外K補。

本輪實跑37項新測試PASS（33合成工程方法＋4真實保存來源方法），31／36中間批及新解壓重現不重複累加。涵蓋同票、重疊、最大群獨立子集合窮舉、平台／異常量／零缺值、來源與基底衝突、精確邊界、時點／前綴隔離、原料及meta竄改、純核心無IO／不呼叫舊graph analyze。只做新研究所需驗證，舊32／88及全套／producer／指標未重跑。真實月份meta部分未記HTTP，保留null，不補200；原捕捉與本地重用時點分存，不倒填announced_at。初期只讀搜尋的錯路徑及修正留在execution.json；沒有失敗測試。

## 限制與交付

入口`deliveries/m1-volume-peak-research-20261024/README.md`，九組完整JSON／input／source-lineage／summary／manifest及新ZIP／SHA／package-verification均在該目錄。純核心可無網頁執行；無新UI或手機驗收，不要求使用者搬檔、終端或架伺服器。

未取得／未讀：沒有收到Work獨立研究檔，本輪由原庫內小原料重現；其他舊來源／私人權利／Work研究包缺口不解除。完整band-volume讀取已結清，不再列待補或重取原檔／分片。未實作：正式單線、平台自動分組、全自動完整帶／主壓力／全市場或換股飛輪。未執行：原來源GET、舊大檔／blob／PNG／ZIP重取、舊驗證及producer／指標、每日淨帳／六方案。未測：辨識品質、獲利及新Android；NOT_TESTED_NEW_BUILD不升格，file://不重試。未讀回：本輪固定工程逐檔原bytes另存收據，未取得舊封包不冒已讀回。

來源0.10及全部parent、Raw null／UNKNOWN、策略／引擎／庫、P0-3事件／ID／角色、歷史／舊成品／main及警告保持，不建來源0.11或catalog、不回寫null。完整公司行動／指定期間權息、個人實配畸零／既有2884換股影響、台泥最後調整／最細稅源、個人淨額及九起點權利等缺口保持；Raw／五年Adjusted／歷史公布／主檔／SQLite未知。私人原件不公開、不補零／行情／前價／估值；所有既錄受拒入口、library及嘉新逾時路徑不重試或繞過。execution_qualified=false；imputed_close／valuation=null；historical_signal_eligible=false；primary_pressure_id=null；policy_authorized=false。全換／分批仍研究變數，不宣稱辨識品質或獲利已驗。

## 完整可貼Work指令

```text
接續blue1998-glitch/Twstockai，分支dev/m1-v018-chart-annotations。
使用Codex本次回覆的固定研究工程及最新已核SHA，先唯讀核包含兩者、3b6fe93fe582ba943451374491f081f23af42f59、0df19d88abb20ae89b9082beb42433de9c394225及全部後續；保留成果，不回退、強推或用main／舊ZIP覆蓋。只由原唯一Codex處理工程與GitHub寫入，本輪Work唯讀，不另開工作／Codex或子代理，不bootstrap、工程、測試或commit／push。

讀根最新AGENTS、CONTINUE_IN_WORK_MODE、PROJECT_VISION、M1_V019_GRAPH_CORE_RESUME_HANDOFF，全文讀M1_VOLUME_PEAK_RESEARCH_HANDOFF.md、股票系統M1_v0_18/volume_peak_research/README.md／core.py／build.py及validation_20261024/execution.json、tests-final-37.log、synthetic-cases.json；讀deliveries/m1-volume-peak-research-20261024/README.md、artifacts/summary.json、research-input.json、source-lineage.json、probe-08.json，以及package-verification與GITHUB_READBACK MD／JSON。其他八probe按需要實讀，未讀不可說全部九完整物件已核；不能只靠摘要冒完整probe已讀。

只檢視這次有限研究輸出：非平台峰／平台拒判、所有不能擴張的完整跨度群、全部同票及重疊共用柱、全部原量和極大量、來源與時點、最新量對群兩端及原最大量的獨立精確比較。k/r是研究探針，不選最佳或正式單線。真實k=3、r=1.15有21確認峰／13最大群／5同票群各7筆；7/9仍缺一筆來源內右窗，不冒最終完整峰集合、不借來源外補齊。最後一群僅展示，不能只留它；共用柱不當獨立反應或市場樣本。candidate_anchor真實結果全null，正式representative_volume_line保持NOT_IMPLEMENTED/null。不要重問已答P0-4，不新增平台、箱界、量倍數、比例、天數或主壓力規則。

本Codex最終37項新測試PASS，中間31／36及新解壓重現不相加，Work沒有替跑。原graph_core、P0-3、原band_volume.py、UI、指標、策略／庫、原五JSON與事件／ID不改。小原料adapter另建研究binding，不冒舊全史frame已重新核驗；meta未記HTTP仍null、capture與local reuse分開，歷史公布不倒填。合成反例非市場資料。

完整band-volume.json的取得／串接／解析已結清，原10圖、五項用途及五JSON沿用；不重取分片、大檔、blob、圖、舊ZIP或來源，不重跑舊32／88、producer／指標，不為同一讀取確認再往返歸檔。無新UI，不重開手機驗收；Android NOT_TESTED_NEW_BUILD，file://不重試。

來源0.10及全部parent契約、Raw null／UNKNOWN、歷史／舊成品／main及所有警告保持，不建來源0.11或catalog、不回寫null。所有來源／個人權利缺口及Raw／Adjusted／歷史公布／主檔／SQLite未知保持。受拒入口、library及嘉新逾時路徑不重試或繞過，私人原件不公開，不補零、行情、前價或估值。execution_qualified=false；imputed_close／valuation=null；historical_signal_eligible=false；primary_pressure_id=null；policy_authorized=false。全換／分批仍研究變數，不跑每日淨帳／六方案，不宣稱辨識品質或獲利通過。

交實際讀過的本輪新研究結果及真正差異，分列未取得／未讀／未實作／未執行／未測／未讀回。若沒有明確新缺陷或核心歧義，交付現有有限研究成果，不強迫選代表線或另開階段；可重現工程缺陷只交回原唯一Codex。不部署、付費、交易、發訊息或啟動子代理，不要求使用者手機搬檔、終端或架伺服器。
```
