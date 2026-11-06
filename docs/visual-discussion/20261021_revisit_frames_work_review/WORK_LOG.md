# 本批實際作業

起點7c115b9cba5d6ca0963e82754912554ba0669cfa，dev/m1-v018-chart-annotations。已核HEAD、讀三根入口最新節、前批完整WORK_HANDOFF及PROJECT_VISION；全部歷史前鏈保留。

1. 兩次臨時唯讀探查：先比較完整窗收盤格點穿越（A／B最多皆4），再比較已出現低／高／收盤參照的三段側向造訪，看到「歷史重訪」與「當前位置」須分判。診斷結果及方法限制存hypotheses.json，不把全窗後見格點冒稱歷史事件。
2. 新revisit_research.py driver實際3次，皆完成。首版完整登錄含重複現值視圖，gzip2555223 bytes；第二版改共用末K及來源缺日快照，可重建現值，835515 bytes；第三版再將重複長ID改共用事件表索引，135169 bytes。後兩次只改無損保存布局，指定案例數字保持，未改discover邏輯。舊資料與上批driver未重跑。
3. 新verify_revisits.py實際1次通過。以不同的逐參照離線枚舉獨立核243觀察、31410重疊見證出現，去重937事件／430框；每個現值視圖由共用快照無損重建，31410項相等。十一外部截止107去重前綴、截斷／追加事件框ID穩定、未來價格與未來列缺日污染、正仿射關係、合成常數／單向／相等／返回越界／影線越界／遇缺重累積、5/13影線31.40仍登錄通過。這不是分類準確率、概率或獨立市場驗證。
4. 新build_figures.py成功1次，PDF191545 bytes，SHA256 2b058546802228102e27a30d5733b0f2f3877f2b8b4e588ee8a83770e59a084c。Poppler三頁渲染逐頁實看，無文字疊合、裁切或缺字；無需第二次繪圖。底色受原K日期與高低範圍限制，量圖分開。舊圖重建0。
5. 三PNG用PIL驗、複製fsync、逐bytes回讀再驗，人工QA與最終PDF／PNG指紋綁定。研究靜態圖不是新Android／瀏覽器驗收。數值verify後才更新圖QA狀態；新變更不能借用本批收據。
6. 新增本目錄與三根入口最新節，完整舊文字保留；同分支保存，固定提交逐檔回讀，收據另存GITHUB_READBACK.json；實際提交及成功以該收據與HEAD為準。

無原核心MA/MACD/pivot/box/reaction重算、原CLI／adapter／source-query、bootstrap、舊14／22／60等產品測試或前批362／208／21檢查重跑；無新行情、新瀏覽器／Android、子代理、部署付費交易訊息。不改main、原核心策略參數、來源舊圖。正式形成與選擇未定，分類NOT_VALIDATED、用途NOT_ESTABLISHED、行動NOT_EVALUATED、Android NOT_TESTED_NEW_BUILD。
