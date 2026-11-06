# Work完整接續：同一批原參照、局部來源與確認後價格路徑

2026-10-21；blue1998-glitch/Twstockai／dev/m1-v018-chart-annotations；前核提交6c6eaf8affd644eb125f0691f4088089240b623d。新研究提交、回讀收據與最終HEAD按本目錄GITHUB_READBACK_RECEIPT及實際分支核，不預填。先讀AGENTS.md、CONTINUE_IN_WORK_MODE.md、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md最新節，再讀本交接及README。

## 模式、目的與授權

使用者允許下一步一次多步，有重要性才問；原任務維持Work研究局部活動連結較大結構，不轉產品接入或正式分類器。最高目的資金增值閉環＋正向資本成長飛輪保持，AGENTS／CONTINUE第一節仍最高目標，PROJECT_VISION不改。本輪不評估資金／交易／飛輪成效。

例行讀取、研究、核對、修正、原分支保存回讀直接做，真正新核心歧義才附廣角真實圖問；已答案例不重問。使用者非工程師、以圖形交易、Pixel9Pro手機優先，不把程式欄位或數量當用途完成。保留main、全後續、原引擎策略參數／資料／舊圖。不部署、付費、交易、發訊息或開子代理。

## 本輪新進展

前批研究完成局部活動才提跨活動閱讀；本輪新增另一條觀察途徑：**已可用原參照被保存收盤嚴格跨過，當日即可更新較大觀察問題，不必等新局部雙向活動完成。** 這只記價格位置改變，不證正式新大結構／舊終點／清除壓力／交易資格。原參照及原事件定義保留，不因被跨過便刪除。

另一個重要反例：多個局部候選都在原高下方，不足以認證同一原高正在壓制。原影線框含原價，可能只是重用形成K；須分開構成證據與確認後反應。沒有精確原價再含／到達，也不等於較大壓力帶不存在，因正式帶寬及作用機制仍未知。保留使用者已答較大帶與代表，不以此降權。

## 已存資料與具體對照

本批三組、六事後指定原3%點、17截止／37參照視圖，34當時可用、3不曝價格的不可用遮罩。不是主點排名／全市場盲掃描／歷史曾選取。reference_paths.py按原known_on處理已存pivot，不重算原核心。

| 原參照 | 本批事實與解讀界線 |
| --- | --- |
| A 9/17原高47.35，9/23確認 | 10/14 H=C47.30仍下；10/15 O48.35、H49.50、L47.60、C48.80，第一次保存收盤及整根在該原高上，日K價域卻未含47.35；10/16 C49.15。可在10/15提出跨原參照後路徑的觀察問題，沒有跨過後新完成局部價帶也可更新，不宣稱盤中在47.35成交或回測 |
| A前批固定框事件 | 44.20至47.35的9/17框，departure=10/15，known_on=10/16；舊定義要離開之後再等後一筆整根在外，與10/15原值已整根在原高上分開。兩者不矛盾，不回寫事件known_on、不改舊算法 |
| A 10/1原低44.20，10/7確認 | 五個局部原影線框含44.20，極值來源全為10/1形成低點；確認後至10/16無保存日K價域再含該精確價，不能當五次回測。較晚原低參照加入時只加關係，原局部出生不改 |
| ABC 4/8原低28.45，4/10確認 | 6/2 L27.65、C27.70已下但H29.05仍跨含；6/3 H28.00才整根下。6/2已可更新原低跌破的觀察，不等6/12框下活動完成；6/2仍人工ABC第39筆，不把此收盤事實當通用正式終點 |
| ABC 3/12高35.45及5/13高31.40 | 分別3/13、5/14原確認，至6/13無保存日K價域再含各精確價；局部活動在下只證位置與尚未再到達，不直接認證反壓。35.45不是舊主要帶正式上緣／唯一代表，31.40仍局部已答非主壓力 |
| G2 5/2高40.25，5/9確認 | 5/9至8/16共69保存筆無日K價域再含40.25。九個含40.25的局部影線框極值來源均為5/2形成高點，非5/9後九次測壓；其他後續多段在下不直接證約束，也不否定大G2或原代表 |

局部活動完整來源早於或重用參照確認前期間者另標；不能把原形成點出現在局部框內，當作後續反應。局部common／raw相對位置與確認後逐日原K分開。日K價域含點也不證日內順序或精確價確有成交。相等不嚴格過破，合成HIGH／LOW兩方向已測相等→影線越界但收未過→整根跳過→後來返回；觀察問題出生ID不被返回改寫，現況另更新。

## 圖面與檔案

新output/pdf/m1-same-reference-price-paths.pdf共兩頁及兩PNG，已最終渲染逐頁實看。P1 A全段及10/12至16放大；P2 ABC自3/12及G2自5/9的原參照後路徑。虛線自原參照確認日畫，不回填先前；來源點與原確認分開。舊圖／builder未重跑。四個價圖對齊成交量，局部核心只在自身價域著色，沒有滿高背景。

queries.json／reference-paths.json為17完整截止資料；summary、formation-point-reuse-audit、verification、source-provenance、figure-build、manual-qa與三程式reference_paths.py／verify_paths.py／build_figures.py同目錄。review_question只是研究觀察問題，不是交易訊號、正式結構ID、信心機率或重要性排名。

