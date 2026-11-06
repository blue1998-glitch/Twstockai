# 明示合成研究操作外部協調0.1

基線2ccfae04a71124ce36b581181ab131666e0c6850。run_operation(store,id,request)／read_operation(store,id)及獨立CLI RUN／READ。僅串未改quantity_after_retry.generate_after_retry、Journal、research_choice_workflow.select_and_save／read_choice及research_choice_source.check_saved；不改任何數值／帳務／資格／舊schema，不建單或成交。

輸入schema capital-research-operation-input/0.1，欄位固定schema／synthetic=true／generation_input（完整明示after-retry0.1）／selection（明示mode、股數／端點與reason，或null）／recorded_at。selection存在時recorded_at須明示含時區；其餘資格由既有選擇閘門處理。缺selection欄位拒絕輸入；明示null先保存候選並停止AWAITING_EXPLICIT_SELECTION，不選HOLD或勝者。

operation ID明示，限既有Journal字元且長度1..90；固定派生--request／--generation／--choice／--result四個key，不搜尋來源或替代ID。任一key已存在，RUN不寫入、不匯入／呼叫生成器；只要求明示READ。不同請求同ID拒絕。新RUN先保存含完整canonical request_json的請求紀錄，再只生成一次、保存並讀回同一generation；來源binding由這份明示RUN的讀回值導出，不是自動選來源。selected_id／ranking不改。

生成停止也保存原結果並結束；缺選擇停止；選擇遭拒保存拒絕而不往下核對；一般／條件意圖保存讀回後，核對同一generation並保存最終結果。來源MATCHED不代表正式資格。request_json採完整JSON的canonical字串，避免重複縮排放大，READ解析原內容及指紋，不遷移舊schema。原本金、權利、reserve、latest及全部token只保存在同一原帳鏈，無新會計。

保存分request／generation／choice／result各有NOT_PERFORMED、SAVED_AND_READ_BACK、NOT_SAVED或UNKNOWN。任何階段保存失敗／回應不明就停止，保留已存在檔案，不繼續選擇／核對、不刪除、不rollback或重跑。最終計算結果與保存確認分開；UNKNOWN須明示READ。READ只核既有request／generation／choice／result指紋與接線，不生成、不重新選擇、不重新核對source verdict、不寫檔。缺最終結果顯示INCOMPLETE_SAVED_PREFIX；缺失／衝突不猜零或補算。最終結果保存後可READ原結果；原件／歷史schema不變。

這版不支援缺選擇後補選、失敗／中斷自動續跑或多程序競爭保證。已存在ID不靠自動重跑修復；保留所有檔案並回報。Journal原單機／fsync／partial／目錄持久性界線不升格。指紋是保存一致性，不是來源認證。

先凍結精確引用／請求／expected／版本，再執行新定向操作：一般、條件、舊觸發拒絕、搜尋上限及缺選擇；必要反例涵蓋同ID重送／不同內容、各階段UNKNOWN、部分保存READ、跨來源或帳戶接線錯配與fresh READ無引擎／重選／保存／寫檔／網路。故障注入只用暫存副本與明示cached backend，不冒真實斷電／新市場結果；新RUN只計本輪實際呼叫，不加舊PASS。

70／2／其中8／合格真實總淨0、1101 UNKNOWN／拒算、正式flags false／主壓力null、原來源／圖形／人工契約及未支援帳務保持。無新來源、私人文件、bootstrap、真實producer、舊suite／九路徑、UI／Android、樣本外、部署／交易／付費／訊息。原唯一Codex／原工作區／原分支依里程碑有限工程、自審、正常保存及固定SHA原件讀回。
