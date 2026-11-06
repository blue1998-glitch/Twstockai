# 外層數值環境定向驗證與自審

## 範圍與實際結果

原/workspace/Twstockai、dev/m1-v018-chart-annotations，起始本地HEAD與遠端均3b472ae8575f4f4f6c5acaf504f29d0ded078bdd，tracked／index／untracked皆0。只原唯一Codex，無子代理、worktree或新分支。

先保存本輪契約、精確輸入／原期待指紋及原source，再執行修前。三主例重用 quantity_after_retry_20261027/cases 的原完整請求、after-final 的完整actual與既有五組contexts；wrong-latest、tampered-token-history、search-limit只作直接相關必要回歸，不重跑舊20案或原回放。

| 主例 | 正常／ROUND_UP／ROUND_DOWN修前 | Inexact控制修前 | 狹窄指數修前 | 五組修後 |
| --- | --- | --- | --- | --- |
| 新獨立觸發 | 三組完整相符 | Inexact，無結果 | Overflow，無結果 | 五組完整相符 |
| 舊觸發 | 三組完整相符 | Inexact，無結果 | Overflow，無結果 | 五組完整相符 |
| UNKNOWN資格 | 三組完整相符 | Inexact，無結果 | Overflow，無結果 | 五組完整相符 |

「相符」指完整外層JSON、內部generation、帳戶／資格／所有身分皆與原件相等；不是摘要、尾數容差或只核股數。每筆actual有呼叫端前後狀態、精確input_id、當時production指紋及完整例外。完全相同內容直接指向舊原件的path／bytes／SHA及完整結果身分；不同內容須完整另存，本例沒有不同的成功輸出。

## 原因與最小修復

舊公開外層只有localcontext()與prec=50。雖然內層quantity_candidates.generate已獨立隔離，外層先執行validate_checkpoint與account_at_checkpoint，其原帳證明仍繼承呼叫端traps、捨入、flags與指數範圍。

為確認邊界，修前另對新觸發的兩個已重現設定保存完整stack及呼叫計數：bridge1、action_ledger.replay1、內層generate0、simulate0、retry0。Inexact在原action_ledger.py:221的scenario_net_return除法中斷；Overflow在:141的期初估值乘法中斷。兩者皆經quantity_after_retry.py修前:82的validate_checkpoint，證明不能只再改內層產生器。

只改quantity_after_retry.py：Decimal import、revision常數及公開外層local Context。明示50位／ROUND_HALF_EVEN／Emin=-999999／Emax=999999／capitals1／clamp0／空flags／標準InvalidOperation、DivisionByZero、Overflow traps，涵蓋完整公開呼叫，退出後呼叫端不變。implementation revision0.1.1，原輸入／輸出schema0.1不變。_generate本體、quantity_candidates、continuity、action_ledger、費用／風險／資格及其他引擎source全不改。舊READ不重算或隱式遷移。

## 必要驗收與資金複核

五唯一方法、五次方法執行首次全部通過；沒有中間失敗或為增加PASS重跑。方法分別驗：保存修前／修後與中斷位置、原帳及候選完整接續、preset旗標／純呼叫、三個必要拒絕反例、新程序DefaultContext隔離。修前15控制、2個邊界診斷、修後15控制及測試中的8次公開呼叫，共40次有限診斷，不是40項測試或40個市場樣本，不累加任何舊5／6／其他PASS。

額外資金複核：

- 原資本1430、當期估值1425.100、現金275.100、reserve100與A60/B25/C2逐欄核原保存值，不將當期估值重開本金。
- 完整checkpoint仍等於原輸入，原opening／原帳及全部fills、order_states／未成交歷史保持；目前無活單、無應付，不擴張其原未支援接續。現金及股份權利照原row逐欄保留，不把UNKNOWN補零。這不是新增逐輪回放或只憑終點相同宣稱中途無重用。
- 精確latest決策／帳戶、兩個REJECTED／ACCEPTED attempt及12歷史token保持；當期候選基準包含歷史token，新批沒有借舊review重新取得觸發資格。
- 新獨立觸發可競爭，舊觸發與UNKNOWN的增加買進仍拒絕；全換仍WAIT_SETTLEMENT_REASSESSMENT。其他持股C2不消失，沒有選勝者或宣稱全帳已清倉。
- 錯latest、遭改歷史token與搜尋超限在normal及preset均完整等於原拒絕結果，不提升資格或改理由。
- fresh程序DefaultContext與getcontext皆設惡劣條件，輸出仍完整相同，input、呼叫端及DefaultContext不變。實際bridge1／generate1、原ledger核對14次，simulate／replay_sequence／retry／Journal.save各0，監看禁止寫檔及網路。不是宣稱所有ledger函式0或沒有核原帳。

原oracle、舊actual／log／manifest與全部重用來源均以指紋保全。原始source與新source分開，沒有覆寫歷史。

## 未擴張、未測與下一步

只修已完成0.3結果的公開轉接入口，不宣稱獨立core.decide／resume_decision、execution.simulate、C原單重評、allocation.full_transfer、直接checkpoint／action_ledger或舊trend回放已全面隔離。其餘公開入口的靜態缺口保留在本對話上一輪盤點；不把它們拆成無限helper待辦。

沒有舊suite、完整20案、九路徑、真實producer／資格重算、市場六方案、UI／Android、樣本外或新行情／來源。R2/F、信用、期初應付／外部活單、來源認證、自動解除衝突及完整分叉等原未支援不擴張。1101期初cash_claims UNKNOWN、70拒算／2不足／其中8換股未支援／真實總淨合格0、正式false／主壓力null與來源0.10全部parents、action_resolution0.4、P0-3／P0-4、reaction_facts及人工基底保持。Astra及第一工作區救援原件未取得未讀；不推定890檔存亡。

原唯一Codex依里程碑自審、正常commit/push及GitHub固定SHA讀回，無人工操作、不預設Work逐輪驗收。未定觸發、期間、風險／資金及分批規則仍由Work與使用者決定；本輪未升待驗假說為交易規則。沒有部署、下單、付費或訊息。

下一項可留Codex，有限確認直接決策及checkpoint續接兩種入口，重用已保存初始／跨輪請求與控制，先證實影響再決定最小修復；需特別檢查resume_decision在內部localcontext前的bind_resume。只屬既有工程，不新增策略；本輪不擴張實作。