## 真實實行與驗證

新研究driver1次；verify2次均成功，第二次因新增形成點重用反例才重驗，driver未重跑；新圖builder1次、渲染1次，兩頁實看綁SHA。最終17視圖／源前綴／未來價格與人工標籤污染／未可用原參照值污染／正式未知、136全路徑及首事件獨立核、1047局部位置與可用時序、34不推作用／重要性、3不可用遮罩、A直接價事實與舊較晚分支1、ABC先收破後整根及人工39保持1、3多段同側無原價再含、4觀察問題出生追加保持、2方向合成、2形成點來源重用、8輸入SHA通過。

這些是有限指定研究、原值與不回填的核對，不是分類準確率、通用充分條件、獨立市場樣本、票數或產品驗收。人工標籤不入函式，原價與來源保持。原core／MA MACD／pivot box reaction／CLI／adapter／bootstrap／舊研究driver／舊產品測試0重跑，新行情、瀏覽器、Android、子代理均無。

## 未完成與下一步

正式形成起末成員、價界、主結構／重要性、父子合併、量權重／衰減／生命階段未定；support_or_pressure_response_demonstrated與importance_score=null，不把同側／接近／日K含點直接寫成作用。formal欄位／selected_role／primary_pressure_id／historical_selection_time=null，historical_signal_eligible=false，10/7原core snapshot／numeric_frame仍無、不補造。分類器NOT_VALIDATED、用途NOT_ESTABLISHED、行動與capital_growth_flywheel_effectiveness=NOT_EVALUATED、新Android NOT_TESTED_NEW_BUILD。靜態PDF不算實機驗收。

下一步仍Work，從已有真實日K再含原參照、收盤跨過、後來返回的有限案例，研究何種前後路徑能記為反應證據，而不只同側位置。將原點構成來源重用、確認後新增證據、跳過參照、實際日K價域再含分開；比較多段活動是否只是內部變化或提出較大過程觀察需求。保留兩條觀察途徑：已完成跨活動閱讀及原參照收盤位置變化；不強制先有新小價帶才更新背景。

先用現有原參照與原K，不發明帶寬／接近門檻或主要性分數，不把精確點未再含當較大帶不存在。原構成來源結束不是較大正式終點／參照失效；同價、共段、包含、全新、完全分離、最近／最大窗／候選數均不單獨選主父結構。不只堆欄位或重畫同圖；真正新核心歧義才附廣角圖問，舊共享正式角色PENDING_NOT_REASKED不代答。

## 所有原答案與限制仍保留

2884完整上漲→短暫整理→再漲及10/7足夠已答，不宣稱最早辨認日或9/17正式起點。ABC自身較弱／相對舊主要帶跳空更弱；人工4/7至6/2共39、6/2仍內6/3在外；6/2新低非通用終點、5/14內跳非通用切分；5/13 H31.40、C31.10低於5/12 C31.20，影線局部代表保留。G2人工1/16至8/16共136、5/2 H40.25代表保持；二月3/1返回、4/21另次不倒接；正式全成員價界未知。舊主要帶2023-06至2025-04僅月精度，不配日端點／價界／主代表，未挑戰舊高前不因小核心先降重要性。

1/27、6/3、11/25非關鍵／小窗撤問、局部與整體／異質大整體保持不重問；重複版本不加票，OHLC不推日內先後。Raw公司行動、五年Adjusted、歷史公開可得、完整日曆／原九待核非窮盡且兩股缺日分開、Darvas正文、SQLite未知保持；G2 8/3缺日保留不宣告連續性。原2高2低與3%／6%／12%不改。

## 恢復與重現

本機/workspace/scratch/89f271ea68f4/reference-path-research；ROOT為程式所在目錄、BASE為同層研究。原2884 /workspace/scratch/54685b8dac93/independent-level-review/source-data-2884.json SHAab87a51b5b8afd076603f290b10f415bd60d31ae47c5ab2f6d9d609ad4014901；1101 /workspace/scratch/54685b8dac93/real-review/input/comparison-data.json SHA184bdef0b687ec0ab7bfcaaac2157ff7916fbc1000ef312d81b5efc0c2e73e15。各1213保存筆至2026-10-16，volume_shares_scaled原字串不改。字型/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf。

其餘六輸入及SHA見source-provenance。需observation-bundle-research的observation_bundle.py與evidence-extensions，overlap-role-research的overlap_roles.py與registry，followup-role-research的registry及selected-role-proposals，source-role-research registry，以及broader-observation-research/reading-proposals.json。Git前核6c6eaf8下對應docs/visual-discussion/20261021_structure_link_bundles_work_review、20261021_overlap_fresh_evidence_work_review、20261021_separated_followup_roles_work_review、20261021_original_source_roles_work_review、20261021_broader_observation_topics_work_review恢復，核SHA後重定位。不得下載新行情或重算core補檔。

只用前輪純解碼／投影函式，不執行舊driver或builder。未有新變更不重跑本批；新研究另目錄記真實次數及新QA。前baseline與extend_evidence防覆寫保護保留。前輪完整交接 ../20261021_broader_observation_topics_work_review/WORK_HANDOFF.md及其前鏈持續有效。
