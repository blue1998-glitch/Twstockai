# 明示承接保存來源及既有選擇｜實作前契約

基線36b9e2779286537579f6680dd382fee1143b03e2，原工作區／分支／唯一Codex。只沿research_operation新增IMPORT分支，不另建協調器、Journal、READ工具或帳本；舊RUN／READ及保存結果不遷移、不重算。所有股數／策略／時點已在原件外部明示，這輪不生成、不重選、不入帳、建單或成交。

## 輸入及精確承接

新API `research_operation.import_operation(store,id,request)`、既有CLI新增明示IMPORT。request exact schema=`capital-research-operation-import-input/0.1`、synthetic=true、saved_source（完整capital-saved-quantity-source/0.1，內含完整0.4 request與generation）、choice（完整既有capital-research-choice/0.2封套）。沒有choice不自動選HOLD或建立新choice，沒有來源不搜尋替代。RUN不能偷接IMPORT請求；READ仍不接受input。

新header／result／receipt各明示operation版本0.2；舊0.1原語義不變。沿同一明示操作ID派生--request／--generation／--choice／--result四個Journal key，generation階段保存原saved_source，不呼叫生成器。header canonical request_json含完整原件，四階段互相以指紋連結；來源及choice寫入／讀回值必與輸入完全一致。

重用bind_saved_source、validate_record及已有unit／receipt／checkpoint純READ校驗。來源只可完整0.4；choice只可既有0.2，精確屬該來源及唯一成員，不只匹配候選ID。核choice.request_id與原choice-input/0.2的完整來源、binding、requested_selection、recorded_at相符；不再次choose_saved／select_candidate，亦不重新決定資格。原source_kind、原帳account_snapshot／權利／reserve、origin/latest、全部歷史及當期token、單位來源／通道／可知時間及full_search政策／逐點收據原樣承接。

綁定不明的REFUSED choice不能冒與指定來源相同；這版拒絕不具可回查source_binding的匯入。原開帳不造checkpoint；既有checkpoint不變新本金。未知資料及完整來源的既有不支援狀態沿原拒絕；沒有重新核算或來源認證。

## 狀態與保存

一般choice → COMPLETED_RESEARCH_INTENT；條件choice → COMPLETED_CONDITIONAL_INTENT，仍不代表立即可買。既有REFUSED choice可原樣保存為CHOICE_REFUSED，不改選、不升資格，停止後續source-check階段。一般／條件意圖在IMPORT只呼叫既有純來源核對一次並保存verdict；MATCHED與正式資格分開。READ僅驗保存鏈及verdict結構，不重新呼叫check_saved、生成器或選擇器。

任一key已存在，IMPORT完全不寫，顯示OPERATION_EXISTS_READ_REQUIRED；不同請求同ID為OPERATION_ID_CONFLICT。部分紀錄不自動續跑、不刪除或rollback。各階段沿原_persist讀回；NOT_SAVED／UNKNOWN立即停，保留已保存前綴。明示READ顯示INCOMPLETE_SAVED_PREFIX或UNREADABLE，不補來源、choice或最終結果。保存狀態與研究意圖／拒絕分開。

## 凍結及驗收

正例直接重用choice_v04_20261029/final的B2一般、B93條件、checkpoint新觸發、舊觸發零新增、HOLD及UNKNOWN拒絕。精確來源／choice／版本／指紋先保存，所有成功原件、帳戶、單位、收據及token逐bytes內容核對。所有反例與正例input指紋須不同，避免無實質變動的假反例。

反例：跨來源配choice、缺source／choice、null choice、舊版choice、已重簽但錯request_id／token／角色、改帳戶或單位／搜尋政策及未完成generation，一律拒絕，不自行重選或認證。必要保存控制含同ID相同／異內容、每階段UNKNOWN、缺中間／最終檔、交叉階段錯鏈及READ不寫入。故障注入只在新暫存store，不改舊原件。

必要定向方法覆蓋：全部凍結預期、完全原帳／權利／reserve／latest／token及來源保存、原REFUSED不升級、Journal同ID／UNKNOWN／部分前綴／錯鏈、fresh process禁止數值producer與選擇函式／網路、IMPORT只一次來源核對且READ零次、完整Decimal／input不變、舊operation READ完全相容及既有ID RUN不執行生成。只重用歷史保存結果，不跑舊suite／數值回放／真實producer。

本輪只合成研究結果承接，不接補選、多份比較、條件單啟動或成交。70／2／其中8／真實總淨合格0、1101 UNKNOWN、正式false／主壓力null、全部來源parents及圖形人工不變。R2/F、來源認證、自動解除衝突及原未支援帳務不擴張；封存救援只保留不解壓套用，Astra及封存內原件未讀不作新認證。沿功能里程碑自審、正常commit/push與GitHub固定SHA讀回，無代理／worktree／新分支或部署交易付費訊息。
