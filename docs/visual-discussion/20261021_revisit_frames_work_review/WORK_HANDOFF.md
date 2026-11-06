# 接續：可自動提出已知價位重訪片段，正式範圍形成仍研究中

repo blue1998-glitch/Twstockai；分支dev/m1-v018-chart-annotations；本批起點7c115b9cba5d6ca0963e82754912554ba0669cfa。先核實際HEAD保留全部後續成果，不用main或舊ZIP覆蓋；最新研究與收據提交以本目錄GITHUB_READBACK.json及實際HEAD核定。

先讀AGENTS.md、CONTINUE_IN_WORK_MODE.md、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md最新節、PROJECT_VISION.md，本目錄README.md、hypotheses.json、summary.json、selected-revisits.json、pool-summaries.json、verification.json、manual-qa.json、WORK_LOG.md、GITHUB_READBACK.json。完整自動登錄為pool-revisit-registry.json.gz。全部原裁決／來源恢復限制沿../20261021_scope_followup_work_review/WORK_HANDOFF.md及其完整前鏈，舊執行不得算本次重跑。

## 本輪新研究方法

discover(source,start,cutoff)讀既有候選種子後資料，不接收目標片段起末／長度／人工標籤。某原低／高／收盤第一次在該種子目前來源段中出現，才加入參照，保留日期與角色。同值合一參照保留角色，不當獨立票。只追蹤出生後完成收盤的嚴格側向造訪，忽略相等的跨越作用但不刪原K；三個側向段上-下-上或下-上-下形成一次重訪見證。單一往返也可出現在噪音／反彈／趨勢，不等於區間已形成。

每次返回前凍結第一嚴格造訪日至返回前一筆的完整原K高低框，formal_price_bounds=null。返回收盤在舊框內含相等為回入；回到同側卻超出舊框另留overshoot，不能冒稱回原價位活動範圍；影線可以創新高低，返回收盤在內仍留兩種事實。返回當日、原框時間涵蓋、證據可知日、原seed起日分開，不冒充正式起末／確認轉折。原2高2低與3／6／12%未改，無新比例／等待天數／最短長度門檻。

現值關係隨各截止另算，原episode／frame ID及內容不回寫。源原列缺日間隔重開參照和造訪序列，舊見證保留；跨疑點至當前的舊框現值關係帶未認證標記，並非市場強制重置／正式停段。完整日曆／公司行動仍未核，兩股缺日分開，不用資料隔離貶低舊大帶。

## 有限結果與約束

2884研究種子9/17，參照9/24 L45.10：9/24 C45.60上、9/29 C44.90下、10/1 C45.35上。返回前9/24至9/30只3筆，觀察44.75..45.95；10/1 L44.20可創低而C回框內；10/7 C45.75仍在框。10/1只是此見證完成日，不宣稱最早辨認日；10/7足夠及整體上漲整理再漲裁決保持，9/17非正式起點。此seed至10/7共12回入見證／8框，現收對11見證在內1在上，相關非票或準確率。

方向對照4/15至5/4：參照4/16 L32.80，4/16 C33上、4/17 C32.75下、4/20 C32.85上，先前4/16至4/17框32.50..33.20。以前確有往返，5/4 C31.30已在下；全部4個回入見證的現收都在下，3整根在下1仍跨框。此為前批事後方向對照，人工區間標籤null，不把它叫所有尺度負例或曾無區間。

ABC後續seed6/3，參照6/4 H27.45：6/4 C27下、6/5 C27.50上、6/9 C27.20下，先前6/4至6/6框26.55..27.65；6/9得第一自身重訪片段，6/13 C26.90仍在框。6/4是該見證片段起日，不替代6/3seed或定正式起點。原ABC4/7至6/2共39筆、6/2創低仍內、6/3在外與5/14區內跳空全部保持。

ABC39至6/2有58個收盤回入型早先見證，末收對58全部在下，仍不否定已確認自己的較弱區間。G2早期局部見證也能被向上離開，仍在已答較大人工時間涵蓋內。不能把當前在某局部框內定為所有區間存在／正式成員必要條件。5/13 H31.40在參照登錄保留，角色high、只1個嚴格側向段，無該價收盤往返；不能因此刪已確認影線代表或說沒有作用。

前批G2 2/22觸及37.85、3/1 C37.80返回與ABC至6/13九筆仍整根在舊28.45下的持續追蹤保留，不重跑、不取代。本批十一外部截止包括A四截點、方向對照、ABC39／新seed、G2早期／至3/3／新seed，以及2884末10/16僅1筆0見證。G2人工1/16至8/16與5/2 H40.25已定，不冒稱本輪自動找到，完整跨原8/3缺日資格不變。

## 下一個具體目標

