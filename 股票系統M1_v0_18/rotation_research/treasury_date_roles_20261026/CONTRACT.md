# 台泥第58頁獨立日期角色契約0.1

- 只適用已固定SHA的1101／2026Q2合併財報實體及印刷第58頁，輸入schema `rotation-treasury-date-roles-input/0.1`，輸出 `rotation-treasury-date-roles/0.1`。不是新公司行動catalog或金融來源資格。
- 原PDF、124頁全文、metadata及原抽字紀錄由IO層核bytes／SHA與精確頁面對應；純核心另核source／issuer／URL／PDF／native／頁碼／頁面內容及原觀察ID。指紋綁定只保護此保存來源，不宣稱通用來源認證。
- 新觀察保存公司報告的board_approval_month=2026-01、registration_completed_month=2026-02，以及cancellation_quantity=28000／THOUSAND_SHARES。月份保持ISO_MONTH，不補成日期；登記完成月份不是董事會日期、除權日、生效日或個人款股日。
- exact_board_approval_date、exact_registration_completed_date、exact_effective_date、announced_at、holder_conversion_ratio、holder_cashflow、personal_entitlement均為null，未知欄位沒有proof，不得default成0。一般股東與公司庫藏股角色不得互借。
- 保存原0.7catalog ID及觀察ID的明示同源連結，不另造帳務事件或市場樣本，不修改原0.7、來源0.10及全部parents的資料／資格／null／指紋。
- 原捕捉、原讀回、新本機讀取、新observed_at及後續視讀／核驗分開。附錄不早於原來源可觀察時點；document／year-month、HTTP時間及PDF建立時間不能補announced_at或認證一月歷史訊號。
- 查詢重用原resolve_field，須精確version／family／issuer／持有人／instrument／action_type／field／role／unit／帶時區observed_as_of，只准來源診斷。FINAL_LEDGER／歷史訊號／未知欄拒用；重新hash輸出不能改原來源事實或升資格。
- 純核心與IO分離；新單筆builder只讀既存原件，exclusive-create保存新input／expected／actual／收據，不執行舊producer／窗口／會計。READ使用保存JSON，不重算或遷移。
- 保留全部外部資格false、主壓力null及70／2／其中8／0；不把來源紀錄當實際股東績效、零影響或策略有效性。
