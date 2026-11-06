# 明示合成回放完成後另存評估0.1

最低基線11c914ad5235682822b2c22e07e00d092ab3b6de。本輪只新增外部RUN／READ協調：沿quantity_replay.replay_sequence，先保存／讀回原回放，再沿account_metrics.evaluate_saved評估、另存評估與結果連結。不改原回放／決策／帳務／指標公式、schema或舊READ；不自動選擇、造單、補行情、排名或升正式資格。

## 輸入、保存與結果

capital-evaluated-replay-input/0.1固定schema、synthetic=true、replay_input及evaluation_at。replay_input必明示完整capital-quantity-replay-input/0.1；新入口預檢原來源須為ENGINEERED_ACCOUNTING_FIXTURE_NOT_MARKET，不接受真實資料改標synthetic繞過資格。所有每輪選擇、orders／tape、calendar、原帳權利與限制都由既有輸入明示，原API判定，不預設比例或策略。

唯一operation id沿原規則1～90個ASCII字母／數字／底線／減號。Journal分開存id--request、id--replay、id--evaluation、id--result。request保存完整canonical request_json及指紋；每一階段須保存後讀回相等才前進。replay只呼叫一次；evaluation只對剛保存／讀回的replay呼叫一次，之後另存。停止或不完整回放保留原件、評估明確REFUSED且統計null，不拼接停止前績效或改選方案。

evaluation record綁operation、header／request、完整replay指紋、明示評估輸入指紋、evaluation_at與原評估evaluation_id。result再綁全部階段及必要摘要；評估資格、回放狀態與保存狀態分開。COMPLETED_EVALUATED只表示保存完成且合成評估EVALUATED；COMPLETED_EVALUATION_REFUSED表示保存完成但拒算，退出2。全部正式flags false、主壓力／ranking／selected_strategy null。

已存在任何階段一律不重跑：同請求OPERATION_EXISTS_READ_REQUIRED，不同請求OPERATION_ID_CONFLICT；不重寫舊檔或自動恢復。保存NOT_SAVED／UNKNOWN立刻停止，UNKNOWN不當成功；保留已寫入原件及明示READ入口。單程序範圍，不宣稱多程序exactly-once、真實斷電或自動復原。

## READ界線

READ不接受input，不呼叫replay_sequence、evaluate_saved、生成、會計、Journal.save或網路；不選最新來源，只讀同id四階段。沿原Journal讀取，再檢查保存指紋、原回放input_id、stage binding、來源／帳／checkpoint／latest／token連結、狀態與摘要欄位一致。沒有指標重新計算或帳務重播；自洽SHA不等來源／分錄認證。

缺最終階段只顯INCOMPLETE_SAVED_PREFIX，不補算；錯來源／評估／operation／時間／結果指紋等UNREADABLE且保留原件。READ可讀出已保存的拒算，workflow_status=READ_ONLY但outcome仍COMPLETED_EVALUATION_REFUSED、metrics_status仍REFUSED，不變成合格建議。

## 定向驗收及保留

先凍結精確input／expected、來源指紋及本契約，再實作。只新RUN三份明示合成輸入：無新交易的完整原帳觀察、較早截止仍有待交權利的不完整原帳、當期新資金資格不合格而停止。原source seed只作新fixture素材，parameter_source明示新版本；不重跑舊suite或覆寫舊actual。新RUN實際繼承原回放引擎，不宣稱引擎呼叫0。

必要驗證含保存先後、source精確綁定、有效原帳及null拒算、相同ID不重跑／不同ID內容衝突、四階段UNKNOWN、缺檔／跨階段錯配／自洽篡改摘要拒讀、fresh READ禁引擎／評估／寫檔／網路、原input／原source／帳權利／reserve／latest／token不變。故障／損壞只用新暫存副本，不冒真實中斷。

1101期初cash_claims UNKNOWN、70／2／其中8／真實總淨合格0及來源parents、正式action_resolution0.4、P0-3/P0-4、圖形／人工基底與原未支援不變。無新行情／來源、私人原件、bootstrap、真實producer、市場六方案、九路徑、UI／Android／樣本外、部署交易付費訊息。原唯一Codex依里程碑自審、正常commit/push與固定SHA GitHub原件讀回。
