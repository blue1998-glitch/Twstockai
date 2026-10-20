# 最新裁決（2026-10-20 21:46:37 台北）

使用者對第2頁截至10/7是否已足夠辨認整理，回答「足夠辨認了」。USER_CONFIRMED_DO_NOT_REASK；[裁決及完整續接](../20261020_recognition_timing_user_decision/README.md)。下方問題與timing-evidence／verification是生成當時歷史快照，已由新裁決取代；原圖不重畫。10/7非已定最早日，無原核心快照資格不變，historical_signal_eligible=false、primary_pressure_id=null。

---

# 2884 整理辨認時點｜Work 真實截點圖

本批承接使用者已確認的「上漲中短暫回來整理，後來再漲」，不重問本例是否整理。新問題只研究較早截點是否已有足夠資訊辨認；尚無答案，不把後來標籤倒填歷史。

入口：[可放大三頁向量圖冊](output/pdf/m1-2884-recognition-timing.pdf)。第1頁是2021/10/18至2026/10/7長背景1207筆；第2頁是2026/5/4至10/7的109筆；第3頁是同起點至10/14的113筆。近期兩頁價格刻度相同28–51。page-1.png、page-2.png、page-3.png是原尺寸預覽。

**唯一新核心判讀：只看截至10/7的資料，是否已足以辨認這個整理區間？還需要10/7以後更多K線才足夠？** 第3頁供較晚截點對照；不要求指定最早成立日、正式區界或交易條件。狀態PENDING_USER_REVIEW；「下一步」本身不算答案。

10/7的原K線、MA、MACD存在；原包15個已保存核心結果與numeric_frame並沒有10/7，因此saved_core_result_id及saved_numeric_frame_id=null。本批只截取原資料，不冒充10/7原核心回放。10/14則讀原1211筆結果指紋，未重算。兩頁不含10/15、16或其指標。原9/17高47.35與10/1低44.20僅標示原日值，不作正式箱頂底、成員或本次新確認點。

這是看過後來走勢後的截點複核，**不是盲測、實際歷史選取或歷史公開可得性證明**。截取既有指標不等於本輪獨立驗證指標在歷史上沒有前視；原前綴測試只是歷史紀錄，本輪未重跑。當前人工整理標籤USER_CONFIRMED保留，兩截點足夠性皆null待判，historical_selection_time=null、historical_signal_eligible=false、primary_pressure_id=null。

實際執行build_review.py一次：核原HTML SHA與包指紋、原抽取來源全等與SHA、兩截點來源數及原值、10/14保存結果指紋、指標序列長度及截點外零列；讀取保存值繪圖，核心／MA／MACD重算0次。PDF三頁均重新渲染實看，另看第2頁400%裁片。完整記錄見timing-evidence.json、verification.json。最初查詢保存結果時把as_of誤從context取值，唯讀檢視KeyError後改讀頂層並查明10/7無快照；無產出被錯誤結果覆蓋。

沒有產品修改、reaction或source-query重做、CLI／adapter／bootstrap／14或22或60等舊測試、新行情、ZIP、瀏覽器或Android驗收。Android NOT_TESTED_NEW_BUILD，file://不重試不繞過。Raw公司行動／五年Adjusted／歷史公開可得／九待核非窮盡日曆／Darvas／SQLite未知；正式成員區界代表、增量量權重、重要性衰減、合併直接承接、解除生命階段未知。相等不補過破、OHLC不證日內先後、不同窗不排名。

仍在Work研究辨認時點，不交Codex實作未定算法。完整續接見[WORK_HANDOFF.md](WORK_HANDOFF.md)；逐檔GitHub精確回讀及研究提交見GITHUB_READBACK.json，收據提交亦另回讀。原核心參數策略庫歷史舊頁案例及main保留。

