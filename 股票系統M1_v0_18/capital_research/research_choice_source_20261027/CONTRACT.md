# 研究選擇紀錄與明示完整來源：純READ核對並列0.1

基線424689ce351e6fb548e6ff5a3d1c74c84a12e820。純API research_choice_source.check_saved(choice_value, explicit_source)；獨立stdout-only CLI research_choice_source_read使用原Journal read_choice讀指定store/id，再讀明示--source完整JSON，不改舊READ／SELECT格式或schema。

重用validate_record與bind_saved_source；來源必須是完整quantity-after-retry/0.1保存wrapper及其COMPLETE generation0.2，不能只傳內層generation或候選ID。整份內容／來源版本、原帳／截止／latest／checkpoint／歷史與當期reviewed tokens／receipts綁定須完全相符；不找較新來源、不重新選擇或呼叫生成器／數值／會計／回放。指紋是內容一致性，不是來源認證或防任意重新簽署造假。

check_status=MATCHED或REFUSED，choice_status原樣獨立。相符後，selected或rejected_candidate快照須以ID在明示來源中唯一存在、完整內容相同；不能只看股數／ID。兩者皆無但綁定相符可回報NO_SAVED_CANDIDATE，只證來源相符；沒有綁定則拒絕核對，不猜來源。只有MATCHED才有兩欄；錯配／竄改／重複ID則columns空、保留原因。等待交割只顯條件意圖；REFUSED意圖不升格。新CLI exit0只表示來源核對相符，並非研究／交易資格；錯配或IO錯誤exit2。預設text，可明示json。原選擇CLI退出碼不改。

並列只顯保存候選／分類與來源綁定；不重建完整帳本、現金、reserve、權利或成交。所有正式flags維持false、主壓力null。來源無需新行情，不補1/13、不改原件／帳／token，不建立新選擇或第二帳。共市場策略比較、來源真偽、完整分叉及原未支援不擴張。

驗收：一般／條件／遭拒來源相符；有綁定無快照及無綁定分開；同ID不同generation／錯latest／缺token拒絕；紀錄竄改、非完整來源、快照內容不同、來源重複ID拒絕。結構變體是合成READ輸入，不冒producer結果。先凍結精確引用、變體、materialized input指紋及expected，再實作。必要測試證明原件／輸入不變、核對與資格分離、fresh CLI無引擎／重選／保存／寫檔／網路；不重跑舊suite、producer或已結清案例。

1101 UNKNOWN／拒算、70／2／其中8／真實總淨合格0、來源／圖形／人工契約及原未實作保持。無新來源、私人文件、bootstrap、UI／Android、樣本外、部署／交易／付費／訊息。原唯一Codex／原工作區／原分支依里程碑有限實作、自審、正常保存讀回。
