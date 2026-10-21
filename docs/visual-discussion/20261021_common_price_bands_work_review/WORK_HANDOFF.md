# 接續：共同往返價帶可串來源片段，正式整體與角色未定

repo blue1998-glitch/Twstockai；分支dev/m1-v018-chart-annotations。本批起點92cd074ae204553ec27a3845bcd36a1adedba447，包含前批cfce9adc9c3fd55b5819032a70d9113389dc8bed之後三筆最高目標更新b57b662／8c0332e／92cd074，全部保留。先核實際HEAD與後續成果，不切main、不用舊ZIP覆蓋。最新研究與收據提交以本目錄GITHUB_READBACK.json及實際HEAD核定。

先讀PROJECT_VISION.md最上方最高資金增值閉環／正向資本成長飛輪目標、AGENTS.md、CONTINUE_IN_WORK_MODE.md、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md最新節；本目錄README、summary、selected-common-spans、pool-summaries、hypotheses、verification、manual-qa、WORK_LOG、GITHUB_READBACK。完整登錄pool-common-span-registry.json.gz。歷史與來源恢復限制沿../20261021_revisit_frames_work_review/WORK_HANDOFF.md及完整前鏈，不遺失所有原裁決／限制，不把舊實測算本次重跑。

## 最高目標與目前範圍

最高目標是風險約束下的資金長期淨成長閉環與飛輪；圖形辨識、動能換股／機會成本、資金配置回收再投入與績效回饋是協作引擎。閉環存在不等於賺錢；不以圖多、交易多或漂亮案例當飛輪成效。本批只研究可追蹤結構／風險參照，capital_growth_flywheel_effectiveness=NOT_EVALUATED，不新增自動下單、概率／績效保證或交易門檻。保留最新目標節在AGENTS／CONTINUE第一節，PROJECT_VISION不改。

## 本批研究方法

common(source,start,cutoff,revisit_episodes=None)從同一來源種子內的新完成收盤轉向形成相鄰上落。轉向需平台左右不等收盤、等候右側保存日，保留平台起末／左右日／可知日，是新研究事件，不是原M1 pivot；觀察首尾無兩側確認不補轉向。

相鄰已確認高低收盤端點是一段完成上落；所有連續至少兩段（才有兩方向）的端點價域，若共同交集有嚴格正寬度便保留為候選。所有長度都留、同點相等不當正寬，不選最長／最短或加比例門檻。端點域覆蓋不是實際日內成交路徑／成交密度／籌碼，收盤共同價帶不是正式箱頂底。每個確切段序列有不可變zone ID／可知日，另含原K觀察外包及右側證據K，正式界／成員保持null。

當前可用的最大連續段序列只是cutoff-local view，後來新段可擴展／改變它，較短zone及歷史輸出仍保留，不改舊ID或當多票。兩最大候選若共用實際leg ID，另算其共同價格是正寬重疊／僅觸及／不相交；共用路徑不等於共享同一價格核心或正式父子合併。

前批重訪只回連參照價在候選共同域內、三次造訪第一日至返回已在zone路徑起日至右證據日內、且不晚於zone出生者；只作來源追溯，不給獨立支持票。回連在zone出生時凍結，不拿較晚見證倒補早期。

按原列待核缺日分來源段，不跨疑點確認轉向／連段／價帶；舊候選及人工大涵蓋不刪，當前跨缺關係帶未認證標記。原日曆／Raw公司行動／歷史公開可得等未核不變，兩股缺日分開。G2完整人工時間跨8/3仍有資格限制，不能說新算法認證全部日曆或市場正式被切段。

## 已有有限結果

2884 seed9/17至10/5有2已確認收盤轉向／1段，無共同候選；至10/6有3轉向／2段：9/30 C44.85（10/1可知）、10/1至10/2平台C45.35（10/5可知）、10/5 C44.80（10/6可知），共同44.85..45.35，路徑9/30至10/5。10/7仍同候選，C45.75已在局部共同價帶上；不否定已確認整理，不宣稱10/6最早整理日，9/17非正式起點。

方向對照seed4/15：4/23有較短2段共同32.75..33.00；4/24可擴展到3段，路徑4/16至4/23；4/28另有2段共同32.45..32.55、路徑4/22至4/27。二者共用4/22至4/23下跌leg，卻核心不相交，描述局部價位向下移動，formal_merge=null。至5/4仍2最大局部候選，不能說此例從未有區間或升全尺度人工負例。

ABC原39至6/2最大局部價帶3：30.55..30.60（4/9至5/19，5/20可知）、29.80..29.85（5/12至5/28，5/29可知）、29.10..29.35（5/26至5/29，6/2可知）。原自己的較弱區間、4/7至6/2共39筆、6/2創低仍內／6/3在外、5/14內部跳空及5/13代表H31.40保持，不能因內部多核心而正式拆箱。至5/13的當時候選右證據K仍完整H31.40，不被5/12 C31.20或共同30.55..30.60代替。

ABC後續seed6/3至6/11只有1完成段、無共同候選；至6/12可知27.15..27.30（6/6 C27.55高收→6/10 C27.15低收→6/11 C27.30高收），路徑6/6至6/11，至6/13仍同候選。前批6/9單參照重訪與本批6/12共同段證據是不同層次，不能混成同一形成日、硬等天數或升已形成新整理。舊6/3種子與各觀察片段起日不改正式起點。

