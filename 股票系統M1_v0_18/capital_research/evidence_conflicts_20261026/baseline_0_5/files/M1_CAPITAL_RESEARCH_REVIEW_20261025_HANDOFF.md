# Work接續：本地研究修復0.2與長期趨勢唯讀驗收

本輪依使用者要求沒有commit／push。最新已核遠端與本地Git基線均為`6be4333d490bcccfe952c7606dffb802b76cdd5c`。新檔只在原共享工作目錄，不能冒新GitHub提交或讀回。程式／契約patch為`/workspace/capital-research-review-20261025.patch`，大型JSON證據另在原路徑依manifest可讀，不要求使用者搬檔。

以下可直接貼給Work：

```text
股票系統｜Work唯讀驗收資金研究0.2本地差異

接續blue1998-glitch/Twstockai，分支dev/m1-v018-chart-annotations。
本次最新已核遠端SHA與本地基線：6be4333d490bcccfe952c7606dffb802b76cdd5c。
保留固定工程ea380cf7d9ae7fa8e204c2b02dfea72f51b3fa01、1085b17ccbbc09269908bb95442ec309910d1399、3b6fe93fe582ba943451374491f081f23af42f59及全部後續。
先唯讀核最新ref／祖先與本地差異，不回退、強推或用main／舊ZIP覆蓋。

目前沒有commit／push：0.2程式、研究契約與證據是未提交本地差異。GitHub仍是舊0.1交付，核到6be4333d不等讀到新0.2。用正式共享檔案／workspace工具讀/workspace/Twstockai；若Work只能讀GitHub，明列新檔未取得未讀及工具限制，不要求使用者搬檔、不自行發布。工程仍只原既有唯一Codex，未有新保存指示前不commit/push。

全文讀根AGENTS.md、CONTINUE_IN_WORK_MODE.md、PROJECT_VISION.md、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md、M1_CAPITAL_RESEARCH_PHASE1_HANDOFF.md及本M1_CAPITAL_RESEARCH_REVIEW_20261025_HANDOFF.md最新有效內容。讀股票系統M1_v0_18/capital_research/review_20261025/REPORT.md、CONTRACT_0_2.md、OUT_OF_SAMPLE_PROTOCOL.md、intake.json、execution.json、diagnostics.json、preservation.json、CHANGE_MANIFEST.json、tests-final-evidence-bound.log；對照before四份與artifacts/after四份重現紀錄。必要原碼：core.py、execution.py、continuity.py、transition_risk.py、trend.py、trend_fixtures.py、trend_replay.py、cli.py及test_review.py／test_trend.py。原action_data、正式action_resolution0.4、來源0.10與全部parents、P0-3／reaction_facts／manual_basis契約及原件／警告繼續有效。

本輪實做：四項靜態推導都先保存輸入／預期／實際／版本再修。原A未賣B40仍買使shared曝險1800>1100；交割後沿1/5決策買B99；不同OPEN／漲停tape可比較；token resume可將帳戶重設到10000。before原檔保留。修後逐觀察核實股／股份權利／可能買單，不給未成交賣單或避險額度；超限／持倉mark陳舊則擋新買，無法退出仍照實觀察，不保證強制成交。
等待交割買單必綁新checkpoint、新帳戶與證據截止、新decision_id；失效即使仍在限價內也取消。正面例已驗1/8新決策後1/9成交。compare_jobs綁共同外生價格、容量、狀態、available_at與交割路徑，orders可不同。靜態目標Pareto不含等待／未成交，不當政策支配，也不作淘汰可行政策的理由。
resume必有原帳checkpoint，下一帳戶不能加錢、掉權利或無聲刪單；有限continuation沿原action_ledger opening與全部fills追加，不另開帳、不重設本金。檢討點須已無買進應付，有效舊單須明示取消或已知到期；期初應付及不中斷外部既有單完整重播仍未實作，不把有限成功路徑冒稱完整生命週期。

本輪最終51個唯一方法PASS＝46新增＋5必要回歸，不是舊46重跑，不累加21／41中間批、smoke、builder或45條合成序列。完整舊suite、真實窗口producer／新資格／市場六方案、UI／Android皆未跑。開發中的基底變更先raise、共同前綴10/10.0精度污染、漲跌停未覆蓋委託、到期誤要求再取消等診斷與修正均保留。最終無未解測試失敗。

「10倍股」只指超出原持有預期仍可能延續，不要求十倍或無限報酬。trend是明示已知圖形事實的可逆研究狀態，不是新圖形辨識公式。保存截止、來源／證據ID、支持／反證／未知、持有與加碼資格、硬風險和替代機會；不重問P0-3／P0-4。可續抱不等可加碼，事後winner不進決策、不放寬風險；到目標、固定獲利或天數不自動退出。四種壓力知識分開，未知不補近期高點／無限空間；新小階梯不解除舊主要壓力。虛擬用途必分割實股，權利在單一帳保留一次。

讀artifacts/summary.json與paths各fixture.json／competition.json：階梯上漲、直接加速、深回撤續漲、急拉崩跌、長盤、漲跌停未成交、基底變更、產業一起反轉、退出修復再進場。九路徑初始decision_id相同。每條跑原A-zero觀察、結構續抱、可變參與、適應式退出、全帳重配五種外部數量意圖，各五輪承接自己的成交／現金／權利，原始共同資本2000。weekday日曆、第二後續合成session交割、20%合成限價帶與數量預算只是fixture，非真實日曆／券商資格或正式策略。45序列不是獨立市場樣本，ranking=null。零交易控制超限不可因事後較賺而當合格建議；相同上限不等實現曝險相同。

優先驗途中風險與可能成交子集合、交割重評繞過、共同市場漏綁與下一帳戶完整追溯；再檢查九路徑是否有足以反駁續抱／保留參與部位的情況，是否把事後標籤回填、較小階梯暗自解除舊壓力。指標只看全帳戶幾何成長、回撤恢復、成本、現金、贏家參與與回吐；不用單筆報酬÷天數或事後最高價判勝負，不預定參與部位或R2最好。
依OUT_OF_SAMPLE_PROTOCOL事前凍結共同point-in-time候選／市場環境、完整資本權利／逐輪連續帳、未見時間切分、重疊事件／產業／形成點污染的purge/embargo、真實成本容量交割、不同市況及同風險／實現曝險對照。R2/F未求解；沒有穩定額外價值就保留R1，不用合成案例宣布勝者。

70拒算／2不足／其中8換股影響未支援／合格真實總淨0保持，只核保存檔，非本輪producer重跑。完整公司行動、淨分配、個人期初權利、實配畸零、歷史可得等仍缺；未知不補零／行情／零事件。全部parents、Raw null／UNKNOWN、警告及false資格保持。R2/F、信用、期初應付及不中斷外部既有單完整重播未實作。
Astra libfile_8ae424394ee88191a64125c72ffdaee6：Work已讀459行／48887bytes為使用者提供狀態；Codex仍無正式Library reader，全文未取得未讀，無HTTP試探／重試。Work若已有全文可對照差異，明分全文證據與Codex未讀範圍，不要求搬檔或把摘要冒全文。

Work只唯讀驗收，不bootstrap／工程寫入／測試／commit/push／開第二Codex或子代理。不改正式交易／圖形規則或歷史schema，不接UI／重做人工模式，不部署、下單、付費、訊息。明確缺陷交回原唯一Codex，附輸入版本、預期／實際與最小接受條件；未有新保存指示仍不commit/push。真正核心歧義用正反例說清，不要求使用者猜比例或代做工程。
最後分列已讀／未讀、已證／未證、缺陷或反證、未實作／未執行／未測／資料不足；提供當次最新遠端SHA、本地基線、未提交狀態及給Work或原既有Codex的完整可貼指令，不能只說交給某模式，也不要求手動搬檔。
```
