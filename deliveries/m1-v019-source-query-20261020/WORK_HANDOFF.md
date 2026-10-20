本次source／查詢成品已核提交：`e45d972406cc6a4ef1a9babf1ba9865d97073096`；GitHub逐檔回下載27檔／15,211,000 bytes全等，遠端JSON同原來源／完整query逐值重現。回讀收據與本段另存後續交接提交，最新請實際核分支HEAD。

請接續股票系統M1，同Work使用已完成的來源反查研究正式整體歸屬，不重做查詢／圖表／reaction_facts，不自行合併。

儲存庫：blue1998-glitch/Twstockai
分支：dev/m1-v018-chart-annotations
本輪已核工程起點：df25a67191fa19b7d577d2e2bdd4e3ff2f365356
原反應事實交接：db000b9a7a09c2bbc693e9d2094482a5edd6b867
原真實圖成品：fff47915523fab8c8de8279de8bbb7a26b05647b
新source／查詢成品及最新交接提交見本目錄README／GITHUB_READBACK.json，最新以實際分支HEAD為準，不能把工程起點冒充最新保存。確認包含指定提交；若有更新先讀最新交接、保留全部後續成果，不用main或舊ZIP覆蓋。

依序讀AGENTS.md、CONTINUE_IN_WORK_MODE.md最上方、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md最新節；全文讀deliveries/m1-v019-source-query-20261020/README.md、本WORK_HANDOFF及GitHub回讀收據。再讀股票系統M1_v0_18/graph_diagnostics/SOURCE_QUERY.md、source_query_validation_20261020/驗收報告.md與verification.json、source_query_examples/request.json、source_query_generated/source-query.json。沿讀docs/visual-discussion/20261020_source_query_contract/CODEX_HANDOFF.md與SOURCE_QUERY_CONTRACT.md、path-audit.json，以及structure_membership_work_review的README／user-decision／原audit和reaction_pressure_work_review/USER_CORRECTION.md。原反應事實、真實圖、五月十月反例與全部來源限制沿用，不重讀101圖、0.4.3或舊手機驗收。

本輪已實作既有graph_diagnostics內source_query.py純函式、source_query_adapter.py及source_query_cli.py，沒有改原diagnose／graph_core／策略／schema／庫／歷史／主圖／reaction_facts。重用原fingerprint／number／_validate／publish_immutable，不呼叫diagnose、_pivots、_boxes、analyze或MACD來反查。

明示pivot_ids反查所有原箱引用及序位；原箱完整起末、確認、尺度及source_turn_ids保留，不按月份裁箱。完整同座標依同segment／種類／發生日／精確價／有序source_dates，全同才列對照，不合併ID或投票。路徑只接明示同scale／segment的from_id與to_id，完整保留中間來源；跨尺度、跨段、倒序、未知／未確認、混合來源／基底／context／前綴拒絕。額外點只入ID表，不遞迴反查更多箱。

原來源確認、關係not_before_original_confirmations（路徑全點最大／對照雙方較晚／引用原箱與點）及後來實際selected_at分開；historical_selection_time=null、historical_signal_eligible=false。CLI每次記真正執行時間；純函式同完整query可逐值重現。comparison診斷摘要明示SUMMARY_ONLY，沒有宣稱完整diagnostic_id驗證；來源自洽不認證外部行情或真實歷史公開可得。

實際準備：本環境bootstrap --hydrate-missing成功，0補檔／7差異保留。最終14項新Python測試PASS／1.572秒，包括真實171來源全反查與89原箱引用、完整9點路徑／119序列背景、同座標異確認與source_dates差異、非法與未確認／混合／跨尺度段／倒序拒絕、原前綴在追加改未選未來封包後報告不變、純函式確定性／輸入不變、CLI實際時戳／精確JSON／衝突不覆寫及禁重算mock。固定原ZIP CRC／SHA及原完整來源／core／manual audit全等另實核。查詢JSON30584 bytes／SHA4a43a8c0f03bbffacb86306f064b7c807a7a83bdaf7e737bc76cd654a2c1dbb0。無新瀏覽器／Android／ZIP，不沿用舊22／47等作本輪通過。

守衛整合時曾有1次14項中1項FAIL：較早的參照一致性檢查正確拒絕了故障fixture，使測試未走到要驗的原K source_dates守衛。已同步fixture冗餘來源欄位以隔離原K檢查，保留原拒絕斷言與新守衛，完整失敗log保存；最終14項PASS，不隱藏初敗。

本例明示查3點，A反查B16／B17／B18，另查10/24與11/28原3%來源並列6%原ID／確認；合計8原箱／17原轉折供獨立閱讀，不是8個獨立型態或重要性票。9點路徑最後35.50高於前高34.15；全原序列119點／前33後77只作背景，不決定正式整體起訖，也不自動串接全歷史。六月前40.25等來源保留不表示歸入人工整體，不把任何該價或39.25／35.50／35.45指定正式代表。

下一步Work以可追溯單點、其原箱、完整路徑和反例研究正式整體歸屬的必要證據與反證。已確認不重問：整體可含不同形態、不要求整體再通過局部橫箱同條件；局部與整體分判；本例未挑戰舊帶高點前不因低位整理先降重要性。月份、39筆、5/13、6/3、1/27等案例不重問。這些確認不批准自動合併、代表、區界、量權重或買賣規則。只有真正新核心歧義以具體原真實圖討論；已定規則或可重現工程缺陷才交Codex。

primary_pressure_id=null。正式成員／整體區界代表／增量／衰減重要性／量權重／合併直接承接／解除／生命階段未知。原拒絕餘量−2.4800／−0.7825、49反應轉換非訊號、89版本84幾何非獨立型態、不同窗不排名、原值可知與實際選取分開、相等不補過破／日OHLC不證日內順序保持。Raw公司行動／五年Adjusted／歷史可得／九待核非窮盡日曆／Darvas／SQLite未知；核心NOT_ESTABLISHED／分類NOT_VALIDATED／行動NOT_EVALUATED；Android NOT_TESTED_NEW_BUILD、file://不重試不繞過。

保留原核心、參數策略、庫、歷史、舊頁、案例來源證據及main。不調參寫死人工答案，不新增自動選關／合併／主壓力／解除／量權重／買賣門檻，不部署、付費、交易、發訊息或啟動子代理。成果與實際研究／錯誤保存同分支並逐檔GitHub回讀，未讀未測未執行不得標完成。結束提供最新已核提交、入口、完成未完成與完整換模式續接指令。
