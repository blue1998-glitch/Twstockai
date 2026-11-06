# 來源研究0.8契約

schema=`rotation-source-contract-research/0.8`，精確parent0.7完整物件與coverage不變。此獨立純事實附層只解釋來源、持有人、條件與日期／單位，沒有新個人分配、每日淨帳、六方案、買賣或自動適用規則。

原件必須驗bytes、SHA、長度、HTTPS精確URL、HTTP200、無redirect／retry與原meta。公開說明書全文native及765頁數、xref診斷保持，選定實體頁逐頁綁同一原件，不能只憑研究摘要或SHA字串。新一頁的issuer來自直接官方ESUNFHC來源URL及原件指紋，內文未印2884，不冒稱內文自載代碼。每個非null欄位proof綁source_id、實體頁、native evidence SHA及normalized_value，來源物件保存URL／原件SHA／四時點／精度與範圍。

原公開說明書官方要求2026-10-23T03:28:15.861377+00:00、完成／捕捉03:28:35.939691+00:00；本輪固定GitHub原bytes讀回09:31:15.448898+00:00。新一頁官方要求09:31:12.995652+00:00、完成／捕捉09:31:14.584109+00:00、讀回09:31:14.584728+00:00。Work附件及meta未見，Work讀回時點保持null，不能挪用這些Codex時點。文件簽署、決議、核准與歷史公布可得是不同日期角色；announced_at=null、historical_signal_eligible=false。

實體頁162／契約印刷1：甲方玉山2884（統編70796305）、乙方三商2867（統編84443471），契約簽署2025-11-05。代碼身份沿用已知公司對應，非用統編當股票代碼。頁175／印刷14第9條只記「倘甲乙任一方股東依法表示異議並請求買回」條件；不是每位股東自動有已行使權利。personal_eligibility、person_exercised、request_date、repurchase_price、quantity、payment、actual_disposition及later_amendment_applicability全null。第15.2條的修約可能性不當已修約或現行個案適用已核。

頁163／印刷2：初始0.2486只屬原2867普通股、雙方股東會及主管機關許可條件下的新2884換股對價；後續0.2596仍精確留在parent既有版本，不覆歷史、不自選目前有效版本。ratio-versions.json只是並列不同來源／階段，非個人實際受配。畸零處理僅該換股原2867，不能套2025股票股利或既有2884；最後交易收盤價是契約參照角色，沒有補價／估值或個人畸零款計算。預計17,640,615,960是初始契約預計總已發行普通股，不是實際新發行股數。新股權義相同不等既有2884零影響，actual_issued_shares／existing_2884_impact／personal_final_ratio均null。

頁175第10條員工保障與原2867股東受配、既有2884權利分開；頁176／印刷15第14條稅捐費用各自負擔不是個人免稅、零保費／匯費或淨額證明。employee_share_grant、personal_tax、nhi、fees、personal_net_cash、tax_exempt保持null。

頁461／財報印刷81：使用者指定的2025常會（2024盈餘）報告組件，依顯式研究年度選取，不按段落最後一筆或當成有效策略：股東紅利1,602,000仟元；員工酬勞522,900仟元；合計新股178,200仟股。分成股東、員工、混合總數三個角色觀察，持有人／instrument不同；不是三次行動。總數不全配股東，面額10元不是員工發行價格，不用酬勞除面額反推股數。個人實配、未圓整比例、員工股數／價格、分組股數全null。公司報告已申報生效及變更登記不是直接上市／可交易日；registration_date／listing_date／tradable_date均null。

新一頁：只記2026-01-23股東臨時會通過、2026-07-07金管會核准。表格抽字有跨欄，移除已定位核准句後確認交易標的與唯一會議日期，已視讀核對。兩日不能借成實際交割／個人權利／announced_at；不覆parent0.7新聞頁面9/2對內文今(1)日矛盾，canonical_effective_at保持null。

resolve重用原精確family／issuer／受領持有人／instrument／action_type／version／field／date_role／unit／observed_as_of；只允許SOURCE_DIAGNOSTIC，FINAL_LEDGER及歷史訊號拒用。預設未知不補零。完整旗標不得覆parent來源缺口，70窗資格由保存輸入實際計算，不能硬編總數或新績效。

既有期交所只佐證股票復牌，非TWSE直接公告，不推停牌終點／整段；missing-quotes新副本精確等parent，舊UNKNOWN與Raw null保留，execution_qualified=false、imputed_close／valuation=null。台泥月份／仟股及財報仟元對原議事錄精確元、第7頁掃描空字限制保持。

完整行動減資及7/25後權息、2884直接復牌／2025可交易日／個人實配／股利畸零期限與處置／既有股東換股影響、台泥最後調整／最細稅源、個人淨分配／九起日期初權利仍缺。搜尋未找到不是無事件，當前持股非期初權利。私人券商／集保原件不公開。

原所有版本與main不改；Raw／五年Adjusted／歷史公布／主檔／SQLite未知、primary_pressure_id=null、policy_authorized=false。全換／分批仍研究變數。已拒入口與三舊403網域不重試／繞過；無新UI不重開Android，NOT_TESTED_NEW_BUILD保持。不部署、付費、交易、發訊息或子代理，唯一既有Codex寫入。
