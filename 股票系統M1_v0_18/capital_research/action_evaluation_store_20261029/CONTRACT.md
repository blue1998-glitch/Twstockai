# 既有行動評估的明示匯入／唯讀保存 0.1（事前凍結）

基線a33bfc416881e58e390c3086523ccf0d6a743a07。唯一既有Codex、原/workspace/Twstockai／dev/m1-v018-chart-annotations。只新增完整來源與已完成評估的IMPORT／READ，不產生評估、決策、委託、成交、帳務或市場回放，不另建store／引擎。

## 輸入、單筆紀錄、狀態

IMPORT(root,id,request)：request exact schema=`capital-action-evaluation-import-input/0.1`、synthetic=true、evaluation_input、evaluation、expected_evaluation_input_id、expected_evaluation_id。id沿既有明示operation identity。evaluation_input是完整capital-action-account-metrics-input/0.1與完整saved_result（action_request／action_result／可選一份原單續播）；evaluation是既有capital-action-account-metrics/0.1原結果，不用摘要或路徑代替。expected兩ID須由外部明示且精確符合原件；不自動選最新來源或重算。

單一capital-action-evaluation-record/0.1綁完整import_input、其指紋、evaluation input／來源document／evaluation ID、原evaluation_at與status，再有record_id。重用原Journal.save的exclusive create與同內容重送；同ID異內容NOT_SAVED且原件不動。重用原_persist保存／讀回／全文相同檢查，寫入或讀回不確定則UNKNOWN，不當成功。單筆原子建立不等斷電／多程序全面保證；部分檔原樣保留、不修復、不刪除或自動重試。

READ(root,id)無request，不呼叫評估／決策／執行／帳務／Journal.save／修復或網路。只沿Journal.read與同版純結構校驗；缺檔NOT_FOUND、損壞／錯schema／跨來源UNREADABLE；不補算。receipt的storage_status與evaluation_status分開；SAVED_AND_READ_BACK／READ_ONLY不提升任何資格。拒算可保存，仍REFUSED、statistics=null及全部正式false。

## 校驗範圍及誠實界線

既有action_account_metrics的純來源校驗原樣抽到saved_action_source，保留原API接線、原數值公式與舊結果。IMPORT／READ只用純來源／指紋／保存欄位核對，不載入account_metrics／action_account_metrics，不計成長、回撤、恢復或費用。

EVALUATED須來源結構成立、精確綁原帳／原capital／權利／reserve／latest／全部token、截止與close.available_at、evaluation_id、原成本及期末值、完整原8日日曲線equity。來源資格仍限完整明示合成，正式flags必false、主壓力／ranking／selected_strategy null。統計shape及來源投影校驗不重算指標；不能識別所有自洽改寫或宣稱來源認證／逐分錄審計。

REFUSED原評估source=null，沒有producer input attestation，不能證明拒算原因確由這份input計算。只接受明示完整同版合成input與已簽名REFUSED原件，保存外部pinned input／evaluation的宣告配對，標明EXPLICIT_REFUSAL_ASSOCIATION_NOT_REEVALUATED。所有指標／來源／帳／成本／期末值須null、拒算原因非空；不因存檔而重新資格化或假造來源證明。缺完整輸入或外部ID不符仍不保存。

## 事前正反例與驗收

重用action_metrics_20261029已保存的退出、減碼、部分續播完成與部分／停止拒算input／actual，先凍結完整新IMPORT input、expected與來源長度／SHA，不重跑評估或producer。正例須保存及純READ完整相同、原帳與token不變；REFUSED另存且資格false。負例包括缺來源、錯input／evaluation ID、跨來源、錯截止／latest／token／帳／reserve、資格提升、unknown schema、REFUSED夾指標。

必要定向驗證：同ID同內容不改檔、同ID異內容拒絕、symlink／破損／缺檔、寫前／寫後／讀回故障、UNKNOWN後只明示READ、READ禁producer／評估／save／寫檔／網路、input不變及完整Decimal呼叫端狀態不變。來源校驗搬移只選必要既有完整評估／拒算的精確輸出回歸，不重跑舊suite或真實producer。CLI只明示IMPORT／READ，無RUN或自動重新評估。

70/2/其中8/真實合格0、1101 UNKNOWN、正式false／primary_pressure_id=null、來源0.10全部parents與圖形人工保持。R2/F、來源認證、多段續播來源矩陣、未知期初款及原未支援不擴張。Astra／Work／救援未讀保持。沿里程碑必要測試、自審、正常commit/push及GitHub固定SHA讀回；無代理／worktree／分支、bootstrap／部署交易付費訊息。
