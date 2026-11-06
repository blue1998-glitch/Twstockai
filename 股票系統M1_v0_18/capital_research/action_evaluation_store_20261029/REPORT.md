# 明示匯入與保存讀回里程碑報告

基線a33bfc416881e58e390c3086523ccf0d6a743a07。起始原/workspace/Twstockai、本地／遠端與原分支一致且全淨；原唯一Codex，沒有代理／worktree／競爭分支。只補原評估的受控保存，沒有新增回放或策略。

## 新增能力與重用

新action_evaluation_store.import_evaluation／read_evaluation及明示IMPORT／READ CLI。重用rotation_research.store.Journal、research_operation._persist及原id規則；一份record包含完整來源／既有評估與外部pinned IDs。原Journal exclusive create、相同內容不改檔、不同內容衝突、fsync及保存讀回沿用，不另建store或資料庫。

為使READ不載入評估器，將原action_account_metrics內七個純來源校驗函式原樣移到saved_action_source，原API保留同名aliases；原evaluate_saved函式本文逐字不變、所有財務／指標公式未改。AST來源片段精確比對，不為搬移重算原評估。原account_metrics、CLI、execution、continuity、ledger、Journal、來源與資格檔均保持指紋。

EVALUATED的原source document／evaluation input／evaluation／checkpoint／截止與可得時間、原帳／rights／general reserve／latest／token、原成本及期末數字／每日equity須相符。只檢查保存投影與shape，不計算成長／回撤／恢復或再扣費。REFUSED保留原null與理由；外部明示配對標EXPLICIT_REFUSAL_ASSOCIATION_NOT_REEVALUATED，不假造不存在的producer input attestation。

## 凍結與實際驗證

先保存本契約、16組完整IMPORT input／expected、原評估input／actual長度SHA、變動前source及保護原件，再實作。凍結材料、舊oracle及actual均不覆寫。功能驗收首批全過；提交前格式及來源指紋核對失敗與更正另留史，詳末段，未修改oracle。

五正例（退出、減碼、部分續播完成、部分前綴拒算、停止拒算）實際寫入Journal並READ完整相同。十一負例（缺來源、錯兩個外部ID、跨來源、錯截止／latest／token／reserve、正式資格提升、未知評估schema、拒算夾指標）均NOT_SAVED，READ為NOT_FOUND，沒有自動補檔。保存及資格狀態分開，拒算留存不等合格。

最終8個唯一方法首次全部通過，不加16案例／故障控制或舊PASS。證據：tests.log與validation。另驗同ID同內容完整receipt相同、檔案bytes／mtime不變；同ID不同合法內容拒絕；非法id／symlink拒絕，原目標檔不動。READ對缺檔／損壞／錯schema／重簽但跨來源或資格不合保留UNREADABLE，不修復。

故障注入只在新暫存副本：寫前失敗UNKNOWN後READ=NOT_FOUND；寫完後回覆失敗UNKNOWN後可明示READ_ONLY找回完整record；讀回錯配UNKNOWN但原檔仍可純READ；部分JSON寫入保留原bytes且READ=UNREADABLE。這些是定向軟體故障，不宣稱真實斷電或多程序全面保證。

fresh process的IMPORT及READ均禁止import評估器、決策、execution／continuity／quantity／ledger，仍完整執行CLI。READ再禁止save、mkdir、所有寫入open與網路，保存前後檔名／內容SHA相同。完整Decimal環境控制下receipt及原件相同，caller／DefaultContext／input不變。所有新評估／決策／成交／帳務producer呼叫0；沒有重跑舊suite或真實producer。

## 限制與後續

保存只能證明原件自洽及明示配對，不是來源、指標計算過程或策略的認證。拒算的來源因果沒有producer attestation，不靠reader重新評估補證；自洽重簽的任意統計造假也不全面檢出。舊結果不遷移，UNKNOWN及破損留存，不提供自動恢復／重試；來源仍限原已支援的一份續播完整合成範圍。

70／2／其中8／真實合格0、1101 UNKNOWN、正式false／primary_pressure_id=null、0.10全部parents、P0-3/P0-4／reaction_facts／人工基底及原未支援不變。R2/F、信用、未知期初款、來源認證、多段來源矩陣、真實市場回放與策略未擴張；Astra／Work／救援原件未讀。未執行bootstrap、九路徑、UI／Android、樣本外、部署交易付費訊息。

里程碑自審檢查來源函式原樣搬移、IMPORT／READ不載入數值評估、單筆Journal保存／讀回、所有input／權利／latest／token不變及資格不混用；保存前再核manifest／敏感內容，僅正常提交本輪相關成果並GitHub固定SHA讀回。無人工操作，不預設Work例行工程驗收。本項結清，不增加相同保存／READ工具；後續只依既有已定義缺口，未定策略與共同期間留回研究。

提交前staged格式檢查攔下saved_action_source.py尾端多餘空白；只移除空白，函式逐字相同，未重跑測試。actual/source-versions.json保留測試時版本；final-source-versions.json為提交版本，diagnostics保存差異及修前manifest／preservation。輸入、預期、actual及log均不改。

來源指紋方法改為明示核對final-source-versions.json；第一次更新因相對路徑錯誤未寫入，tests-format.log如實保留舊指紋不符FAIL。更正指針後只執行原test_01，tests-format-corrected.log PASS；八個唯一方法不加成九個，其餘七個不重跑。舊test_store.py保存在diagnostics/pre-format-test_store.py。
