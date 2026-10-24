# 接續：競爭停止／延續／後續種子已有研究，正式選擇未定

repo blue1998-glitch/Twstockai；分支dev/m1-v018-chart-annotations；本批起點f34635187baf0efa0c9d66d5884e06b114fd95c7。先核實際HEAD並保留所有後續成果，不切main，不用舊ZIP覆蓋。最新已核研究提交及回讀收據提交以本目錄GITHUB_READBACK.json和實際HEAD核定。

先讀AGENTS.md、CONTINUE_IN_WORK_MODE.md、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md最新節、PROJECT_VISION.md、本目錄README.md、summary.json、reviewed-scope-tests.json、verification.json、manual-qa.json、WORK_LOG.md、GITHUB_READBACK.json。完整自動池為candidate-pools.json.gz，解壓後是完整JSON，不是摘要。完整原限制沿../20261020_observation_start_proposals_work_review/WORK_HANDOFF.md與其前鏈，不丟任何前批成果。

## 已做及仍未做

新純研究observe(source,start,cutoff)：已觀察外包首次遇完成收盤嚴格越界時凍結之前框；完成收盤返回（含邊界）解除待觀察，對側離開另記方向；後來整根日K嚴格在凍結框同方向之外時，並列舊觀察止於前筆、新種子從當筆起、原範圍繼續，selected_alternative始終null。延續包絡包括所有已觀察K，pending凍結框不擴。沒有百分比／等待天數門檻，這是新研究假說，不是正式箱界或正式解除規則，也不改原2高2低及3／6／12%。新種子僅一筆，尚未形成區間，不補父子／合併／承接。

自動六池只重用上批未改propose函數的反向外包候選；人工起日不餵入生成器。候選數／分支數：2884截至10/7=66/195、10/16=63/260、方向對照5/4=36/55；ABC截至5/14=27/39、6/2=25/30、6/3=26/54。共243觀察、633分支，重疊非獨立市場樣本／準確率。

ABC從4/7觀察：5/14區內跳空不強切；6/2 C27.70首次低於此前38筆外包L28.45（H31.40），H29.05仍重疊，截止6/2只有待觀察離開、無停止分支；6/3 H28.00<28.45才可知整根在外，當日提案舊觀察4/7至6/2共39筆、新種子6/3，同時保留40筆延續。能生成與既有39筆相符的替代提案，不能叫正式成員分類通過；6/2當時不能預知6/3或把這個正式終點提前成立。

2884從研究種子9/17：9/30 C44.85<此前L44.90，10/1 C45.35返回、L44.20仍可創低，至10/7沒有停止分支。10/15 C48.80>此前H47.35，10/16 L48.00>47.35整根在上，提案觀察止於10/15及10/16新種子並保留延續；10/15不是使用者正式終點。方向對照4/15至5/4有4/23離開／4/24返回／4/30再離開待觀察，非已標負例。

G2人工時間涵蓋2023/1/16至8/16的136保存筆只作外部範圍測試：2/17 C38.00>此前H37.85；2/20仍重疊；2/21 L38.15>37.85產生止於2/20提案，2/24再產生止於2/23提案。若強制套在較大G2，會截斷已確認較大範圍；因此必須保存局部停止與較大延續競爭。人工起日不是自動找到G2。全窗跨原列待核8/3仍帶來源限制；2月事件在該缺日前。原G2時間範圍與5/2高40.25代表已確認，不補完整正式成員／正式價界。

## 下一個具體工作

繼續Work研究選擇分支所需的角色／尺度證據：利用現成候選池追蹤每個凍結框的來源、同時存在較大候選及後續種子的累積過程，區分局部觀察停止與較大範圍保留。必須一起容納ABC39、6/2創低仍在內、5/14內部跳空，以及G2可含早期同類局部事件。不能硬編日期、用整根離開即終止所有尺度、預設最短／最長窗勝出或先套正式層級。也不要只再核同例數字／堆欄位就當識別完成。可推導細節直接做，只有真正新的重要核心歧義才附足夠廣角可放大實圖問，不重問已答。