G2完整人工1/16至8/16（136保存筆）本方法產69收盤轉向／67段／170全長候選／20當前最大局部價帶，來源在原8/3疑點分為兩段，未跨接。這是外部人工範圍測試，未提供該完整窗的前批重訪回連，不把未提供當0見證；較早G2-Feb20／Mar3有提供既存見證。20局部核心不能當20正式區間或取代已答大G2與5/2 H40.25代表，更不能冒稱自動找出其人工起末。

## 下一個具體工作

仍Work研究局部共同價帶與較大觀察範圍的角色連結：合看原高低影線代表、離開後的實際返回、當前位置與已知較大參照，避免把大量小帶當主要結構。用現成不可變turn／leg／zone與原重訪來源，而非重畫同圖、只核數字／再堆欄位。不能用單純重疊／共用段／同價或最大長度直接正式合併；不能要求較大整體只有一核心，也不因時間較晚或候選多就提升可信度。重要新核心歧義才附足夠廣角可放大實圖問，原已答案例不重問。

正式形成／起末／成員／代表及父子合併承接／重要性／量權重／衰減／生命階段仍未定。formal_interval/start/end/membership／selected_zone=null，primary_pressure_id／historical_selection_time=null，historical_signal_eligible=false。分類NOT_VALIDATED、核心用途NOT_ESTABLISHED、行動與飛輪成效NOT_EVALUATED、Android NOT_TESTED_NEW_BUILD。10/7原核心快照／numeric_frame無仍null。未定算法不交Codex硬編，已定可重現工程需求才交。

## 真正執行、保存與重現

新driver2次，第二次只無損正規化儲存布局，gzip1745280→125503 bytes。243舊seed觀察去重128新收盤轉向／126段／360共同候選；saved prior witness IDs對應前批937表，整數索引0起算只是保存表示法，不是策略排序或新層級。正規化登錄的current views、maximal shared-path relations及birth revisit links由物件表／末K／缺日快照／原見證表重建，不另外存重複大視圖。

verify1次，獨立非零收盤變化方向反轉核轉向、窮舉全段交集、14594候選出現／同數現值重建、65439前批來源回連、1473共用路徑關係、299外部候選。16指定範圍211去重逐截止、截斷／追加turn-leg-zone及出生回連不變、未來價格／未來列缺日污染與正仿射幾何、合成常數單向平台相等觸及／不相交／缺日、5/13 H31.40保留、G2缺日不跨通過。這些重疊不是獨立市場樣本／概率／全市場或產品分類準確率。當前最大view可改，不以它當不可變事實。前批所有driver／測試未重跑。

圖builder1次成功，三頁渲染逐頁實看、PDF與三PNG指紋綁定，價量各貼原K，舊圖重建0。新變更要重QA，不借本批收據。靜態圖不是新Android／瀏覽器驗收。無原核心MA/MACD/pivot/box/reaction重算、CLI／adapter／source-query、bootstrap、14/22/60等舊產品測試或新行情。

本批本機 `/workspace/scratch/89f271ea68f4/common-band-research`。兩來源仍為2884 `/workspace/scratch/54685b8dac93/independent-level-review/source-data-2884.json` SHA ab87a51b5b8afd076603f290b10f415bd60d31ae47c5ab2f6d9d609ad4014901，1101 `/workspace/scratch/54685b8dac93/real-review/input/comparison-data.json` SHA184bdef0b687ec0ab7bfcaaac2157ff7916fbc1000ef312d81b5efc0c2e73e15。前批 `/workspace/scratch/89f271ea68f4/revisit-frame-research/` 的pool-revisit-registry.json.gz（SHA2f1d797d7892b5c47b131447e68bb01a2500c1a4e54d84f1e89d9a5d54f61cc3、解壓SHA dac09001f9afae5370ae1369d440291464ffac784ad59a64ab888763217e8cc7）與selected-revisits.json（SHA778c015dd23eb6d89205015a9449b63bba21390e7f6d945a5e199ffdfd1f800f）供新研究；恢復方法沿前鏈，不下載新行情。字型沿 `/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf`。

有變更需驗證才重現：
```
python common_research.py --source SOURCE --comparison COMPARISON --prior-dir PRIOR_DIR --out OUT
python verify_common.py --source SOURCE --comparison COMPARISON --prior-dir PRIOR_DIR --out OUT
python build_figures.py --source SOURCE --comparison COMPARISON --font FONT --out OUT
```
新執行需更新本批記錄式driver_runs等次數與QA；它們不自動統計。最終gzip原JSON SHA f66907bc82be08637f4e15fbf3b2343ce38b869c9aa91bec48d893ffcd52af12，gzip可完整恢復；無需原核心／舊driver重跑。

所有原裁決與限制保持：ABC自己較弱／39筆／5/13／6/3、G2時間與代表、2884上漲整理再漲／10/7足夠、1/27、11/25非關鍵、小窗撤問、局部整體分判／異質整體、未挑戰舊帶高點前不先降重要性；共享角色未答不代答。相等不補過破、OHLC不推日內先後、來源可知／確認／後來選取分開、重複版本非票／不同窗不排名。Raw公司行動／五年Adjusted／歷史公開可得／完整日曆／Darvas正文／SQLite原未核保持。保留main、原參數策略、來源歷史舊圖與全部後續成果，不部署付費交易訊息子代理，file://不重試不繞過。同分支保存逐檔回讀，結束附最新已核提交、成品、完成未完成、完整續接及Work/Codex判斷。
