# 資金配置第一階段接續

本輪工程固定SHA與GitHub讀回收據見 `deliveries/m1-capital-research-phase1-20261024/GITHUB_READBACK.md`／JSON；最新已核提交以該收據和最後回覆為準。起始遠端392b94a4，1085b17／3b6fe93及全部後續保留。

下一步只用 **Work** 做研究契約與反例唯讀驗收；原既有唯一Codex仍是後續工程／寫入對象。以下是完整可複製指令，實際最新已核SHA亦列於交付收據，不能把文件中的起始SHA當分支最新。

```text
股票系統｜Work唯讀驗收Astra資金配置第一階段

接續 blue1998-glitch/Twstockai，指定分支 dev/m1-v018-chart-annotations。先唯讀查最新ref，核包含1085b17ccbbc09269908bb95442ec309910d1399、3b6fe93fe582ba943451374491f081f23af42f59、起始392b94a4f29b2e53fbfc0b7bda8a3fc1d0592b25與deliveries/m1-capital-research-phase1-20261024/GITHUB_READBACK.md／JSON記載的固定第一階段工程及後續讀回提交；保留全部後續，不回退／強推／用main或舊ZIP覆蓋。最新已核SHA請以本輪最後交付的完整SHA及收據核對。

先讀根AGENTS.md、CONTINUE_IN_WORK_MODE.md、PROJECT_VISION.md、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md最新有效段落及M1_CAPITAL_RESEARCH_PHASE1_HANDOFF.md；全文讀股票系統M1_v0_18/capital_research/README.md、INVENTORY.md、CONTRACT.md、REPORT.md，validation_20261024/intake.json、execution.json、diagnostics.json、preservation.json及tests-final.log；再讀delivery README與固定GitHub讀回。需要原碼時讀core.py、allocation.py、execution.py、evidence.py、cli.py、build_evidence.py及test_mechanisms.py。

必讀相關原契約：rotation_research/README.md／WORK_HANDOFF.md、action_data_20261022/CONTRACT.md、正式action_resolution_20261023/CONTRACT.md／WORK_HANDOFF.md及resolution_validation_20261023；最新subsidiary_proposal_20261023/CONTRACT.md／WORK_HANDOFF.md／window-qualification.json與0.9～0.3全部有效parent契約；structure_state/README.md及reaction_facts／manual_basis相關來源綁定。保存狀態仍70拒算／2不足／8換股影響未支援／總淨合格0；本輪只核保存檔，不是重跑producer。

本輪46個唯一新定向方法PASS，初輪40含一失敗及43中間批不累加；builder／CLI／新解壓重現也不當新測試數。原帳務核心不改，所有fill交原action_ledger，無第二資金帳。三層證據／新資金／移轉分離、零交易與A～F契約、共同權利資本、多候選預留、成本／交割、未成交與容量、事件去重及READ無重算已驗。R1為有限事件／風險預算可行性及成本感知全配置；C/E數量只是外部合成提案，沒有最佳比例。R2/F為NOT_IMPLEMENTED，須未來樣本外證明相對R1增益，未預定勝者。

請直接讀validation_20261024/artifacts的input.json、execution-input.json、records、common-capital-comparison.json、accounting-evidence.json、future-isolation.json、synthetic-cases.json、broker-credit-distinction.json及R1-full-proposal.json；另讀validation_20261024/real-source-gate-probe.json：這是本輪唯一1次0.10→0.4拒算接線probe，非70窗producer重跑，daily／journal空、總淨null、numeric replay=false。初次未綁正式events而拒絕的診斷保留，不放寬原契約。核同一決策前綴在A大漲／B大漲／雙跌時整個decision一致，完整性metadata分開。核2000=1991.020+稅費6+滑價2.98、賣款1/8日終結清前不得買、同NAV不同權利拒比、多候選及既有預留不可重用現金。

檢查A賣出B漲停未買、A跌停未退、部分賣／買及容量共用；小優勢可不交易、風險超限時band不得阻擋減風險；B假突破A漲與B加速、雙跌現金有利與持續上漲拖累／再進場慢皆保留。現金名目報酬0與退出成本5分開，估計終點退出不是實際成交。不拿合成數值宣稱市場績效、使用者實績或正式圖形通過。

券商額度有另列明示合成資格，完整借貸帳務未實作並拒絕重播。期初應付／既有待成交的決策預算已支援，但既有帳務能力不足以重播，明確拒絕。日內／複雜權利／缺價／未知淨額不默默簡化。建議不把data_qualified、execution_model_qualified、historical_signal_eligible、policy_authorized、live_execution_authorized升true。正式主壓力／參照未知保持null，不補近期高點；量峰群不升正式代表線。

Astra_Work_v1_0_資金配置核心研究.md：Library ID libfile_8ae424394ee88191a64125c72ffdaee6，https://chatgpt.com/library?file_id=libfile_8ae424394ee88191a64125c72ffdaee6&account_id=personal。Codex本輪正式工具盤點沒有Library reader，全文未取得未讀，未發HTTP請求。若Work已有正式檔案工具可讀，優先讀全文、明列與本輪契約差異；工具不能讀則保持待讀，不HTTP試探登入、重試舊拒入口或要求使用者下載上傳。報告是研究設計，非正式策略批准或獲利證明。

Work本輪只唯讀驗收，不bootstrap、工程、產品測試、commit/push，不啟動第二Codex／子代理。對照研究意圖逐項列「機制已驗／介面未實作／未執行／未測／資料不足」，優先找能推翻本輪主張的具體反例；不要為看結果再重跑舊驗收、來源或已結清band-volume，不重問P0-3／P0-4，不訂未知比例／固定檢討天數。

保留所有來源版本／parents／原件／歷史／Raw null／UNKNOWN及舊警告，私人原件不公開；所有已拒入口不重試繞過。完整行動、個人淨分配／期初權利仍不足，不跑無資格真實每日淨帳／六方案。人工Raw/Adjusted路由已存在，不做新UI／重做模式。不改正式規則、歷史schema、main，不部署、下單、付費或發送訊息。

若找到明確可重現缺陷，交回原既有唯一Codex：先核同分支最新與全部祖先，按最新AGENTS必要準備、保留既有差異；只修對應隔離capital_research及必要相關測試，不重建帳或放寬資格，保留失敗診斷。同分支正常提交、提交前再核遠端、固定SHA與GitHub讀回；不強推。若只是研究核心歧義，Work先用合成正反例說清，只有實質歧義才詢問，不要求使用者猜比例或代做工程。

最後提供本輪實讀範圍、具體契約／反例差異、尚不能證明事項，指定Work或原既有Codex下一對象並附含最新已核SHA的完整可複製指令；不能只說交給某模式，亦不要求手動搬檔。
```