現有分支不選定、formal_start/end/membership=null、primary_pressure_id=null、historical_selection_time=null、historical_signal_eligible=false。截止隔離只證現在做的事後研究，歷史公開可得／實際當時選取未核。10/7無原核心快照／numeric_frame仍null。分類NOT_VALIDATED、用途NOT_ESTABLISHED、行動NOT_EVALUATED、Android NOT_TESTED_NEW_BUILD。正式規則未定繼續Work，不交Codex硬編；已定可重現工程需求才Codex。

## 已測範圍與重現

driver1次、verify1次：2284事件幾何核對、633分支一致性、六外部範圍208去重逐截止，截斷及追加後原事件／分支ID不變，六案未來價格／未來列缺日污染隔離與正仿射價格轉換，合成創低但內收／相等／返回／反向事件。這不是產品分類器或全市場驗證，前批362檢查未重跑。圖builder2次成功、兩批次渲染加頁3單獨修復渲染，最終三頁靜態人工QA及SHA綁定。截斷PNG修復見WORK_LOG，根因未定。原歷史圖冊重建0次，無核心MA/MACD/pivot/box/reaction重算、adapter/source-query CLI、bootstrap、舊產品測試、瀏覽器或新版Android。

已核本機來源：
- 2884 `/workspace/scratch/54685b8dac93/independent-level-review/source-data-2884.json`，SHA256 ab87a51b5b8afd076603f290b10f415bd60d31ae47c5ab2f6d9d609ad4014901；Git沿20261020_independent_source_levels_work_review/source-data-2884.json。
- 1101 `/workspace/scratch/54685b8dac93/real-review/input/comparison-data.json`，SHA256 184bdef0b687ec0ab7bfcaaac2157ff7916fbc1000ef312d81b5efc0c2e73e15；原保留ZIP恢復方法沿前鏈，不下載新行情或重傳3MB源檔。
- 前批module `/workspace/scratch/89f271ea68f4/range-proposal-research/proposal_research.py`，SHA256 7e7ccc3d4d9fcb091c502c0ae7ee813a9a2722fd7bb70459d9aa8039d6606483；Git沿上一批同名檔。
- CJK字型 `/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf`；本批工作目錄 `/workspace/scratch/89f271ea68f4/stop-branch-research`。

需要變更重驗時才執行，參數均替換成恢復且核SHA的實際檔路徑：
```
python branch_research.py --source SOURCE --comparison COMPARISON --prior-module PRIOR_MODULE --out OUT
python verify_branches.py --source SOURCE --comparison COMPARISON --out OUT
python build_figures.py --source SOURCE --comparison COMPARISON --font FONT --out OUT
```
新輸出不能借用本批manual-qa；重新渲染並人工檢視再綁定最終SHA。解壓candidate-pools.json.gz也可恢復驗證需讀的candidate-pools.json；gzip mtime=0，282244 bytes，原JSON SHA db4dc777c42dd89d605556be776841ba76e966ecdd9bd46055fbaa58e5d9c2b9。

## 所有原裁決／保護仍有效

2884完整上漲整理再漲及截至10/7「足夠辨認了」已答不重問，不問最早日；9/17非正式起點。ABC自己的較弱區間、原4/7至6/2共39筆／5/13代表H31.40／6/3在外、1/27、11/25非關鍵點、小窗撤問、局部整體分判、異質整體、未挑戰舊帶高點前不先降重要性全部保持。共享來源角色未答不代答。相等不補過破，OHLC不推日內次序，來源可知／確認／後來選取分開；重複版本不當獨立票、不同窗不排名。

Raw公司行動、五年Adjusted、歷史公開可得、完整日曆、Darvas正文、SQLite等原未核限制保持，兩股原列缺日分開，缺日後保守候選段是來源疑點隔離，不是市場正式起點或舊帶變不重要。正式代表／成員界／量權重／衰減／合併直接承接／生命階段未知仍未知。保留main、原核心參數策略庫、來源、歷史舊圖及全部後續成果，不部署付費交易訊息子代理；file://不重試不繞過。完成同分支保存回讀，結束附已核提交、成品、完成未完成及可直接接續方式。
