> 最新已答（2026-10-20 17:26）：使用者確認「ABC是自己一個區間沒錯和舊大帶相比他就是跳空下跌，更為弱勢的區間」。本例USER_CONFIRMED_CASE_DO_NOT_REASK，A/B/C同自己的區間，舊PENDING已關閉；勿沿助手A-vs-BC暫案拆出A。原圖冊問句及下方文字保留為裁決前歷史；最新看[使用者判讀與證據](../20261020_april_interval_user_decision/README.md)及[完整續接](../20261020_april_interval_user_decision/WORK_HANDOFF.md)。不據此泛化所有跳空或自動歸屬，舊帶重要性不調降。

---

請接續股票系統M1，仍在Work用實際廣角圖討論右端「構成來源」與「後續反應」的核心差別。新問題PENDING_USER_ADJUDICATION：四月急跌A及其後低位反彈B、再下探C，哪些是舊帶本身構成、哪些只屬後續反應？可分開，不必整月同一角色。助手工作假說是A先作後續轉弱觀測、B/C先獨立保留低位局部觀測，未有歸屬依據不自動納入舊帶；未獲答，不當批准，不交Codex實作。

儲存庫blue1998-glitch/Twstockai，分支dev/m1-v018-chart-annotations，本輪起點84e0dd176d6f98d994cd6d3c45978688e5c19925，研究提交與逐檔回讀見本目錄GITHUB_READBACK.json，收據另回讀；最新以實際HEAD為準。先確認包含起點、e0bd48c9245c877fda8ebca5598f69ff346a99cb／e45d972406cc6a4ef1a9babf1ba9865d97073096及fff47915523fab8c8de8279de8bbb7a26b05647b；若有更新先讀最新交接保留全部成果，不用main或舊ZIP覆蓋，不能讀GitHub明說未取得。

依序讀AGENTS.md、CONTINUE_IN_WORK_MODE.md最上方、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md最新節；全文讀docs/visual-discussion/20261020_april_role_visual_review/README.md、pending-decision.json、evidence.json、verification.json、GITHUB_READBACK.json及本檔。看output/pdf/m1-april-role-study.pdf兩頁：第1頁保留原597筆全景，第2頁放大閱讀2024/7～2025/6全241原K/量/均線/MACD，標A/B/C。PNG原尺寸也提供。圖冊是新研究討論附件，不是重建原互動產品或新瀏覽器截圖。

圖片放大要求已落為可用PDF檢視器開啟的兩頁檔，第2頁向量線／K／嵌入字形，可用檢視器放大；第1頁是原高解析圖。已實際兩頁PDF渲染檢查，不冒稱Android手勢或App流程已驗。原圖／來源／核心／query／reaction保持，不再讓孤立68筆小窗代整體。新圖附原尺寸連結，未測操作不填通過。

A=2025/4/7 O29.20 H30.80 L29.20 C29.80量118,749,437，紅K但較前保存4/2 C32.40跌；B=4/10 O30.95 H31.20 L30 C30.75量48,104,987，綠K但較4/9 C28.50漲，6%高4/18確認；C=4/22 L28.50 C28.60，6%低5/5確認，高於4/8 L28.45不補相等破低。5/13 H31.40只是已答局部背景不重問。對B77原研究下緣30.05，4/7在下→4/10在上→4/11 C30在下，保留反覆，不以此判正式界線或解除。

本輪問角色，不重問已答月份跨度、局部與整體可分判、異質形態整體、重要性不先降、5/13／6/3／1/27；不要求精確終點或公式。舊共享來源角色PENDING_NOT_REASKED、小窗一月問WITHDRAWN_RESEARCH_WINDOW_INSUFFICIENT及11/25本例非關鍵點保持。後續反應可用於觀察舊帶，但是否構成來源須分辨；本輪尚未核准正式來源成員。

本輪實際：build_study.py只讀原comparison SHA184bdef0b687ec0ab7bfcaaac2157ff7916fbc1000ef312d81b5efc0c2e73e15，原241連續索引/OHLCV/MA/MACD字串直接保留，核原值跨30.05；reportlab沿用全景頁、Matplotlib新向量頁、pypdf合併核頁數及文字，pdftoppm渲染兩頁、view_image逐頁實看。首稿CFF Type42警告改Type3字形後無警告重繪看最終頁；CLI整理後渲染與已看圖全等。原源數值不變。沒有原引擎／MACD／reaction重算、source query adapter CLI、bootstrap、14／22或舊產品測試、新ZIP／瀏覽器／Android。重新查本機仍無瀏覽器執行檔，不安裝不file://；Android NOT_TESTED_NEW_BUILD。

