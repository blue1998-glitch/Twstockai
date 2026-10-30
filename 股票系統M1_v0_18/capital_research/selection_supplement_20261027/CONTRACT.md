# 待選操作的明示補選0.1

基線101c1d3744d18ba0837c4839ff8b6e10dc621a9d。新增SELECT／READ，以獨立child紀錄綁原AWAITING_EXPLICIT_SELECTION結果及完整generation；原等待結果不變，不寫原ID--choice。重用read_operation／原校驗、select_and_save、check_saved及Journal。不重新生成、不改帳／權利／reserve／latest／tokens、不建單／成交或升正式資格。

SELECT明示parent_store／parent_id、child_store／child_id及request；schema=capital-selection-supplement-input/0.1、synthetic=true、parent_binding、selection、recorded_at。selection必須非null，理由及資格沿原choose_saved；不預設、不改選。父須完整可讀READ_ONLY且保存outcome=AWAITING_EXPLICIT_SELECTION、generation=GENERATED／COMPLETE、原choice不存在。綁parent id、header／request／result id、generation id及完整source_binding（帳／截止／checkpoint／latest／全部token／版本／receipts）。停止前prefix、錯父、錯binding與未知拒絕。

child派生--request／--choice／--result三份Journal，與父key不可重疊，不複製generation或建立第二帳。既有child任一key停止SELECT，不重做或覆寫，不同內容同ID拒絕。先存請求，再沿原選擇保存讀回；遭拒保存拒絕結果並停止，不做來源check。一般／條件意圖以同一父generation核對後保存補選結果；原父一直等待留史。多個child只屬互斥研究意圖，不等資金已配置。

保存與研究結果分開；NOT_PERFORMED／SAVED_AND_READ_BACK／NOT_SAVED／UNKNOWN。UNKNOWN立即停止留檔，不自動續跑。READ明示同一父與child，核保存指紋及接線；不重新選擇／來源verdict／生成／寫檔，缺result顯INCOMPLETE_SUPPLEMENT_PREFIX，缺父或錯配拒讀，不遷移舊schema。補選時間含時區，但只證原截止的研究意圖，不回填available_at、變成新決策或今日交易資格。

先凍結精確input／expected／原件引用與版本，再驗一般／條件、未列數量拒絕、非等待父、錯父result／缺token、缺選擇、父子key重疊、同child重送／衝突、三階段UNKNOWN、部分保存與錯鏈READ。fresh雙入口禁止數值引擎／生成／網路，READ另禁選擇／check／寫檔；故障僅暫存副本，不冒真實斷電。資格完整舊矩陣不重跑；生成／producer／交易回放均0。

原本金1430、A60/B25/C2、現金275.100、reserve100、權利及歷史維持；正式flags false、主壓力null，1101 UNKNOWN、70／2／其中8／合格真實總淨0及來源／圖形／人工契約不變。R2/F、來源認證、完整分叉、多程序競爭、失敗自動續跑與原未支援帳務不擴張。無新來源、私人文件、bootstrap、UI／Android、樣本外、部署交易付費訊息。原唯一Codex／原工作區／原分支沿里程碑自審、正常保存及固定SHA讀回。
