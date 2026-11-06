# 隔離研究修復0.2與趨勢延續0.1契約

本文件是未提交的研究契約；本地基線與最新已核遠端均為`6be4333d490bcccfe952c7606dffb802b76cdd5c`，固定舊工程`ea380cf7d9ae7fa8e204c2b02dfea72f51b3fa01`。0.1 REPORT／CONTRACT／validation_20261024及全部舊包不修改、不重新生成。新輸出決策／成交／比較版本為0.2，舊Journal READ依原樣讀回，不移轉版本、不重算。

## 真實持股與可能成交風險

`transition_risk.inspect_risk`每個明示觀察透過原`action_ledger.replay`的當日帳，取得實際持股及股份應收；沒有第二套公司行動、資金入帳或估值程式。價格只取決策原mark及已觀察tape，保存每個來源／基底及時點。新買進時任何有曝險的價格仍停在以前交易日，保守阻擋增加風險，不能暗補即時價或用當日稍後收盤。

檢查單股、群組、共同情境帳戶風險時：尚未成交賣單不釋放任何額度；目前持股、尚未可賣的權利、仍可能成交買單一起計入。潛在買單按有界限價及成本保守估計；對每一共同情境，只計可能買單的下行增量，不預先認列尚未買到的避險利益。任何買單導致可能超限則不成交，沒有自動假定縮量成交或成功退出。

觀察到價格跳變而原持倉已超限時，`risk_observations.actual_violations`照實列出。零交易可作`observation_only`帳務控制，即使候選本身不可行也能觀察既有帳；此模式必須空orders，不能用來放行新買單。降風險賣單仍受限價、容量與跌停限制，不保證市場超限時一定能退出。

## 舊委託、條件方案與新決策

有已結現金且原本可用的持續委託，在原有效期限內可繼續，仍逐觀察接受來源、取消事實、風險及現金檢查。沒有新證據觀察不等於證明突破永遠有效；輸出執行模型資格仍false。

凡原候選`funding=WAIT_SALE_SETTLEMENT_AND_REEVALUATE`的買單，狀態為`WAITING_REASSESSMENT`。賣款到位不是批准，不能自動使用原decision_date成交。`tape.evidence_status=INVALIDATED/BASIS_CHANGED`會取消該股未成交買單，即使價格仍在限價內。

明確`reassessments`必須綁定id、order_id、新decision_input、新decision_id、plan_id、checkpoint_id與cancelled_order_ids。新截止必為成交日前的真實研究日終，account必精確等於原帳既有成交／權利／應收的檢查點；不准把應收搬成現金。新decision須在成交前可知，來源／基底不偷換、成本假設一致、候選須可行且已結資金足夠。目標縮小必取消並另發明示委託，不靜默改數量。成交會保存新decision_date，execution_events另存完整decision_id與觀察時點。

## 連續帳戶檢查點

`capital-account-checkpoint/0.1`包含原始ledger_input、執行結果、截止前全部明示fills、日終持股／現金／應收應付／股份應收、所有未成交狀態、root initial capital與external_flow=0。`make_checkpoint/validate_checkpoint`重新委派原帳驗證，不只信任新NAV或token。

`resume_decision`現在必須給checkpoint。上一個decision_id／common_account_id須與已執行結果相符，下一account與截止須精確回連原帳；加現金、掉權利或無聲刪除舊單都拒絕。已看token只能防重複證據，不單獨證明資本鏈。完整來源／執行指紋放在完整性metadata，數值決策只綁prefix checkpoint state；改未來原價可以改完整性metadata，不能改共同前綴的decision。

本最小連續adapter只支援在日終已無買進應付、且檢討時明示取消全部尚有效未成交單後，建立下一輪新決策。逾期單保留剩餘股數、狀態與到期事件，不必假造取消。新`continuation`回原始opening及既有全部fills追加重播，從不把當前帳戶重新當成一筆新初始資本。跨輪重複order ID拒絕。期初應付、不中斷承接外部既有委託、信用借還款仍NOT_IMPLEMENTED／拒絕，不以這條有限成功路徑冒稱全部帳戶生命週期已支援。

## 共同市場與靜態支配

`compare_jobs`共同身份包括完整初始資料／權利、ledger、tape、observed_until及前次帳戶state。tape價格、容量、交易狀態、available_at或交割路徑不同，不能當同市場政策比較；各方案orders可不同。

