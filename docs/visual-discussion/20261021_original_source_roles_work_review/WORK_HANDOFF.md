# 接續：局部價帶與較大原來源關係，正式父子及主要角色仍未定

Repo blue1998-glitch/Twstockai；分支dev/m1-v018-chart-annotations。本批起點cfe73ac6653692ed85b111fa3ff755f0cf64f1df；最新研究／回讀提交以本目錄GITHUB_READBACK.json與實際HEAD核定。先查是否另有後續，全部保留，不切main、不用舊ZIP覆蓋。

先讀AGENTS.md、CONTINUE_IN_WORK_MODE.md、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md最新節，PROJECT_VISION最上方最高目標，再讀本目錄README、summary、verification、storage-verification、manual-qa、source-provenance、WORK_LOG與GITHUB_READBACK。前批完整交接在../20261021_common_price_bands_work_review/WORK_HANDOFF.md，沿前鏈保留所有已答與限制。本批新增17,175來源關係，不代替舊見證或人工裁決。

## 最高目標與授權

資金增值閉環＋正向資本成長飛輪：圖形辨識、動能換股與持股／候選／現金機會成本、風控資金配置與回收再投入、淨績效回饋共同改善長期風險調整後資本成長。閉環存在不證獲利；本輪只推進可追溯觀察，flywheel成效NOT_EVALUATED，未增交易門檻／績效保證／自動下單。PROJECT_VISION不改；最高目標節仍置AGENTS與CONTINUE最上方。

使用者允許一次多步，例行工作直接做，重要核心歧義才問；同分支保存回讀已授權。非工程／手機使用者，交付要有真正可放大圖與清楚發現，不能只累積欄位核對。未定算法仍Work研究，只有規則已定或可重現工程缺陷才Codex，不能假裝目前自動分類已完成。

## 本輪方法與有限結果

只讀原保存原核心：依confirmed_at、first_observed_at與source_dates不晚於截止，投影白名單靜態pivot／box欄位；不複製原輸出截至10/16的anchor_relation、path、reaction、pending_extrema、interpretation、comparison。此為事後保存中繼資料資格研究，不是較早核心快照、當時公開可得或增量原核心回放。

在完整原pivot序列中，同scale且同原segment的相鄰異類點組兩點價域，非原箱體、新正式箱或父區間。先保留原完整鄰接再判兩點可用，不跨scale／segment或跳過未可用中間點。原box必須自身確認／首次觀察及全原source_turn_ids可用，僅沿原research_bounds與來源，不重新枚舉或調參。原列缺日覆蓋仍附，未認證完整日曆或重寫原segment。

與前批不可變共同zone聯結：價格相交才存（含僅碰），另分價格包含／交疊、來源時間包含／前／後／交疊、是否包住右證據窗、原點source_dates是否落zone證據窗。關係known_on取兩來源較晚日；zone出生已知與後來新增分開，後者不回填出生。不選唯一父子、不按數量投票／最近／距離／最大窗排名。當前收盤對每來源的關係另算，不複製成每連結的多票。相等僅AT_LOW/HIGH而非嚴格越過。OHLC仍不推日內路徑。

2884：共同44.85..45.35路徑9/30..10/5，10/6有完整研究證據。原3%8/12低36.30→9/17高47.35在9/23確認，價域包住核心但時間全在前；原9/17高47.35→10/1低44.20到10/7才可用，價域包住核心而來源僅至10/1，未包住完整路徑。故不能以價格包含定父子；10/6已有44.20原低也不能先給原pivot確認資格。10/14收47.30在44.20..47.35內，10/15收48.80、10/16收49.15在上，非正式突破／解除／交易門檻。原2884保存34箱最高high39.10低於當前核心，仍有相鄰點可參照；不新增假原箱、改2高2低與3/6/12%或當產品缺陷。10/7足夠整理與完整上漲整理再漲已答，不重問，不宣稱10/6最早。

ABC：原3%4/8..5/13研究箱28.45..31.40於5/14可用；6%同幾何於5/27才可用。來源不同日期保留、不回填／加票。原5/13 H31.40當天原值、5/14原高確認、後來人工代表分判。6/2 C27.70低研究框仍在已答人工39筆；局部三核心不能取代大涵蓋或直接停止／正式拆併。ABC相對舊主要帶更弱的已答保持，不能先降較老高點重要性。

G2：人工1/16..8/16共136筆與5/2 H40.25代表保留，原3%該高點5/9確認。20局部最大核心不是20正式箱；5/10放大只用當時可用共同zone view，8/16廣角保留完整人工範圍，8/3原列疑點不跨接新片段。原值、原確認與人工選取不混同，較晚小核心不自動成主要參照。

## 真實完成／未完成

新driver1次，保留243舊重疊觀察，合入外部範圍總531既存去重zone；297原pivot、291同尺度相鄰價域、123原研究箱共414來源；17,175相交關係中11,467出生已可用、5,708後加，不當獨立市場樣本／投票。22完整選定視圖，包括固定既有A與ABC候選於後續截止觀察，**沒有重跑前批common／revisit／seed driver或增造較晚common候選**。

獨立verify1次：297原點價日期、414來源界鄰接尺度segment與缺日、17,175幾何關係獨立重建、243池投影、22視圖重建、238去重逐保存筆截止與連結不可變、19有zone案例未來來源payload／未來K／截至16日解讀污染、12指定案例斷言與5輸入SHA未變通過。不是產品分類準確率、全市場／歷史公開資格或獲利驗證。19不是22：3個無zone視圖未做該污染迴圈，22個視圖均重建。

