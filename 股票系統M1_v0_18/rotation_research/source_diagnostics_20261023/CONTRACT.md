# 來源診斷／資格附層0.5契約

1. `source_diagnostics.py`為獨立純核心；`source_diagnostics_sources.py`為外部離線producer。schema `rotation-source-diagnostics/0.5`是附層版本，正式金融來源仍是action_resolution 0.4；嵌入精確parent0.4並保留parent0.3、事件、八來源版本、coverage及舊UNKNOWN。原scope／resolution／producer／action_ledger／core／參數／策略／庫／歷史／頁／ZIP不改。
2. 只採實際取得的官方原件。精確固定URL、原件SHA、長度、HTTP200、metadata／manifest相同、PDF magic、抽字SHA／回傳值／分頁數、帶時區起訖擷取時間、0重試／0跟隨重新導向逐項核對。抽字是衍生物，不加算獨立來源。代理403只有失敗metadata，沒有原站HTTP、原件SHA或可用source；不得變空報告、無事件或法律證據。
3. 台泥復牌公文PDF一頁證明1101上市普通股自2025/8/14恢復交易。文件日期及「8/13公布暫停交易事由」不能單獨當8/13整日停牌起日。未取得的8/13停牌公文另列缺口。新診斷可附相關復牌原件，但舊UNKNOWN、Raw null不改，也不推估停牌估值／交易價。
4. `quote_diagnostic`把官方市場session、個股停牌來源、復牌、缺價及執行資格分開。原日曆仍顯示兩缺價日市場開市，不能當市場休市。只有來源明示的個股停牌日期才可在新診斷記不可成交；不往前後推及其他日期／股票。無來源為UNKNOWN。即使有直接停牌來源，仍不補價、不定估值、不解除缺價拒算。API沒有成交執行政策；execution_qualified維持false。
5. 公開說明書固定SHA與使用者所給相同，765頁中只核第1／55頁（印刷45）。預計發行1,531,510,471普通股是原2867股東的換股對價，實際按基準日股數計；0.2596單位是NEW_2884_PER_OLD_2867，不可變成既有2884股東股票股利。actual_issued_shares及既有2884權利影響維持null，不認證已完成換股。
6. 第55頁截至2026/7/3普通股16,192,000,000股是公司股本快照；6/30經濟部登記是員工酬勞增資登記，不能當上市可交易日或既有股東受配。執行報告的7/7員工增資基準日另存，不借用登記／股本快照日期，不認證2025股票股利實配及可賣日。
7. 執行報告的7/7是盈餘分派除息基準日（record），不是除息交易日；7/27每股1.40發放完畢是公司報告完成，不是個人實收到款。毛額保留原精度1.40，個人淨額、稅、保費、匯費、期初權利、實收均null。6/30、7/3、7/7、7/27各角色、受領對象與source明確分開。
8. `resolve`重用舊resolve_field的明選version／family／issuer／原股／instrument／事件／field／unit／date_role／帶時區observed_as_of門檻；早於觀察、無時區、歷史訊號、錯角色／對象、未知欄及FINAL_LEDGER均拒用。沒有選最新、後見回填或輸入空白補零。
9. 財政部官網此次在代理層403，未對同網域API再請求；無官方頁面／script／API原件，不聲稱本環境已核法規。`parse_mof_api`只接受外部payload，合成測試核TaxVer／Title／Content與所指函令，忽略可變ViewCount；這是未接實際來源的契約分支，不是完成法律原件驗收。即使將來取得一般函釋，也不能單獨證台泥最細來源、個人免稅、零保費／零匯費或淨額，亦不認證歷史公布可得。
10. `qualify`先綁明確新catalog，呼叫不變正式0.4的refuse_accounting，只追加診斷界線，完整保留parent拒算。coverage精確沿用不完整parent，input自填VERIFIED_COMPLETE不能蓋過來源不足。沒有新的成功numeric replay、每日帳、六方案或排名路徑。原72研究窗實跑70拒算、2不足、8換股影響未支援、真正總淨報酬合格0。
11. 新觀察共5條，來自3原件；不是5個獨立公司行動。停牌及一般法律分支用明標合成工程資料測反例，不放進真實catalog、行情、窗口或績效。原0.3／0.4舊結果與歷史完整保留。
12. source producer重建驗等正式0.4、122價量原件、16市場月報；只寫本新目錄，同名不同內容先拒絕（不覆蓋），相同結果不動原檔。網路擷取是本輪明示的一次性動作，離線producer不進網路。未讀101舊圖，未重開UI／file://／Android。
13. 仍缺完整1101／2884行動減資及2026/7/25～10/16權息、2884直接2025可交易日／未圓整實配／畸零股與既有股東換股影響、台泥最後調整及稅務細項、個人淨分配及九起日期初權利。Raw／五年Adjusted／歷史公布／主檔／SQLite未知、historical_signal_eligible=false、primary_pressure_id=null、policy_authorized=false保持；全換／分批比例及觸發仍研究變數。無新UI／Android，NOT_TESTED_NEW_BUILD不升格。