仍Work研究多個局部重訪片段如何構成有意義共同觀察範圍：結合各片段反覆價位、時間銜接、原高低影線代表及各自可知日，檢驗同層延續與較大整體並存。用現成937見證／430框及候選摘要，不再只核同例數字／堆欄位；不能直接重疊就合併、按最短最長窗選勝者、拿數量投票或把當前在內當所有區間必要條件。也不能用未來資料修早期端點、為ABC／G2硬編日期，或把一個ABA見證定成充分形成規則。常規可推導細節連續做，重要新核心歧義才附足夠廣角可放大實圖問，已答案例不重問。

正式形成規則、起末、完整成員、選定框、合併直接承接、正式代表／量權重／衰減／生命階段仍未定。formal_interval/start/end/membership／selected_frame=null；primary_pressure_id、歷史選取null／historical_signal_eligible=false。分類NOT_VALIDATED、核心用途NOT_ESTABLISHED、行動NOT_EVALUATED、Android NOT_TESTED_NEW_BUILD。10/7無原核心快照／numeric_frame仍null。未定算法不交Codex硬編，已定可重現工程需求才交。

## 真正執行及重現

新driver3次：首次計算後兩次僅無損儲存布局改進，gzip2555223→835515→135169 bytes；discover邏輯與指定摘要相同。最終登錄共243舊種子觀察、937去重事件、430去重框。episode_table保留完整episode_id；observations的episode_indices索引該表，另含末K與原列缺日，可對frames逐項重建現值關係。此整數索引是檔案表示法，不是新結構ID／策略排序。

verify1次，另一演算法逐參照離線枚舉核31410個重疊見證出現、31410現值無損重建，事件框指紋、107去重逐截止、十一案未來價格／未來列缺日污染與正仿射關係、合成單向／常數／相等／超出舊框／新影線／遇缺，5/13保留均通過。937／430等互相重疊，不是獨立市場樣本、概率或分類準確率。臨時診斷曾見A／B完整13筆窗最大收盤格點穿越皆4，因此未採計數門檻；後見格點只診斷不當因果事件。

圖builder1次成功，三頁渲染逐頁實看，原K價格與日期受限底色、量圖分開，最終PDF／PNG SHA綁定；原圖重建0、無新Android／瀏覽器驗收。新變更必須重新QA，不借本批收據。無原核心MA/MACD/pivot/box/reaction重算、原CLI／adapter／source-query／bootstrap、原14／22／60與前批362／208／21等舊測試重跑。

本批本機 `/workspace/scratch/89f271ea68f4/revisit-frame-research`。兩來源仍為2884 `/workspace/scratch/54685b8dac93/independent-level-review/source-data-2884.json` SHA ab87a51b5b8afd076603f290b10f415bd60d31ae47c5ab2f6d9d609ad4014901，1101 `/workspace/scratch/54685b8dac93/real-review/input/comparison-data.json` SHA184bdef0b687ec0ab7bfcaaac2157ff7916fbc1000ef312d81b5efc0c2e73e15；恢復沿前鏈，不抓新行情。前池 `/workspace/scratch/89f271ea68f4/stop-branch-research/candidate-pools.json.gz` SHA97ee3be1288fd09e1891939b7ef01530daf624f187d5f40ec8d132483a266bb8，解壓原SHA db4dc777c42dd89d605556be776841ba76e966ecdd9bd46055fbaa58e5d9c2b9。字型沿 `/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf`。

有變更需要驗證才重現：
```
python revisit_research.py --source SOURCE --comparison COMPARISON --prior-dir PRIOR_DIR --out OUT
python verify_revisits.py --source SOURCE --comparison COMPARISON --prior-dir PRIOR_DIR --out OUT
python build_figures.py --source SOURCE --comparison COMPARISON --font FONT --out OUT
```
verify內本批driver_runs=3等為本批紀錄，不是新執行次數自動統計；重現需更新實際次數與QA狀態。最終gzip原JSON SHA dac09001f9afae5370ae1369d440291464ffac784ad59a64ab888763217e8cc7，未另發布重複大原JSON，解壓可恢復。

所有已答與限制保持：ABC自己較弱／39筆／5/13／6/3、G2時間／代表、2884完整上漲整理再漲／10/7足夠、1/27、11/25非關鍵、小窗撤問、局部整體分判、異質整體、未挑戰舊帶高點前不先降重要性不重問；共享角色未答不代答。相等不補過破、OHLC不推日內先後，來源可知／確認／後來選取分開、重複版本非票、不同窗不排名。Raw公司行動、五年Adjusted、歷史公開可得、完整日曆、Darvas正文、SQLite原未核保持。保留main、原核心參數策略、來源歷史舊圖與全部後續成果，不部署付費交易訊息子代理，file://不重試不繞過。完成同分支保存逐檔回讀，結束附最新已核提交、成品、完成未完成、可直接續接及Work/Codex判斷。
