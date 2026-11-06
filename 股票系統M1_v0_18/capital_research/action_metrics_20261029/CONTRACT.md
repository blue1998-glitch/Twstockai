# 完整明示行動保存結果的全帳戶評估轉接 0.1（事前契約）

基線64d2bd5dc17012743b07f8ef15bb8771ca2c1a7b，原唯一Codex／原工作區／原分支。只讀已保存合成行動與原帳，不呼叫決策、成交、續播、checkpoint重建或ledger。舊結果／oracle／schema不遷移，不新增策略、排名或正式資格。

## 新入口及來源

`action_account_metrics.evaluate_saved`，輸入`capital-action-account-metrics-input/0.1`，exact schema／synthetic=true／evaluation_at／saved_result；輸出`capital-action-account-metrics/0.1`。saved_result exact schema=`capital-saved-action-source/0.1`、action_request、action_result、continuation。

action_request必為完整原cash_action_execution 0.1／0.2請求；action_result必為該請求的完整保存結果，非numeric_result、單一ledger或checkpoint摘要。保留原checked_action、action_input、execution_spec、execution_job、execution／checkpoint與來源指紋。原HOLD／BUY／SELL資格只核保存收據及結構，不重新評估或提升。

continuation為null或一份exact request／result，限同原行動的既有standing-order-resume/0.1保存完成結果。完整root_job、path／觀察、前身checkpoint及latest、原單／fills／token必精確相連；不得換root、補行情或重新續播。此版不串任意多份續播、不推定缺段、不中斷資料來源認證。

## 純讀取防線及共用公式

沿lifecycle._snapshot／_chain／_account與原全帳評估的rows／source／origin／時間／曲線／成本檢查。補完整請求及結果綁定、原checkpoint／帳／權利／一般reserve／latest／fact sources與token保存；已知fact history只作純來源一致性校驗，不生成新決策。收據SHA只證保存自洽，不認證來源或每筆分錄真偽。

不得呼叫continuity.validate_checkpoint（它會重播ledger）。評估只用最後一份完整累積原帳daily一次；父輪與部分前綴只校驗，不加總重複曲線或費稅。原account_metrics共用驗證及_curve_statistics，不另寫成長、回撤、恢復或費稅公式。舊quantity入口結果須完整相容；只抽出共用內部驗證，不擴放舊格式。

原始資本與應計淨值區分；保存成交費稅已在曲線內，不重扣。原帳期末假想退出成本／成本後成長另列，不冒實際全清倉。恢復維持日曆日／未恢復截尾，不補交易bar或固定檢討天數。evaluation_at須不早於保存水位及close.available_at，保留等價時區語義。

停止、不完整、缺價／缺日、未知權利、缺原輸入、錯前身／原帳／token／一般reserve／source或真實來源皆REFUSED、statistics=null。部分前綴可保留原拒算；只有後續完整原件才可進入完整評估。輸入與呼叫端／DefaultContext不變，外層完整50位Decimal隔離，API無IO／網路。沿原account_metrics_read新增明示--source-kind action；預設quantity路徑維持，不自動挑來源。

## 事前手算與必要驗收

保存的1/5～1/12每日應計曲線共8列，原本金1180。減B3末值1176.80：期間成長與最大回撤皆為-3.20/1180；退出B7末1176.72為-3.28/1180；拆3+4末1174.72為-5.28/1180。皆自1/5峰值至1/12仍未恢復，截尾7日、recovery_date=null。原費稅分別3／3／5，只保留原數字。B20部分賣7後續播完成末1176.46，成長／最大回撤-3.54/1180，同樣7日未恢復；原剩13到期不假裝全退。這是原帳應計，不能拿cash當淨值。

先存精確來源指紋、完整input／expected與更動recipe，才實作。正例含減碼／退出／拆單／部分續播完成、舊HOLD／BUY；反例含部分前綴及停止、錯完整來源／帳／latest／token／權利／日曲線／基底／時點。必要舊quantity原結果精確回歸、完整Context／input不變、fresh process禁決策／執行／帳務／重建／IO網路與CLI明示路徑。只計本輪唯一方法，不加歷史PASS或合成案例數；不跑整套舊suite或真實producer。

70/2/其中8/真實合格0、1101 cash_claims UNKNOWN、正式false／primary_pressure_id=null、全部來源parents及圖形人工保持。R2/F、來源認證、未知期初款及原未支援帳務不擴張。無代理／分支／worktree、bootstrap、市場回放或部署交易付費訊息。沿已授權里程碑自審、正常commit/push及GitHub固定SHA讀回。