成果及實際證據同分支逐檔回讀，未讀未測未執行不標完成；結束提供最新已核提交、圖冊入口、完成未完成及完整續接，仍Work。primary_pressure_id=null、歷史選取null／historical_signal_eligible=false，正式成員區界代表／量權重增量／衰減重要性／合併直接承接／解除生命階段未知。保留前輪完整限制如下，不改原核心參數策略庫歷史舊頁案例及main，不調參硬編，不部署付費交易訊息子代理。以下前輪「本輪」是歷史，不能當此次重跑。

---

請接續股票系統M1，在Work依原圖廣角、已完成source-query與新來源角色底稿研究正式整體歸屬。使用者17:09新增要求：之後新圖要能放大，這次可沿用；已記錄display-preference.json，不冒稱放大操作／瀏覽器／Android已驗。不要重問11/25本例非關鍵點或已撤回的小窗三選一。

儲存庫blue1998-glitch/Twstockai，分支dev/m1-v018-chart-annotations，本輪起點6e1d84d584824b1c02cf650a43e6173caad619d4，研究提交及逐檔回讀見本目錄GITHUB_READBACK.json，收據另回讀；最新以實際HEAD為準。先確認包含此起點與e0bd48c9245c877fda8ebca5598f69ff346a99cb、e45d972406cc6a4ef1a9babf1ba9865d97073096及fff47915523fab8c8de8279de8bbb7a26b05647b。若有更新先讀最新交接保留全部成果，不用main／舊ZIP覆蓋，不能讀GitHub明說未取得。

依序讀AGENTS.md、CONTINUE_IN_WORK_MODE.md最上方、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md最新節；全文讀docs/visual-discussion/20261020_attribution_roles_work_review/README.md、evidence.json、verification.json、display-preference.json、GITHUB_READBACK.json及本檔。沿用broad_context_correction/597筆全景與rally_path_work_review完整價量，不重做已完成圖表、來源反查／adapter／CLI或reaction。

新底稿列四種助手候選角色：A早高位、原3%九點下移含反彈、B77原6%十點後段反覆、四月轉弱／低位反彈待歸屬。全部formal_membership=null，不是正式成員批准。左端A6/5原39.25被B16／17／18引用，但三箱從4/19、4/26、5/2開始；右端B77來源末3/12／整箱3/24確認、無四月點，而B44／80四月來源延到5/13、整箱5/14／5/27確認。整箱全收／全丟都不足表達這個人工整體研究描述，先把原來源、原箱引用與候選角色並列，不改原箱、不裁月份為正式邊界、不自動吸納40.25或五月來源。

直接讀原6%／segment0連續五點：2025-3/12 H35.45／3/24確認→4/8 L28.45／4/10→4/10 H31.20／4/18→4/22 L28.50／5/5→5/13 H31.40／5/27。最後四ID全等B80四來源；B44同日期價位但原ID／尺度／確認分開。前四點用來看右端原過程，第五為後續背景，不猜正式終點。相鄰不等正式直接承接。4/22發生四月但6%確認在五月，發生、確認、整箱確認、正式歸屬不可混用。

原query九點3%同段完整全串／原K核等，末段反彈保留；10/24低31.35和11/28高35.50與B77有同座標但原ID／確認不同，僅對照，不把跨尺度相接冒同尺度路徑、不批准共享角色。原共享交界仍PENDING_NOT_REASKED。本輪只讀原core這段，不冒稱原query有新增反查或漏檢。

本輪只執行研究audit.py：核A三箱引用、query九點同尺度全串、B77十來源、原K值與確認、兩組同座標不同ID、右端6%五連續點與B80後四來源、B44／80來源日期價位各自確認及原comparison／query SHA不變。不匯入M1引擎。無產品修改／核心MACDreaction／source query adapter CLI／bootstrap／14、22或舊產品測試／新ZIP／新圖放大UI／瀏覽器Android。Android NOT_TESTED_NEW_BUILD，file://不重試不繞過，前輪缺Chromium未解除。前輪「本輪」仍屬歷史，勿冒稱重跑。

下一步仍Work，不交未定自動合併／選主壓力給Codex。primary_pressure_id=null，歷史選取null／historical_signal_eligible=false；正式成員區界代表／增量量權重／衰減重要性／合併直接承接／解除生命階段未知。三已定概念、月份39筆5/13、6/3、1/27與全部已答更正不重問，未挑戰舊帶高點前不因低位整理先降本例重要性保持。全套限制沿以下前輪完整指令，不調參硬編，不改原核心參數策略庫歷史舊頁案例及main、不部署付費交易訊息子代理。成果保存同分支逐檔回讀，結束附已核SHA、入口、完成未完成及完整續接。

---

前輪完整續接（歷史）：

