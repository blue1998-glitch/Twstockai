> 2026-10-22接續更新：下文保留原始人工概念裁決。新的可執行競爭研究、實際條件式資料比較、18／9982／36工程驗證及完整報告已保存於 `股票系統M1_v0_18/rotation_research/WORK_HANDOFF.md`。策略與真實總淨報酬仍未驗證；不把原探索意向升為正式配置規則。

# P1-7 Work 接續：換股相對強弱已答，執行方式未核定

分支：`dev/m1-v018-chart-annotations`。先讀根 AGENTS 與本目錄 [README.md](README.md)，再依既有 M1 入口延續，勿以 main 或舊 ZIP 覆蓋既有成果。

本輪使用者明確指出：要比較 B 是否強於 A、A 是否值得繼續等待；誰更接近關鍵點位、且已經真正跨過關鍵位置，研究順序可優先。仍在摸索怎麼衡量特定時間的收益是否足以讓換股有利；以前多為全賣全換，認為應研究分批，但不清楚最佳方法。**策略未裁決**，不要自行指定批數、比例、買賣條件，亦不要把過去虧損設為新候選必須先賺回的障礙。

下一步 Work 先開發研究方案：同一截止日期比較持 A、換 B、暫持現金與試驗性分批；各候選使用同基底價量、當下可知的關鍵價／動能／結構資訊及相同初始市值。向後評估多尺度淨績效、下行風險、機會成本、交易稅費與滑價，嚴禁偷看未來。分批是競爭性研究候選，不是已批准的策略。先有可核驗的正反例與結果再請使用者裁決重要差異。

狀態：`PARTIALLY_ANSWERED_WITH_OPEN_DESIGN_CHOICE`；`classification=NOT_VALIDATED`、`historical_signal_eligible=false`、`rotation_policy=NOT_APPROVED`、`action_and_flywheel=NOT_EVALUATED`。本輪只做文件與手工原則保存，無新行情、引擎修改、模擬回測／Android 實機驗收。保留最高資金閉環目標、全部舊圖/策略/資料、人工 Raw/Adjusted 模式與已核答覆。
