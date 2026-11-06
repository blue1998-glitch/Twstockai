# 完整Work接續：原參照後日K相交與分時點方向見證

2026-10-21；blue1998-glitch/Twstockai／dev/m1-v018-chart-annotations。前核提交507cf5efa3e84a814211f1cc580fd0a06eb726e6。新研究提交、逐檔回讀及收據提交／最終HEAD按本目錄GITHUB_READBACK_RECEIPT及實際分支核，不預填。先讀AGENTS.md、CONTINUE_IN_WORK_MODE.md、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md最新節，再讀本交接及README。

## 模式、目的與授權

維持Work研究局部反應與較大結構，不轉產品接入或正式分類器。最高目的仍為資金增值閉環＋正向資本成長飛輪，AGENTS／CONTINUE最高目標置第一節、PROJECT_VISION不改；本輪未評估行動、交易或飛輪成效。

使用者允許下一步一次多步，有重要性才問；例行研究、核對、修正、同分支保存回讀直接做。真正新核心歧義才附廣角真實圖提問，不重問原已答。使用者以圖形交易、非工程師、Pixel9Pro手機優先，直接給對照，不用欄位／測試數代替用途。保留main、全後續、原引擎策略參數／來源／原圖。不部署、付費、交易、發訊息或開子代理。

## 新進展與研究界線

**當日價域相交並收在原側，是當日位置事實／反應候選，不是支撐壓力成功的固定標籤。** 兩個G2原低對照都從上方到達、當日收回上方，後續一例收盤上移，一例下一筆下移。兩個後收見證日量都比第一根相交日大，方向卻相反；量較大也不能單獨指向上漲。

凍結第一根日K相交K的原高低，只作描述地標；後來影線、首個後收在地標上／下、連續相交列及當前路徑分時點另存。沒有規定所有反應必須跨此地標，也沒有把它當正式箱界、帶寬、停損或行動門檻。「接觸／相交」只指保存日K價域包含原價，不證日內先後或精確成交。原點形成K及確認當日不當已確認後更早的新反應。

本輪六事後指定對照／22截止視圖／四合資格出生見證，研究資料見queries／response-witnesses／summary。先以原保存3%點與原K作一次事後探索挑不同路徑：G2既定範圍173、A0、ABC36重疊出現，包含跨原點與日期重用，且選例用了後來資料，非歷史盲掃描、獨立樣本、回測或成敗率。exploration-notes保存限制。

## 四個主對照與兩控制

| 對照 | 完整證據與時點 |
| --- | --- |
| G2原3/13低36.15，3/23確認 | 3/28前筆C36.65，當日L36.10 H36.65 C36.20仍原低上；3/29 L36.05影線下探；4/6 H36.70影線先上越凍結K高，但4/10以前仍無後收離開該K36.10至36.65；4/11 C37.45才第一次後收在上。3/28至31相鄰保存列四筆相交，4/6是第一筆後續不相交。接觸量27286673、見證量32191913，皆原整數 |
| G2原5/15低37.15，5/30確認 | 7/7前筆C37.25，當日L36.90 H37.50 C37.30仍原低上；下一保存筆7/10 C36.85下於凍結低36.90。7/7至10兩筆相交，7/11才不相交；不是兩次獨立測試。接觸量19465674、見證量26003083。與上例同收盤側、見證量同較大，但後續方向相反 |
| ABC原4/10高31.20，4/11確認 | 5/12 L30.80 H=C31.20，恰等原高不嚴格收過；凍結30.80至31.20。5/13 H31.40 C31.10，影線上越但收仍在凍結範圍，5/14 C30.35才後收在下。5/12至13同一段兩筆相交。原5/13 H31.40代表保持，31.20不升主壓力 |
| ABC原4/8低28.45，4/10確認 | 6/2 L27.65 H29.05 C27.70，已收在原低下，並非收回原側；6/3 C26.85下於6/2低27.65。6/2仍人工ABC第39筆；後續下移與6/3整根原框下不定通用正式終點 |
| A跳空控制 | 10/15原值整根在47.35上但無日K價域相交，不生本類相交出生見證。前批收盤跨原參照觀察仍保持，不能因沒相交就忽略跨越 |
| G2形成來源控制 | 原5/2 H40.25於5/9才確認，5/2截止遮罩原參照；5/9可回看形成K，但它不生確認後新反應見證。原代表與人工完整136筆保持 |

兩個G2主對照均在已答人工完整1/16至8/16共136筆內，不能把正向／負向局部證據直接當整個大G2成立／終止。5/2 H40.25代表不被這些局部原低取代。ABC人工39與舊較大主要帶保持，局部參照不升主壓力。

## 狀態與程式契約

出生birth含原確認日、第一相交K、前筆保存K、原參照相對收盤側、凍結K原高低、成交量整數及精確比值、witness ID，後續追加不回寫。相交段current_range_intersection_streak是相鄰保存列的 bookkeeping，不是區間／獨立反應次數。指定續段K不得再當新第一根，程式拒絕重複起點。

followup保存第一個後收嚴格在凍結K上／下，另存先出現的上／下影線；同日收恰等K高／低仍非嚴格離開，雙影線不能推日內先後。成交量只比原始整數、保存精確分數，不給放量／縮量／異常或進出資格；零分母不造比值。若首見證前有已列缺日，保留LISTED_DATA_GAP_BEFORE_WITNESS、不跨接認證。已發生見證後出現的資料缺日仍在當前路徑附資格，完整日曆始終未認證。

followup方向是首見證的過去事實，不是當前趨勢。後來返回保留birth與首見證，更新observed_path最後一筆；雙方向返回已合成核。當日／確認日／後收見證日與事後選例時點分開，不能把4/11結果填回3/28，也不能因7/7收原側便當日寫有效支撐。