請接續股票系統M1，在Work用既有廣角原圖及完整價量路徑研究正式整體歸屬。不要回到一月小窗三選一或將11/25升關鍵點；兩項更正已定不重問。本輪接續c12f1c0b638b5fcd325a3abf5d78115df6e15783，研究提交與逐檔回讀見本目錄GITHUB_READBACK.json，收據另回讀，最新以實際HEAD為準。儲存庫blue1998-glitch/Twstockai、分支dev/m1-v018-chart-annotations；若有更新先讀最新交接保留全部成果，不用main／舊ZIP覆蓋，不能讀GitHub明說未取得。

依序讀AGENTS.md、CONTINUE_IN_WORK_MODE.md最上方、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md最新節；全文讀docs/visual-discussion/20261020_rally_path_work_review/README.md、evidence.json、verification.json、GITHUB_READBACK.json、本檔。沿用前輪broad_context_correction的597筆原圖，不新繪、不裁回小窗；原source-query、reaction與圖表均完成，不重做。

新原值進展：完整廣角中讀2025-01-13～03-24的43筆，僅原低點至原6%高點確認的研究窗，非正式整體／局部／波段起訖。同窗最大量在2/25（57,322,068股，H35.10／C34.95），最高收在2/26（C35.25／H35.35，量35,394,831），最高日高在3/12（H35.45／C34.50，量22,178,529），三者分開。35.20原2024/7/26高作明示研究參照；全43筆收上只有2/26，次筆2/27收35.10回下、日高35.20相等；日高上35.20有2/26、3/5、3/12，不能把影線過當收過。3/13 H34.40 C33.40量41,559,442回落。原3/12的6%高點到3/24才確認。

整段最高35.45仍低於原2023/11/28高35.50達0.05，全43筆無H達35.50或原A39.25；不將這些參照指定正式整體代表／區界或將有限窗冒全歷史。原11/28/2023 H35.50 C34.50量65,709,089，11/30 H35.30 C34.95量106,415,572；左側最大價與較大量日不同，不能只拿轉折當日量概括形成區。3/12與3/13 DIF／DEA正但柱負、價格回落，直接讀原MACD無重算。

助手研究方向：完整路徑中原值接近／跨越／收盤保持或跌回／後續反應需一起看，單根轉折及當日量不足承擔正式整體歸屬。本輪沒有把3/12另升關鍵點、沒有定量須提前幾天、選窗、量權重、價量雙過或自動合併公式。這不是新工程契約；不交Codex實作未定規則、不重做已有query/reaction。

本輪只執行研究audit.py讀取原JSON，核43連續原索引及原OHLCV／MACD字串、同窗三最大值／逐筆Decimal三參照關係、原6%確認及相鄰三筆；原comparison／query SHA不變。既有PNG從GitHub核等，無新繪圖、瀏覽器、產品源碼／引擎執行、bootstrap、14／22或舊產品測試、ZIP或Android，Android NOT_TESTED_NEW_BUILD，file://不重試不繞過；前輪Chromium缺失未解除。原已答／未解規則與限制完整沿下方前輪指令，保留其歷史資格，不當本輪執行。

下一步仍Work以足夠廣角研究完整價量過程的整體角色，不要求使用者替機械來源版本分段作無效選擇。正式成員區界代表／增量量權重／衰減重要性／合併直接承接／解除生命階段未知，primary_pressure_id=null，historical_selection_time=null／historical_signal_eligible=false。源值發生／確認與後來研究選取分開。未挑戰舊帶高點前不因低位整理先降本例重要性保持；原共享來源角色PENDING_NOT_REASKED。

成果保存同分支逐檔回讀，未讀未測未執行不標完成；結束提供最新已核提交、入口、完成未完成及完整續接。保留原核心參數策略庫歷史舊頁案例及main，不調參硬編、不部署付費交易訊息子代理。以下為前輪完整續接，前輪「本輪」均是歷史：

---

請接續股票系統M1，在Work依足夠廣角的真實價量背景研究整體歸屬。最新使用者更正已記錄，不重問：「你的圖不足以分析，應該說分析了也沒意義。範圍太小了。我只知道11/25的高點價量都沒過因此也不是關鍵點。」本例指2024-11-25。前輪一月分段三選一已撤回WITHDRAWN_RESEARCH_WINDOW_INSUFFICIENT，不是使用者選第三項，也不能留PENDING催答；不把下一步當批准。原轉折資料保留，但不升關鍵點。

