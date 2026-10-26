# Work接續：資金研究0.3定向修復（未提交）

原工作區`/workspace/Twstockai`。最新已核遠端與本地Git基線仍`6be4333d490bcccfe952c7606dffb802b76cdd5c`；沒有commit/push，0.2、0.3及快照皆為本地差異。下列可直接貼給Work，不能把本文件當Work已取得原件。

```text
接續 blue1998-glitch/Twstockai，分支 dev/m1-v018-chart-annotations。
最新已核遠端及本地基線：6be4333d490bcccfe952c7606dffb802b76cdd5c。
保留ea380cf7d9ae7fa8e204c2b02dfea72f51b3fa01、1085b17ccbbc09269908bb95442ec309910d1399、3b6fe93fe582ba943451374491f081f23af42f59及全部後續／未提交成果。
先唯讀查最新ref、祖先與本地差異；不reset、checkout覆蓋、強推或用main／舊ZIP替換。只有原既有唯一Codex工程，不開第二Codex、子代理或競爭分支。

目前沒有commit/push，七個原tracked修改仍保留；0.2／0.3及快照均未提交，暫存區空，實際新增檔數以新CHANGE_MANIFEST與git為準。GitHub仍0.1，不能冒稱讀到0.3。Work沒有原件時先讀Codex本輪回覆摘要，保持「Codex實讀，Work原件未取得／未讀」；只有正式workspace工具能讀才核本地，不要求使用者搬檔、不自行發布。

本輪Work僅唯讀驗收，不工程、bootstrap、執行測試或producer、commit/push、部署、下單、付費或發訊息。
讀根AGENTS.md、CONTINUE_IN_WORK_MODE.md、PROJECT_VISION.md、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md、M1_CAPITAL_RESEARCH_PHASE1_HANDOFF.md、M1_CAPITAL_RESEARCH_REVIEW_20261025_HANDOFF.md及本新交接最新有效全文。

新證據根：股票系統M1_v0_18/capital_research/repair_20261025。
全文讀REPORT、CONTRACT_0_3、intake、execution、diagnostics、preservation、CHANGE_MANIFEST、tests-final.log、baseline_0_2、before與artifacts。必要原碼core、execution、continuity、eligibility、close_clock、trend、trend_replay、trend_fixtures及repair目錄fixtures／reproduce／test_repairs／verify／build。舊review_20261025、validation_20261024、正式action_resolution0.4、來源0.10與全部parents、P0-3/P0-4／reaction_facts／人工基底契約繼續有效。

修改前封存原0.2的78檔、source/doc patch及逐檔指紋，七個修前probe全保存。五個缺陷實際重現：NOT_QUALIFIED仍買、sellable0變100、09:00提前取得日終995、新前身被拒舊前身接受、過期事實仍買。部分成交取消與到期兩例在原0.2已成立，只補驗證，不冒稱修了不存在的帳務錯誤。

逐項核：
1. 每股新資金review綁當期截止／時點／來源基底／證據ID，未合格增加目標須排除建議及成交。原再進場同市場路徑負例NOT_QUALIFIED不買，明示資格正例1/19買A100；全部正式資格仍false。
2. checkpoint保留opening_unavailable_shares，無來源解除則明確SELLABLE_LIMIT_CONTINUATION_NOT_IMPLEMENTED，不自動把實股變可賣。
3. 明示synthetic ledger_close_proof分開as_of與available_at；09:00不能標日終，延後可知前不能建立下一決策可用帳戶，不推真實收盤或券商T+2。
4. origin與latest decision/account分開，最新前身精確驗指紋／順序，原完整fills／權利／本金和全部已看token續接；舊前身拒絕。看artifacts/reassessment-and-next-round.json。
5. 明示過期／失效不能由新ID復活；有效舊事實可保留原ID經當期review，不變新trigger。未來撤銷不改早期決策。看old-facts-current-review及before／after。
6. 部分成交後取消／到期：原始2180，首輪A80／B7、現金1056.660、現金權利80、股份權利10；原A剩30／B剩13未成交。下一輪沿同一opening追加，終點現金2069.720＋A10×10＝2169.720；2180＝2169.720＋費稅9＋滑價1.28。一般reserve100保持，可用1969.720。A10是既有權利後來交付，不假稱全現金。核fill_order_ids、剩餘量、到期／取消與權利只入帳一次。

最終38唯一方法PASS＝33新增＋5必要回歸；首37失敗／修正批不累加，舊51／46不重跑全suite，probe／builder／10合成序列不算新增測試或獨立樣本。初批1FAIL／2ERROR及修正均保存；最後來源覆核補精確整數對帳與低Decimal精度方法。原CLI READ stdout與舊保存log全bytes一致，未重算。

優先找可推翻上述接線、日終可知、最新前身、權利與預留守恆的反例；不為新PASS重跑舊suite／來源／band-volume。R2/F、信用、期初應付、不中斷外部既有單完整重播、無來源限售解除、真實日終與交割資格及實現曝險配對仍未實作。
只跑一條假想市場的兩種資格變體×五意圖×五輪，未重跑原九路徑45序列；獨立市場樣本0、ranking=null。R1/R2仍須事前凍結共同point-in-time環境、完整權利與逐輪帳、未見切分及purge/embargo、真實成本容量交割、市況與同風險／實現曝險對照；評價全帳戶幾何成長、回撤恢復、成本、現金、大贏家參與與回吐，不用單筆報酬÷天數或事後最高價。R2無穩定額外價值就保留R1。

原70拒算／2不足／其中8換股影響未支援／真實總淨合格0保持，僅核保存檔。完整行動／個人淨額及期初權利／畸零／既有2884影響／歷史可得與原缺價仍缺；不補零、行情、零事件或放寬拒算。所有正式資格false，主壓力未知null，不改策略／圖形／歷史schema，不接UI、不重做人工模式、不重問P0-3/P0-4，不預定比例、永久底倉或策略勝者。
Astra libfile_8ae424394ee88191a64125c72ffdaee6：Codex仍未取得／未讀；Work前輪讀過不等Codex已讀。只有正式檔案工具可讀才全文對照，不HTTP試探／重試拒絕入口或要求搬檔。

交付實讀／未讀、已證／未證、反例及尚未覆蓋邊界，明分保存測試與Work本輪執行0。工程問題回原既有唯一Codex，沒有新授權不自動工程；仍無commit/push授權。最後附最新遠端、本地基線、未提交狀態與可直接貼用的完整下一輪指令，不要求使用者搬檔。
```
