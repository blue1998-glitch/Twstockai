# 接續股票系統M1：區間形成研究

儲存庫blue1998-glitch/Twstockai；分支dev/m1-v018-chart-annotations；本批起點a9b292a1b9708b31151f0f7709ba5e6d1953bd7a。最新提交由本目錄GITHUB_READBACK.json與實際HEAD確認。先核包含起點並讀更新，保留全部後續成果、不用main或舊ZIP覆蓋。

依序讀AGENTS.md、CONTINUE_IN_WORK_MODE.md最上方、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md最新節、PROJECT_VISION.md、本目錄README.md／hypotheses.json／evidence.json／control-scan.json／verification.json／WORK_LOG.md／GITHUB_READBACK.json。原完整限制沿../20261020_present_form_reaction_requirements/WORK_HANDOFF.md及../20261020_recognition_timing_user_decision/WORK_HANDOFF.md，不再堆疊複製全文。

本輪新實做：唯讀原價量的價格幾何／收盤走徑／窗內極值距今與末收位置計算，三頁可放大PDF、三原尺寸PNG。2884截至10/7只用1207筆，13筆9/17至10/7僅研究窗非正式起末。所有1195個13筆窗中排除原已列缺日跨窗72，計算1123，128窗為淨下且相鄰全重疊；按位移比最大、同分起日早選4/15至5/4作方向對照。事後極端選取，非盲測、非歷史選取或獨立樣本／準確率。

A和B皆12/12正寬重疊、同價位最大涵蓋9/13；原收盤路徑、末端方向不同。A窗低10/1之後4筆、末收位置約49%；B末筆創窗低、收在窗低。所有尾段3至13完整保存，末3筆兩例比值都1但方向相反。不是採8／13筆或某數值門檻，不把幾何涵蓋當成交分價／籌碼成本；B區間人工標籤null，不能叫整理負例或所有尺度皆非區間。

ABC已確認自己的區間、相對舊帶跳空下跌更弱。原39筆4/7至6/2包含末日低27.65／收27.70，為這窗最低，故末端創低不能一概否定區間存在。第3頁含2023/1/3至2025/6/2背景及39細節，未畫6/2後。39筆為原使用者涵蓋非完整正式來源成員；不新定箱底破底／解除事件，不改6/3在外。回穩證據與區間是否存在必須分判。不要把A的正面回穩特徵當成所有較弱區間的必要條件。

下一個具體目標：研究截止當下自動提出有意義觀察起點／範圍的方法，再檢查價格停留、方向與末端狀態的證據是否持續；候選範圍不能靠人工先指定9/17／13筆。可以推導／實算的研究自行做，保留假說／反例與來源資格；比較候選生成方法而非只再核本例數值、堆欄位報告或問最早日。未有可重現充分規則，不硬編日期價位、調原2高2低／3、6、12%或實作自動正式分箱合併／選主壓力／解除／買賣。重要新核心含義歧義才用廣角可放大實圖問，不重問已定案例。

原10/7足夠辨認整理與上漲中整理再漲均已定。10/7非最早日，不推10/6不足，10/14獨立答案null；10/7沒有原核心／numeric_frame，不補造，也不能以本研究當原分類器漏判修好。本批沒有原引擎／MA MACD／pivot box／reaction source-query adapter CLI／bootstrap／舊產品測試。分類NOT_VALIDATED、用途NOT_ESTABLISHED、行動NOT_EVALUATED；歷史選取null、historical_signal_eligible=false、primary_pressure_id=null。觀察窗長度敏感度不等原轉折尺度或日週月整合完成。

本批research.py7次，原兩源SHA核同，獨立核算24組及ABC39、PDF三頁結構與渲染實看；verify_evidence.py3次。人工QA收據manual-qa.json與最終PDF／三預覽SHA綁定，自動腳本只核人工收據是否對應現檔，不自動宣稱看圖。首次版面重疊及PDF不完整xref已記錄，根因未確定，改BytesIO完成再一次寫出並核字節與pypdf/Poppler通過。這是研究產檔修復，不是原產品故障。無新瀏覽器／Android；Android NOT_TESTED_NEW_BUILD，file://不重試不繞過。不要沿用舊QA當本批新測試。

重現需恢復兩個既有已核原檔及CJK字型，不重新抓行情：
python research.py --source 已核source-data-2884.json --comparison 已核comparison-data.json --font 可用CJK字型 --out 輸出目錄
原source-data Git路徑見evidence.json；comparison為原跨尺度小ZIP抽出的檔，SHA184bdef...，恢復沿最早real-review與來源交接。字型只顯示用途。只在新變更需驗證時重跑，不無故重建完成圖。research.py未呼叫M1引擎。
python verify_evidence.py --source 已核source-data-2884.json --comparison 已核comparison-data.json --out 輸出目錄
verify_evidence.py的視覺QA文字只反映本批已實看的報告；重現者必須重新渲染實看才能在新驗收記錄中聲稱該項通過，不能只跑腳本借用。

全部既有裁決與來源限制沿原完整交接：39筆、5/13、6/3、1/27、11/25非關鍵點、小窗撤問、局部整體分判、異質形態整體、未挑戰舊帶高前不先降重要性均不重問；共享來源角色未另回答不代答。五月十月反例、相等不補過破、OHLC不推日內先後、來源可知／確認／後來選取分開、重複版本非獨立票保持。不比不同窗／股重要性或績效。Raw公司行動／五年Adjusted／完整日曆／歷史可得／Darvas正文／SQLite未知，各股票待核日曆分開；正式成員區界代表／增量量權重／衰減重要性／合併直接承接／解除生命階段仍未定。

仍Work；可重現算法或工程缺陷確定才交Codex。保留main、原核心參數策略庫歷史證據舊圖，不部署付費交易發訊息或子代理。成果同分支回讀，未測不標完成；結束附已核提交、成品、完成未完成與可直接接續方式。