儲存庫blue1998-glitch/Twstockai；分支dev/m1-v018-chart-annotations；本輪起點3e74a88e10e8413f3fb446d9b3363b4bd7939f4a，研究提交與逐檔回讀見本目錄GITHUB_READBACK.json，收據另回讀，最新以實際HEAD為準。先確認包含起點與來源反查交接e0bd48c9245c877fda8ebca5598f69ff346a99cb、成品e45d972406cc6a4ef1a9babf1ba9865d97073096、原真實圖fff47915523fab8c8de8279de8bbb7a26b05647b。若有更新先讀最新交接保留全部成果，不用main或舊ZIP覆蓋；不能讀GitHub明說未取得。

依序讀AGENTS.md、CONTINUE_IN_WORK_MODE.md最上方、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md最新節，全文讀docs/visual-discussion/20261020_broad_context_correction/README.md、USER_CORRECTION.md、user-correction.json、evidence.json、verification.json、GITHUB_READBACK.json及本檔，看broad-price-volume-context.png。再沿前輪version_continuity_work_review/WORK_HANDOFF.md的完整歷史鏈，但其一月待答問題已被撤回；其餘原值與限制保持。所有舊成品與驗收是歷史，不能當新跑。

本輪新廣角為同原comparison保存2023-01-03～2025-06-30全597日K／量／原MA20、60、130、260與MACD，靜態研究圖不是產品UI或新瀏覽器截圖，不重算指標、轉折、箱或reaction。圖窗包括已答月份前後，非正式成員或起訖。更左40.25保留但不整箱納入人工整體。核原comparison SHA184bdef0b687ec0ab7bfcaaac2157ff7916fbc1000ef312d81b5efc0c2e73e15、原core result sha256:ec7bca9ed6aa176c328fd8c4e94a31ea66967832e7089ac20a44090461f49da4、query SHA4a43a8c0f03bbffacb86306f064b7c807a7a83bdaf7e737bc76cd654a2c1dbb0保持。render_context.py僅讀研究，不匯入引擎。首稿y低限25.5裁到六月K，改min原low−0.50重繪實看最終圖；不是原資料修改。

11/25原高34.20、量43,141,500；助手例示對照2023/11/28高35.50／量65,709,089皆低；與2024/9/30高34.20相等，量41,315,092則略多。用Decimal核原值，單日量不當整區量或權重。使用者未明示唯一比較錨或量口徑，勿擅補其意思為某日或泛化價量雙過門檻。已定本例11/25非關鍵點，不重問、不抹原算法來源；算法轉折≠結構關鍵點≠正式整體代表。

下一步先研究較早高位形成、整段下移、後段反覆及反彈回落的價量關係，建立有意義整體角色，再決定局部是否值得細分。不要用局部版本前綴或30.80跨越直接要求使用者判整體歸屬，也不因新廣角就自動合併全窗／指定最高價或最大量為代表。原共享交界角色仍PENDING_NOT_REASKED。本例舊整體未挑戰高點前不因低位整理先降重要性保持。

本輪完成更正保存／撤問、597筆只讀原值及精確比較、靜態圖視覺檢查與GitHub同分支逐檔回讀；未實作正式歸屬或新關鍵點算法。沒有bootstrap、原產品源碼修改執行、source query／adapter／CLI、reaction_facts、原辨識MACD、14／22或其他舊產品測試、ZIP、瀏覽器／Android。前輪缺Chromium未解除，Android NOT_TESTED_NEW_BUILD，file://不重試不繞過。

primary_pressure_id=null、歷史選取null／historical_signal_eligible=false；後來研究選取不是歷史訊號。正式成員區界代表／增量量權重／衰減重要性／合併直接承接／解除生命階段保持未知。相等不補過破、日OHLC不證日內順序，五月十月全部反例、原拒絕餘量−2.4800／−0.7825、來源發生確認與實際選取時間、89版本84幾何非獨立、49轉換非訊號及不同窗不排名保持。原A三箱／六月前40.25、九點末反彈、119前33後77背景／不猜終點／不同座標確認各自保持，不自動吸納或跨尺度冒同尺度路徑。

原已定局部整體分判、異質形態整體及不先降舊帶重要性，月份39筆5/13、6/3、1/27均不重問。Raw公司行動、五年Adjusted、歷史公開可得、九待核非窮盡日曆、Darvas、SQLite未知，核心NOT_ESTABLISHED／分類NOT_VALIDATED／行動NOT_EVALUATED。保留原核心參數策略庫歷史舊頁案例及main，不調參硬編日期價格答案、不新增自動選關／正式解除／量門檻，不部署付費交易發訊息子代理，不重讀101圖／0.4.3／舊手機驗收。真正新核心歧義用足夠背景真實圖，已定規則或可重現工程缺陷才交Codex。成果保存同分支逐檔GitHub回讀，未讀未測未執行不標完成；結束附最新已核SHA、入口、完成未完成及完整續接指令，仍Work。
