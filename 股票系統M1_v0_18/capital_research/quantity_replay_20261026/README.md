# 受控逐輪回放：可用入口

純API：`from capital_research.quantity_replay import replay_sequence`。按CONTRACT明示原帳、來源、模型、逐輪template、選擇、orders、tape與日終可知證明；呼叫一次即可得到逐輪數量閘門、原執行結果及checkpoint。沒有網頁／資料庫／網路依賴，不產生委託參數或選最佳數量。

只讀成果：REPORT.md、cases/*/{input,expected}.json、after-final/*/actual.json、after-final/summary.json、gate-control-intake／summary、self-review.json。cases/*/actual及根summary／build.log是修前階段，不能當最終source。首次tests-final.log保留一項失敗；tests-gate-control.log是該同名方法補跑，最終15唯一方法，不能算16或把失敗擦掉。

source-versions-before-run綁修前source；diagnostics保留原碼／測試。source-versions-final綁修後17案source；production bridge之後未改，只有測試方法切到新增的強化fixture，見source-versions-final-with-control。gate-control新增輸入及oracle在執行前另存，原所有oracle不改。

完整raw execution／checkpoint保持原0.8指紋，不為了未來隔離重寫或刪ID。numeric_prefix是比較當時數值的明確範圍；原件完整性metadata可因截止後尾段不同而不同。看到COMPLETED_PROVIDED_ROUNDS，只表示明示各段完成，不表示所有委託成交／權利結清或策略有效。

停止後history不是包含新review的可直接resume帳。本版不接外部checkpoint或同區間reassessments；如需繼續，須明示完整新研究輸入及選擇，不跳過拒絕輪、不默認取消舊單。不收私人資料或補真實資格；原已知阻塞保持。
