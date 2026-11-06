# M-CAP1 0.1｜同帳戶明示行動比較

只接受完整、純合成的保存行動輸入／執行收據／checkpoint。沿用 cash_action、cash_action_execution、action_account_metrics、account_metrics、原 execution／lifecycle／action_ledger／Journal；新 compare.py 沒有回報、成本、估值或回撤公式，也不生成委託／成交。

比較前逐支調用原 evaluate_saved，再要求 account_source（含完整checkpoint）、decision_template（含每股證據及成本／執行模型）、policy、原 ledger、close proof、tape、observed_until、evaluation_at 完整物件相等。原始期初／權利／reserve／tokens及決策前日帳前綴不變；不是只比ID。任一分支不完整、混用帳戶／資訊／模型／時間或來源就整組拒比。沒有跨帳戶、真實帳戶或自由輸入策略功能。

三支共用 reduce-B3 的資料集。舊 v01-hold 比賣出分支多一份 B-step2 證據，不能把舊三份直接當公平比較；用現有 HOLD 0.1 intent、共用資訊及空 orders 重新由原引擎計算。reduce／exit重播與原收據完全相同；新HOLD的完整帳戶曲線／成本／回撤等財務欄與舊HOLD相同，不表示兩種資訊集相同。

全部沿原 2026-01-05～01-12八個日曆日，原始淨值1180。01/08 17:00選行動，三支選擇前帳戶皆現金858.860、B7／C2、一般預留100及原權利；不從選擇點重設本金或截去原成本。選項股數僅保存合成案例，不是用戶比例建議。01/09成交、01/12明示交割，原80現金權利及C2交付不是額外本金。C持股2→4不冒新買入。

主畫面用 statistics.period_accrual_growth、maximum_drawdown、terminal_accrual_equity 與 ledger.daily；是原帳戶已發生成本後、尚未假設全帳清倉的應計淨值。recorded_fill_fee_tax是實付費稅；原滑價已在原成交價及淨值中，不能把實付費稅當全部摩擦或再減一次。terminal_estimated_exit_cost／terminal_net_*只是原引擎假設期末清倉，留進階，不當實際清倉或個人實收。

三支均仍持C4。EXIT_SELLABLE_HOLDING是退出B，不是全帳現金化；全退出持現金無全資產訂單／成交及權利處理證據，NOT_IMPLEMENTED、metrics=null，畫面不顯示舊指標或零值。回復日期被截尾仍未知，僅顯示截至期末未回復及原觀察天數。零值只取確有原值欄位，缺值顯示尚無足夠資料。

只做幾何與格式轉換的離線SVG／數字顯示，完整精度保留JSON；三線共用固定尺度，無勝負排序或自動選優。原完整收據仍Journal保存；portable只是小於512KiB的無損物件表示，不冒原Journal bytes相同。

所有來源／parent0.10及以下、正式策略、引擎、資料庫、P0-3／P0-4、真實結果與head不改。execution_qualified／historical_signal_eligible／policy_authorized=false，primary_pressure_id／imputed_close／valuation=null。只限合成工程，不能認證市場績效、策略勝負、真正個人淨額或可交易性。