選定視圖5,511,379byte JSON先驗證再無損gzip轉存292,830byte，解壓逐byte相等；driver／verify對應讀寫gzip更新而未重跑，轉存1次與權威來源核對記storage-verification。registry本來正規化gzip208,671byte；解壓SHA d337e10f56586c493f9cc4d608040181fc5a98bdc37845b0f106dec8da1b9cea。selected解壓SHA a8ea86c931e58c6ef6205f2d12a5f6bfde44970f03acaa923b67942ec5e6de93。陣列索引0起僅儲存，不是策略排序。

新圖builder2次成功；第一版箭頭占位價／巢狀底色經QA修正，第二版3頁重新渲染逐頁實看，PNG保存PIL.verify與byte對照，最終PDF SHA923e53e2c687e6bad85f526555377d421c1d48b26674137369c8a83d1b44c192；manual-qa綁定。原圖重建0。靜態PDF不算Android／瀏覽器驗收。無core指標、pivot／box／reaction、MA／MACD／source-query、CLI／adapter、bootstrap、14/22/60或舊產品測試重跑；無新行情、Androidbuild、瀏覽器或file://繞過。

正式形成／起末／成員／價界／主要參照選取／父子／合併承接／量權重／衰減／生命階段未知。formal_parent／formal_membership／selected_context／primary_pressure_id／historical_selection_time=null，historical_signal_eligible=false；classification=NOT_VALIDATED、core_usefulness=NOT_ESTABLISHED、actions與capital_growth_flywheel_effectiveness=NOT_EVALUATED、Android=NOT_TESTED_NEW_BUILD。10/7原核心snapshot／numeric_frame無仍null。使用者已答定性保持USER_CONFIRMED，不因產品未驗而降回待問。

## 下一個具體工作

仍Work研究如何提出**來源在當前觀察中的角色候選**：前段方向背景、局部共同活動、較早較大主要帶與明示高低參照分判，結合既存離開／返回、整根分離、當前位置。找出可說「先保留哪種觀察、並列哪些較大來源、後續何時需要新活動片段」的有限正面條件與方向對照；不能只多畫同圖或核原值。已知單純價格包含、共用段、來源較近、最近有核心、最大窗口都不足以直接正式父子／合併／主要性；當前在局部核心外也不能直接否定整理。較大整體允許多核心，未挑戰舊帶高點前不能因新小窗先降重要性。不要對舊共享角色PENDING追問或用下一步冒充用戶答案。

## 檔案與重現

本機/workspace/scratch/89f271ea68f4/source-role-research。程式source_roles.py、verify_roles.py、build_figures.py；完整登錄source-role-registry.json.gz、22視圖selected-source-roles.json.gz；summary、verification、storage-verification、manual-qa、source-provenance、三文檔、PDF與3PNG及GitHub收據同目錄。

原2884 source /workspace/scratch/54685b8dac93/independent-level-review/source-data-2884.json，SHA ab87a51b5b8afd076603f290b10f415bd60d31ae47c5ab2f6d9d609ad4014901；1101 comparison /workspace/scratch/54685b8dac93/real-review/input/comparison-data.json，SHA184bdef0b687ec0ab7bfcaaac2157ff7916fbc1000ef312d81b5efc0c2e73e15（內含原core）；新唯讀2884core /workspace/scratch/54685b8dac93/independent-level-review/input/core-2884-latest.json SHA1c178d1ddad99feacf5fa8600cc646cfe60794d51557973036096df8d6bda6f0，Git原4c8d483afc7bb052b01cb6a9b99db92dfbd95612之股票系統M1_v0_18/graph_core_chart/generated/core-2884-latest.json，blob28928b37865e33cb7c0165ce1ebba388d19ce8bc。來源與比較檔Git恢復／舊ZIP限制沿前鏈，不抓新行情或重算原core補檔。

前批common-band-research的selected-common-spans.json與pool-common-span-registry.json.gz，Git ../20261021_common_price_bands_work_review/固定研究commit abe82e5cc7c1825da662a058a222c69a392160bb；gzip解壓SHA f66907bc82be08637f4e15fbf3b2343ce38b869c9aa91bec48d893ffcd52af12。字型/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf沿前鏈恢復。

有變更確需驗證才重現，不例行重跑。程式默認上述已核來源，source_roles.py可用--source/--comparison/--core/--prior/--out重定位；verify_roles.py與build_figures.py依source_roles默認位置。異地接續可同時修正這些路徑或重建相同工作布局。執行新次數／QA需重新記錄，不沿用舊通過。

```
python source_roles.py
python verify_roles.py
python build_figures.py
```

## 所有舊裁決／限制保留

ABC自身較弱／4/7..6/2的39筆／6/2創低在內、6/3在外／5/14內跳不通用切段／5/13 H31.40且C31.10低於5/12 C31.20；G2人工1/16..8/16與代表5/2 H40.25，未定正式全成員／價界；舊主要帶僅2023-06..2025-04月精度，不強配日端點；2884完整上漲整理再漲及截至10/7足夠已答；1/27、6/3、11/25非關鍵及小窗撤問、局部與整體分判／異質大整體、未挑戰舊高前不先降重要性全部不重問。舊共享正式角色仍PENDING_NOT_REASKED，不代答。

重複版本／重疊候選不當獨立票，不同窗不排名；相等不補突破，OHLC不推日內先後；原來源可知、確認、後來選取分開。Raw公司行動、五年Adjusted、歷史公開時點、完整日曆／原九待核非窮盡及兩股不同缺日、Darvas正文、SQLite未核不變。保留main、原核心參數策略庫、原資料歷史舊圖及所有後續；不部署付費交易訊息子代理，file://不重試繞過。結束附可用成品、完成未完成、真實已核提交、完整接續與Work/Codex判斷。
