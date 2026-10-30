> 最新更正（2026-10-20 16:42）：使用者拒絕此小窗作分析依據，指出11/25價量未過、非關鍵點。前述一月三選一已撤回 WITHDRAWN_RESEARCH_WINDOW_INSUFFICIENT，不是選第三項，不再待答。本頁下方保留歷史；最新以[廣角研究與使用者更正](../20261020_broad_context_correction/README.md)及[完整續接](../20261020_broad_context_correction/WORK_HANDOFF.md)為準。

---

請接續股票系統M1，在Work研究正式整體歸屬。本輪新增「2025年1月B74→B76跌到舊研究下緣以下再回升」的具體局部圖，待使用者判讀結構延續／向下擴張、另成新段或證據不足；不是調降舊整體重要性或正式解除。使用者只說下一步，尚未裁決，不當批准。共享交界舊問題亦PENDING，不重問。

儲存庫blue1998-glitch/Twstockai，分支dev/m1-v018-chart-annotations；本輪起點37194f7f9ff5e96cdfbc1914841607496627246e，研究提交見本目錄GITHUB_READBACK.json，收據另回讀；最新以實際HEAD為準。先確認包含此起點及e0bd48c9245c877fda8ebca5598f69ff346a99cb、e45d972406cc6a4ef1a9babf1ba9865d97073096與fff47915523fab8c8de8279de8bbb7a26b05647b，若有更新先讀交接保留全部成果，不用main／舊ZIP覆蓋。不能讀GitHub明說未取得，不假設已讀。

依序讀AGENTS.md、CONTINUE_IN_WORK_MODE.md最上方、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md最新節。全文讀docs/visual-discussion/20261020_version_continuity_work_review/README.md、本檔、evidence.json、decision-state.json、verification.json、read-provenance.json、GITHUB_READBACK.json並看january-continuity.png。它是同原comparison逐筆摘出的新靜態研究圖，不是原互動頁新截圖或產品UI改版。68筆2024-11-01～2025-02-14全部保留，原OHLCV／MACD／MA20／60字串不重算；render_study.py僅研究讀取、精確比較和Matplotlib顯示。原圖脈絡沿讀前輪overlap-context.png，不重做已完成圖表、來源反查、adapter CLI或reaction_facts。

具體：B74舊研究下緣30.80／2024-12-20確認；2025-01-10收30.25在下，1/13日低30.05且收30.50，1/15收30.80相等，1/16開31.20收30.95在舊界上（綠K但較前收上），回升後又回落；2/12收31.90、新6%低點及B76才確認；2/13收33.45、2/14收33.05。B74八來源ID是B76九來源完整前綴，新來源為1/13低30.05／2/12確認。30.05界線只畫2/12之後，不倒灌當時未破30.80。DIF／DEA與柱值分開，不把柱轉正等於DIF正或買賣訊號。

新待判只限此例局部結構的分段身分；先用具體圖討論，不讓使用者訂公式。即使答覆亦只記人工案例，不硬編日期價格答案，不直接實作自動合併、分段、主壓力、正式解除或重要性。尚無泛化充分判準；原來源前綴只證版本連續、跨界只證原研究界的價格事實。當時原值可知、來源確認、本輪後來選取分開，歷史選取null／historical_signal_eligible=false。primary_pressure_id=null。已定局部與整體分判、整體容許不同形態、未挑戰舊帶高點前不因低位整理先降其重要性保持，不重問舊月份39筆／5/13／6/3／1/27。

本輪實際執行只讀研究程式與PNG視覺核看，核68連續原索引與完整原欄位、前綴及新增來源／時點、三個Decimal收盤比較、原comparison及query SHA不變。無bootstrap或產品源碼修改／執行、原辨識MACDreaction、query adapter CLI、14／22或任何舊產品測試、ZIP、瀏覽器或Android。本輪PNG不能冒稱瀏覽器截圖／產品通過，前輪缺Chromium未解除；Android NOT_TESTED_NEW_BUILD，file://不重試不繞過。