`scenario_values`與`dominated_by`只是**假定目標已達成**的靜態壓力診斷：不含等待、未成交、重評或執行路徑。輸出`dominance_scope=STATIC_TARGETS_ONLY`、`policy_dominance=NOT_EVALUATED`；研究建議不再用靜態Pareto淘汰可行政策。只有真正共享外生市場、原始資本與權利的逐輪回放，才可描述此合成路徑下的政策結果，仍無市場有效性或R1/R2勝負。

## 「10倍股」延續狀態

指超過原持有預期仍可能延續的股票，不要求真的十倍，不承諾無限報酬。`trend-continuation-research/0.1`吃明示且有來源／可知時點／證據ID的P0-3狀態及箱型、密集量峰、點線階梯、動能修復、動態平衡、跨尺度證據。這是已給事實的研究狀態機，**不是**正式圖形辨識器、正式量峰選線或新交易規則。

狀態可在UNKNOWN、CONTINUATION_SUPPORTED、REVIEW_REQUIRED、CONTINUATION_REFUTED間反覆變化。已知轉弱不被未知量能遮掉，後來修復也不刪除以前反證。每次保存decision_at、data_cutoff、available_at、binding、支持／反證／未知、替代股／現金比較與展延理由。

續抱資格與加碼資格分開：可條件式研究續抱不等可加碼；明示新資金證據、相同來源基底、當期硬風險均須另核。事後winner標籤只進報告，不能作決策輸入、放寬限制或回填早期狀態。到原目標價、獲利或天數不自動退出；延續必保存理由與替代機會。不設永久參與比例。

壓力知識分四類：DATA_MISSING、NO_IDENTIFIABLE_UPPER_PRESSURE_IN_VERIFIED_SCOPE、BROKEN_OLD_REFERENCE、UPPER_PRESSURE_REMAINS。無可識別壓力必有明示已核**範圍**與來源，不等缺資料；兩者都不填無限合理空間。突破需同基底已知參照及嚴格價格事實；只突破小參照而上方舊主要參照尚在，仍列UPPER_PRESSURE_REMAINS。來源基底變更先UNKNOWN，保留未核跨越主張而不把舊價拿來認證新基底。正式primary_pressure_id仍null，不造近期高點。

虛擬用途只允許把實際股數完整分割為互斥用途，總和必等於實股。權利清單只在單一帳戶保留一次，不能每個用途各複製一份股數／股利。

## 最小共同路徑競爭

九條假想路徑：階梯續漲、直接加速、深回撤後續漲、急拉崩跌、長盤機會成本、漲跌停未成交、訊號基底變更、同產業一起反轉、退出修復再進場。16個評估交易點／6個檢討點，另保留兩個合成交割點；完整weekday日曆、價格、tape、限價、容量與第二後續合成session交割日都明示，**不是台灣真實日曆或券商資格**。合成中間價格是刻意設計資料，沒有拿來補任何真實缺價。

每條路徑同時跑原A-zero零交易觀察基準、結構續抱、非固定比例參與、適應式退出、全帳戶重配置。後四者只消費fixture當時給的數量意圖及證據，再由數值／成交／風險閘門約束；不是已批准的通用比例公式。數量、20%合成委託限價帶、2,800提案預算與3,000上限只是明標fixture參數。原零交易控制若超限，只作觀察，不可因其事後賺更多就當風險合格建議。

每個方案在每輪承接自己的真實模擬成交與帳戶差異，起始共同資本／權利相同，後續NAV不強制相同、不重設本金。共同外生價格／狀態／容量及候選環境相同；各帳戶現金、持股、可行委託不同是結果。45條合成政策序列不是45個獨立市場樣本。

指標只用全帳戶原始資本與連續淨清算估值：幾何成長、收盤序列回撤與未完成恢復的截尾時間、已發生成本／滑價、現金權重、事後指名股票的參與權重及帳戶峰值到終點回吐。名目現金價格報酬0與退出成本分開。不用單筆報酬除天數、不設事後最高價完美退出基準。這些都是事後描述，沒有預測或實際投資績效。共同硬上限不等實現曝險相同，matched realized exposure對照仍未實作，不能據此宣布某政策或R2勝出。

全部data_qualified、execution_model_qualified、historical_signal_eligible、policy_authorized、live_execution_authorized維持false。原70／2／8／0與來源全部parents／null／UNKNOWN／警告不解除。