## 實行與QA

探索命令1、新研究driver1；新verify2，第二次新增後來返回不改首見證的雙方向合成後重驗，driver未重跑。新圖builder2／渲染2，首圖看後將原參照標籤移離後段K線；最終兩頁逐頁實看綁SHA。PDF output/pdf/m1-post-reference-response-witnesses.pdf及兩PNG，P1兩G2相反後續，P2兩ABC時序，四價圖與量對齊，紫色只沿第一相交K及其原量範圍著色，無滿高背景。舊圖builder0。

驗證22視圖／源前綴／未來價量與人工標籤污染／未可用參照值污染／正式未知，13凍結與首後收獨立核、26影線、13相交段、18精確量描述；同原側且見證量較大但方向相反1、影線不補後收1、ABC相等→影線→後收1、穿過／跳空／形成源控制1、4出生固定、續段拒絕1、雙方向相等雙影線零量2、返回2、缺日1、7來源SHA通過。這是有限研究與截止隔離核對，不是市場分類率或通用充分條件。

原core／MA MACD／pivot box reaction／CLI／adapter／bootstrap／舊產品測試／舊研究driver皆0重跑；無新行情、瀏覽器、Android。未新增原pivot、turn、箱／局部候選、主參照選取或價格百分比／量門檻。人工已答未送函式。

## 未完成與下一步仍Work

支撐／壓力作用、量資格、重要性與正式反應規則未定；support_or_pressure_response_demonstrated／volume_qualification／importance_score／formal_reaction_confirmation均null。正式形成起末成員／價界／主結構／父子合併／衰減生命階段仍未定。formal欄位／selected_role／primary_pressure_id／historical_selection_time=null，historical_signal_eligible=false，10/7原core snapshot／numeric_frame仍無不補造。分類器NOT_VALIDATED、用途NOT_ESTABLISHED、新Android NOT_TESTED_NEW_BUILD、行動與capital_growth_flywheel_effectiveness=NOT_EVALUATED。PDF不是Android驗收。

下一步Work將這些當日候選與後續正反路徑回連既存局部活動及較大原參照，研究反證只改當前片段，或需要重新檢視較大觀察；不把單次正負反應或量較大直接當整體成立／終止。保留前批兩條觀察途徑：完成局部活動的跨活動閱讀，以及原參照被收盤跨過即可更新的觀察問題，不強制先有新小價帶。研究證據充分與結構狀態／行動資格分開，不因時間經過提高確定性，也不先發明可信度／機率／主要性分數。

不只堆欄位與測試數或重畫相同圖；用有差異的真實價量對照推進。真正新核心歧義才附廣角真圖問；原共享正式角色PENDING_NOT_REASKED不代答，已答案例不重問。

## 原裁決與來源限制全保留

2884完整上漲→整理→再漲、10/7足夠已答，不宣稱最早或9/17正式起點。ABC自身較弱、相對舊主要帶跳空更弱，4/7至6/2人工39、6/2仍內6/3在外；6/2新低非通用終點、5/14內跳非通用切分；5/13 H31.40 C31.10低於5/12 C31.20，原影線代表保持。G2人工1/16至8/16共136、5/2 H40.25代表保持，正式全成員價界未知；二月3/1返回、4/21另次不倒接。舊主要帶2023-06至2025-04僅月精度，不配日端點／價界／主代表，未挑戰舊高前不因新小核心降重要性。

1/27、6/3、11/25非關鍵與小窗撤問、局部／整體、異質大整體保持不重問；相等不嚴格過破，OHLC不推日內先後，重複版本及重疊候選不加票。原2高2低、3%／6%／12%不改。Raw公司行動、五年Adjusted、歷史公開可得、完整日曆／原九待核非窮盡且兩股缺日分開、Darvas正文與SQLite未知保持；G2 8/3缺日不抹去、不宣告整體連續性。

## 檔案恢復

本機/workspace/scratch/89f271ea68f4/response-witness-research，ROOT為程式本目錄、BASE為同層研究；response_witnesses.py、verify_witnesses.py、build_figures.py及queries／response-witnesses／summary／exploration-notes／verification／source-provenance／figure-build／manual-qa。只用前輪純解碼／投影，不執行舊driver或builder。

原2884 /workspace/scratch/54685b8dac93/independent-level-review/source-data-2884.json SHAab87a51b5b8afd076603f290b10f415bd60d31ae47c5ab2f6d9d609ad4014901；1101 /workspace/scratch/54685b8dac93/real-review/input/comparison-data.json SHA184bdef0b687ec0ab7bfcaaac2157ff7916fbc1000ef312d81b5efc0c2e73e15。各1213保存筆至2026-10-16、volume_shares_scaled原字串；字型/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf。

其餘五輸入及SHA見source-provenance：需observation-bundle-research的observation_bundle.py／evidence-extensions，overlap-role-research的overlap_roles.py／registry，followup-role-research的registry及selected-role-proposals，source-role-research registry。Git前核507cf5e下對應docs/visual-discussion/20261021_structure_link_bundles_work_review、20261021_overlap_fresh_evidence_work_review、20261021_separated_followup_roles_work_review、20261021_original_source_roles_work_review恢復，核SHA再重定位。不得新抓行情或重算core補檔。

未有新變更不重跑本批；新研究另目錄記真實次數與新QA，前baseline及extend_evidence防覆寫保持。前輪完整交接 ../20261021_reference_paths_work_review/WORK_HANDOFF.md及其前鏈持續有效；保留全後續，不以舊ZIP／main覆蓋。