沿用以下完整前輪續接與所有未解限制；其「本輪」是前輪歷史，不能當新一輪重跑。下一步仍Work裁決本例或續做有區辨力的原圖正反例；已定規則／可重現產品缺陷才交Codex。成果與實際證據同分支逐檔GitHub回讀，結束提供最新已核提交、入口、完成未完成與完整續接，不部署付費交易訊息子代理。

---

前輪完整續接（歷史，不重置最新）：

請接續股票系統M1，同Work研究正式整體歸屬，沿用已完成來源反查，延續「中間路徑＋來源版本身分」的正反對照，不重做查詢、圖表或reaction_facts。

儲存庫blue1998-glitch/Twstockai；分支dev/m1-v018-chart-annotations。本輪已核起點7b0450bcab4074e1eee05cc78db66b265647908d；來源反查交接e0bd48c9245c877fda8ebca5598f69ff346a99cb；來源反查成品e45d972406cc6a4ef1a9babf1ba9865d97073096；原真實圖fff47915523fab8c8de8279de8bbb7a26b05647b。先確認最新包含以上提交；若更新先讀最新交接保留全部成果，不用main或舊ZIP覆蓋。不能讀GitHub明說未取得，不假設已讀。本輪研究提交見docs/visual-discussion/20261020_intervening_path_work_review/GITHUB_READBACK.json，收據本身另回讀，最新以實際HEAD為準。

依序讀AGENTS.md、CONTINUE_IN_WORK_MODE.md最上方、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md最新節。全文讀本輪README.md、本檔、evidence.json、read-provenance.json與GITHUB_READBACK.json。沿讀前輪membership_vs_reaction_work_review README／evidence／decision-state及whole_membership_work_review pending-decision／junction-evidence。原共享交界正式角色仍PENDING；使用者只有下一步，不能當批准，本輪不依賴其答案也不重問。

沿用已全文讀的deliveries/m1-v019-source-query-20261020/README.md、WORK_HANDOFF.md、GITHUB_READBACK.json，graph_diagnostics/SOURCE_QUERY.md、source_query_validation_20261020/驗收報告.md／verification、request與source-query.json；原SOURCE_QUERY_CONTRACT、來源歸屬研究／user-decision及reaction_pressure_work_review/USER_CORRECTION.md保持。原reaction_facts契約／facts與全部來源限制沿用，不重讀101圖／0.4.3／舊手機驗收。

本輪先整理正面研究描述：A早段高位＋原9點下移及末段反彈路徑＋B77原反覆區。B77十原高低點、五個高來源為2023-11-28／35.50、2024-07-26／35.20、9/30／34.20、11/25／34.20、2025-03-12／35.45；各原確認分別2024-01-16、8/15、10/24、12/20、2025-03-24。末高較前高升1.25但較首高低0.05，不補相等或突破，不因此選B77或A作正式整體代表。以上是候選角色描述，不是正式成員批准。

新對照B6研究32.50～34.70，與B77價域重疊；但中間B6原path依序：2022-12-21收34.05在內→2023-01-12收35.40上方→9/6收34.40回內→9/13收35.30再上→9/20收34.35回內→10/18收32.45在下。獨立掃描原OHLC與上述全部原轉換全等，沒有重新算原path／核心。B6原確認日至B77首來源前一筆為198保存記錄，2023-05-02日高40.25／收39.90為該窗最高；40.25不因這次對照就自動歸人工整體或指定代表。

同一2023-06-28～10/23的80筆窗口內，價格有收上B6研究高界、有收下低界，但全日高仍低於A原39.25。A發生後817保存記錄亦均未達其39.25；僅保存Raw記錄，資料日曆／公司行動限制不變，不宣稱完整歷史或A是正式整體高點。不同參照被如何走過，是可觀察路徑差異，不作重要性排名或跨窗比較。

