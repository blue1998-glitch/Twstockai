# 接續：離開後持續追蹤已有有限證據，正式角色／形成規則仍研究中

repo blue1998-glitch/Twstockai；分支dev/m1-v018-chart-annotations；本批起點bbc85a7f5b6c587ae97bbd7c185d71b3f6ba5654。先核實際HEAD保留所有後續成果，不用main或舊ZIP覆蓋。最新研究／收據提交由本目錄GITHUB_READBACK.json與實際HEAD核定。

先讀AGENTS.md、CONTINUE_IN_WORK_MODE.md、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md最新節、PROJECT_VISION.md、本目錄README.md、summary.json、selected-followups.json、boundary-families.json、pool-followup-summaries.json、verification.json、manual-qa.json、WORK_LOG.md、GITHUB_READBACK.json。完整歷史與來源恢復限制沿../20261021_stop_retain_followup_work_review/WORK_HANDOFF.md及其前鏈。不要重問已答案例或把舊執行算本批重跑。

## 新進展

前批首次完成收盤離開前外包凍結、後來整根同側在外提停止／新種子／延續三分支，仍不選。前批整根事件後pending清掉，本批不是改舊方法，而是讀不可變舊事件，另建track(source,event,cutoff)持續追蹤該凍結框。逐筆保留是否整根仍在離開側、是否接觸跨越邊界、完成收盤在框內／離開側／對側，首次後來接觸與首次後來收回分開。返回不抹除舊離開事件、不自動推正式合併或否定已答終點。相等含邊界接觸／框內，不補過破；OHLC不推日內次序。

遇事件後原列待核缺日時，追蹤停於缺日前的保存筆，資格保留，不跨疑點推返回。原框已跨缺日也保留標記。缺日名單不完整、Raw公司行動／歷史可得等未核限制不變，不把沒有列缺日當完整認證。track不得使用事件尚未知的截止日，較晚資料只更新較晚輸出，不回寫早期。

後續種子以整根事件當日為第一筆，新收盤轉向必須等右側不等收盤，平台保留起末日與可知日；種子內高低兩方向俱有只是雙向路徑描述，不升已形成區間，不取代原pivot或5/13最高影線代表。formal_end／membership／selected_alternative／formed_interval仍null，primary_pressure_id=null、歷史選取null／historical_signal_eligible=false。

G2首事件2/21新種子1筆；2/22低37.85等原凍結上界、收38.05仍在上，是接觸不是收盤返回；種子2/22低收於2/23可知，2/23高收於2/24可知；3/1 C37.80回原35.90..37.85內。第二個2/24事件原框35.90..38.50也於3/1收回。不同框各自追蹤，不能因後來收回就把所有來源合併。G2完整人工時間涵蓋2023/1/16至8/16及5/2 H40.25代表已答；本批只外部範圍驗證，不冒稱自動找到。全窗原列8/3缺日仍帶資格；早期2月至3月觀察未跨該處。

ABC首事件6/3新種子1筆；至6/13含本日共9筆，全部整根在28.45下，未碰／未收回僅限這個截止，非永不返回。6/6 C27.55局部高收於6/9可知，6/10 C27.15局部低收於6/11可知，開始有自身往返；還不是新正式區間。原4/7至6/2共39筆、6/2創低仍在內、6/3在外及5/14區內跳空保持，不反覆詢問。後見差異不能倒灌6/3，更不能用必須等9筆或等雙轉向作通用規則。

2884 10/16事件恰為來源最後保存日，只有種子1筆，無之後資料，後續返回／停留答案不造。10/7足夠辨認及完整上漲整理再漲已確認，9/17非正式起點、10/15非核定正式終點。10/7原核心／numeric_frame無仍null。

## 避免重複候選灌票

按股票、事件日、方向、跨越價位歸組，保留每個原事件／提案ID、完整上下框、起日、離開日、框末日與跨越邊界原K日期。群組是相關證據索引，不是正式同結構／合併、去掉來源或獨立樣本。ABC在6/3的24同日事件只跨28.45／28.70；2884在10/16的59同日事件只跨47.30／47.35，不能24票或59票。六池633筆監看歸119池內群組，跨截止重疊也保留；不同群組亦不自動當獨立支持或固定尺度。

## 下一個具體研究目標

仍Work：將「對舊參照的實際返回／持續分離」與「後續種子自己的價位停留、雙向路徑、最高影線代表」合看，研究有區辨力的形成與角色依據。用現成自動候選池、八逐時點軌跡和廣角圖，不再只重核同例數字／堆欄位。既有證據可直接推導的工作連續做，真正新的核心歧義才帶足夠廣角可放大實圖問，已答案例不問。

不能以創低、跳空、整根離開、雙收盤轉向、後來未回到任選截止、同價候選很多，任一單獨當通用正式終點／新整理充分條件；不能硬編日期、最短最長窗或用未來返回提前選擇。返回可新增較大延續／回測研究證據，尚不足決定同一結構；新種子有自己的往返也不能強制拆離較大G2。正式代表／成員界／合併承接／重要性／生命階段仍未定。未定算法不交Codex硬編，已定可重現工程需求才交。

## 實測、圖冊與重現

本批新driver1次、verify1次，633追蹤、28143項日K幾何、119價位群組、633來源成員核對；八指定截止21去重事件前綴（截斷與追加ID穩定）、八案未來價格／未來列缺日污染隔離與正仿射關係、合成相等／對側／遇缺停追／拒絕未可知事件通過。收盤轉向另用平台壓縮演算法核對。這些互相重疊，不是市場樣本／分類準確率／概率。前批driver與驗證（362／208等）未重跑，原事件及來源SHA不變。

圖builder2次成功；首稿p2文字碰標題，移入面板後重繪，兩頁最終渲染實看並綁SHA，舊圖重建0。G2新圖上方廣角至3/16，下方細節至3/3，皆明標；JSON每個截止獨立隔離。靜態圖QA不是Android／瀏覽器。若新改輸出必須重新QA，不能借本批收據。

本機工作目錄 `/workspace/scratch/89f271ea68f4/scope-followup-research`。來源2884 `/workspace/scratch/54685b8dac93/independent-level-review/source-data-2884.json` SHA ab87a51b5b8afd076603f290b10f415bd60d31ae47c5ab2f6d9d609ad4014901；1101 `/workspace/scratch/54685b8dac93/real-review/input/comparison-data.json` SHA184bdef0b687ec0ab7bfcaaac2157ff7916fbc1000ef312d81b5efc0c2e73e15，恢復沿前鏈，不抓新行情。前批目錄 `/workspace/scratch/89f271ea68f4/stop-branch-research`，需candidate-pools.json.gz、reviewed-scope-tests.json供driver；驗證還需前批branch_research.py核未改SHA。CJK字型沿 `/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf`。

有修改需驗證才用核SHA後來源執行：
```
python followup_research.py --source SOURCE --comparison COMPARISON --prior-dir PRIOR_DIR --out OUT
python verify_followups.py --source SOURCE --comparison COMPARISON --prior-dir PRIOR_DIR --out OUT
python build_figures.py --comparison COMPARISON --font FONT --out OUT
```
verify重設圖QA欄位，若重跑需重新綁定實際最終圖QA。原數據池與指標不需重算。

原全部裁決：ABC自己的較弱區間／39筆／5/13影線H31.40／6/3在外、G2人工時間與代表、2884上漲整理再漲及10/7足夠、1/27、11/25非關鍵、小窗撤問、局部整體分判、異質整體、未挑戰舊帶高點前不先降重要性保持。共享角色未答不代答；來源可知／確認／後來選取分開，重複版本非獨立票、不同窗不排名。Raw公司行動、五年Adjusted、完整日曆、歷史可得、Darvas正文、SQLite原未核保持，兩股日曆分開。

分類NOT_VALIDATED、核心用途NOT_ESTABLISHED、行動NOT_EVALUATED、Android NOT_TESTED_NEW_BUILD。無原核心MA/MACD/pivot/box/reaction重算、adapter/source-query CLI、bootstrap、舊產品測試、新瀏覽器Android。保留main、原參數策略、資料、舊圖及所有後續成果，不部署付費交易訊息子代理，file://不重試不繞過。同分支保存逐檔回讀，結束附已核提交、成品、完成未完成、完整接續及Work/Codex判斷。