同時保留反例：檢查比較檔已保存7條同尺度來源前綴版本邊，其中B74→B76包含離區再回返。B74原2024-12-20確認、研究下緣30.80；2025-01-10收30.25跌到舊界下，1/15收30.80等於舊下緣，原path INSIDE含相等；B76到2/12才確認，研究下緣擴到30.05。B74完整來源ID是B76來源串前綴。不能用離區回返直接宣告全新獨立結構，也不能用後來30.05倒灌成當時沒跌破30.80。版本關係亦不證正式經濟同帶。1/15相等不補站上，原FAILED_UP等事件名稱不當已驗短線假突破或正式解除。

本輪研究進展是加入可區辨的候選維度「中間離開與回返路徑」並用來源版本反例約束，尚未獨立樣本驗證充分歸屬判準。下一步仍Work比較具體歸屬假說的正面依據、反例、缺證；同價不直接合併，離區回返不直接切新帶，前綴版本不直接認證正式同帶。沒有新的時間、距離、量、衰減、解除或買賣門檻，不交Codex實作未定自動分段／合併或主壓力選取。真正新核心歧義用具體真實圖討論，已定規則或可重現產品缺陷才交Codex。

原工具、圖表、reaction均保持。本輪只讀保存core／path／OHLC／7來源前綴邊，原comparison SHA184bdef0b687ec0ab7bfcaaac2157ff7916fbc1000ef312d81b5efc0c2e73e15、source-query SHA4a43a8c0f03bbffacb86306f064b7c807a7a83bdaf7e737bc76cd654a2c1dbb0及原result身分不變，原源高低與K欄位核等。舊真實earlier-descent.png從GitHub逐byte核等，圖窗5/2～次年1/19不含較早B6，綠框仍B77，不冒稱畫了B6。本輪無新瀏覽器嘗試／截圖、query adapter CLI、原辨識MACDreaction、bootstrap、14或舊測試、新ZIP或Android。前輪Chromium缺失未解除；Android NOT_TESTED_NEW_BUILD，file://不重試不繞過。14測試／27檔回讀與fixture初敗修正是原工程歷史，不當新跑。

前輪已核局部39筆最高31.40未到B77研究高群34.20～35.50；B44／B80同四源跨四五月，5/14／5/27才確認，不能回填四月已形成。形成來源、後續觀測與正式歸屬分判，不能因價域重疊或含舊來源升格正式成員／壓力因果。4/30是月份閱讀末日不是正式終點。共享交界問題未答，不能因本輪新維度把它標已核准。

已定三概念及月份、39筆、5/13、6/3、1/27不重問；本例未挑戰舊帶高點前不因低位整理先降重要性，亦不因新例額外排名／加權。不擅定39.25／35.50／35.45／40.25為正式代表。五月反覆站回跌回／紅K較前收跌、十月日高過而收未過／相等低／正MACD跌回、全部原路徑與日OHLC不證日內順序保持。

primary_pressure_id=null，歷史選取null／historical_signal_eligible=false；原query selected_at為2026-10-20T07:30:12.393327+00:00，不當歷史訊號。正式成員、區界代表、增量、量權重、衰減重要性、合併直接承接、解除及生命階段未知；原拒絕餘量−2.4800／−0.7825、來源末點／確認／研究離箱／人工終點、49轉換非訊號、89版本84幾何非獨立型態、不同窗不排名保持。Raw公司行動、五年Adjusted、歷史可得、九待核非窮盡日曆、Darvas、SQLite未知；核心NOT_ESTABLISHED／分類NOT_VALIDATED／行動NOT_EVALUATED。

保留原核心參數策略／庫／歷史／舊頁／案例證據及main，不調參硬編答案，不部署付費交易訊息或啟動子代理。成果及實際證據保存同分支逐檔GitHub回讀；未讀未測未執行不得標完成。結束提供最新已核提交、入口、完成／未完成與完整續接指令，說明仍Work或已定工程可轉Codex。
