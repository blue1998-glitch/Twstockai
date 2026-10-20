# 兩個已確認區間案例與三個原保存截點

本輪起點10614308622dcd1506b1fed77552bce2a8fcb369，同分支dev/m1-v018-chart-annotations。使用者21:18:28允許一次多步、重要才問；本批沒有新增問題。已確認判讀不重問、已完成圖表不重畫。

[2884原五年／兩年／近期圖冊](../20261020_rising_interval_work_review/output/pdf/m1-2884-rising-interval.pdf)與[1101原廣角及ABC圖冊](../20261020_gap_contrast_work_review/output/pdf/m1-gap-contrast-research.pdf)直接沿用；目前資格分別以兩份user-decision為準，不把舊圖歷史問句當新待答。本輪沒有新圖或PDF驗收。

## 共同案例對照

|項目|2884|1101 ABC|
|---|---|---|
|使用者已確認|上漲中的短暫整理區間，後來再度上漲|自己的區間，相對舊大帶跳空下跌、更弱勢|
|區間與走勢|整理形態與上漲中回檔可同時成立|相對舊帶弱勢與區間內局部反彈可同時存在|
|範圍資格|17筆是助手原觀察窗，非正式起末|39筆是原使用者選取涵蓋，不等完整機器成員表|
|未確認細項|精確成員、區界、正式生命階段等|不將「自己的區間」擅改為各細項皆已定，也不補全部尺度一路下跌|

case-comparison.json把形態、走勢描述、明示參照反應、人工判讀時點分開。2884的整理標籤為true；ABC只有已明確確認的own_interval與相對弱勢，consolidation_interval留null，**未標籤不是false，不作負例訓練答案**。這不是否定ABC也能有整理，而是保持原話批准的精度。

原ABC中4/10收30.75高於前保存4/9收28.50，局部反彈的原事實不改其相對舊大帶更弱的使用者判讀。不從反彈一根就升整體強勢，也不把較弱區間說成內部每根都下跌。

兩個區間的時間涵蓋資格不同，沒有比較寬度、天數、總量、勝率或股票重要性排名。兩案例不是全市場驗證樣本或通用自動辨認條件。

## 2884原保存截點：後來的價不能帶回去

|原保存截點|原記錄數|收盤對9/17高47.35|收盤對10/15高49.50|原3%待確認高|
|---|---:|---|---|---|
|10/14|1211|47.30，在下|來源尚未可知，不輸出價格比較|47.30|
|10/15|1212|48.80，在上|48.80，在下；日高僅相等|49.50|
|10/16|1213|49.15，仍在上|49.15，在下；日高49.95在上|49.95|

三筆待確認高始終UNCONFIRMED_NOT_A_PIVOT。原9/17高、10/1低兩個3%已確認來源ID與確認日三截點一致，不把後來49.95倒填10/14，也不改舊來源。每筆保留原result_id、numeric_frame_id、source-prefix、原OHLCV／MACD／MA及研究參數。

對47.35，收盤是BELOW→ABOVE→ABOVE；對49.50，在它可用的兩筆完成日K中是BELOW→BELOW。這兩筆收盤沒有先站上49.50，不能把10/16命名為已觀察到的「完成收盤突破後跌回49.50下」。日高越過的事實另留；不推日內先後、回測完成或正式突破／解除。對較近參照未收過，也不抹掉對47.35已在上方的事實或使用者已確認整理再漲。

prefix-observations.json是本輪研究核對檔，只有兩個明示來源的有限原值比對，**不是新的reaction附層／adapter／CLI輸出，也不是新引擎回放**。目前工具沒有被改寫或替代。10/14截點對R2只保留本次後來明示選擇的來源日期，不提供未來49.50值；後來人工正面標籤留在案例紀錄，未寫成歷史截點的模型輸出。historical_selection_time仍null，historical_signal_eligible=false。

## 實際執行與交付

audit.py本輪兩次只讀：核原HTML SHA、原包指紋；讀三個既有core結果並核各result指紋、來源數、原數值／兩來源及各時點未確認極值；核兩份使用者裁決SHA、已確認相容描述與不同時間窗；核明示參照可知日期與原值比較。三個結果本來就已保存，核心重算次數0。README措辭修正後重跑只讀核對；沒有以未執行項目填PASS。

原來源：股票系統M1_v0_18/graph_core_chart/generated/M1_v019_graph_recognition_v01.html，SHA fbca1e1d7e82d5dc9dcca8da0d3c8619f59431c1119d2cd8cb4c8ffc8293a724；原comparison SHA184bdef0b687ec0ab7bfcaaac2157ff7916fbc1000ef312d81b5efc0c2e73e15。舊大來源用既有已核本機檔再核SHA，沒有再擷取行情。兩份使用者裁決則本輪與GitHub現存物件核同。原來源與研究參數保持，SHA只綁保存檔，不是公司行動或歷史公布可得新認證。

檔案：case-comparison.json是兩個部分人工標籤案例；prefix-observations.json是三個原截點與明示參照；evidence-contract.json是有限驗收證據與適用限制；verification.json逐項實際核對。它們不等於已執行產品分類器測試。GITHUB_READBACK.json列本批新檔與三根入口逐檔精確回讀，收據另回讀；WORK_HANDOFF.md包含完整續接及歷史資格。

重現可明示原檔：`python audit.py --html /path/original.html --comparison /path/comparison-data.json --rising-decision /path/rising-user-decision.json --weak-decision /path/ABC-user-decision.json --out /path/review`。這是只讀研究核對，並非產品CLI。每次本輪後來選取時間會更新，不回填歷史選取。

## 已完成與邊界

已完成兩例共同部分標籤與相容描述、三原截點／兩參照有限時點核對、原資格及部分未知保留、同分支保存回讀。本批不新增待答，不再對同兩例重新做同一表。

仍未建立一般自動區間形成、選層、正式成員、區界代表、增量量權重、衰減重要性、合併直接承接、正式解除及生命階段。原minimum_high_turns=2與minimum_low_turns=2研究設定未改，不由人工案例直接改點數或調參。有限正面案例不是完整偵測算法，不交Codex硬編日期價位；已定可重現規則或工程缺陷才交實作，本輪沒有新產品缺陷。

primary_pressure_id=null，formal_price_bounds／formal_membership／formal_lifecycle未知；歷史實際選取null、historical_signal_eligible=false。核心NOT_ESTABLISHED、分類NOT_VALIDATED、行動NOT_EVALUATED。人工已定的定性判讀保持已確認，與普遍模型未定分開。

無新行情、原核心MACD／reaction source-query adapter CLI／bootstrap／14、22、60或舊產品測試／新圖PDF／ZIP／瀏覽器Android。Android NOT_TESTED_NEW_BUILD，file://不重試不繞過。跨格式reaction adapter接2884仍未執行驗證，不將本研究檔當成adapter通過。

Raw公司行動／五年Adjusted／歷史可得／九待核非窮盡日曆／Darvas／SQLite未知；兩股待核日曆分開。原五月／十月反例、相等OHLC與來源時點、拒絕餘量、89版本84幾何非獨立、不同窗不排名保持。局部整體分判、異質整體、舊帶未挑戰高點不先降重要性、ABC與上升整理兩已答案例、39筆／5/13／6/3／1/27、11/25非關鍵點及小窗撤問不重問；舊共享來源角色PENDING_NOT_REASKED不由此代答。

下一步仍Work研究可泛化區間形成與輸出條件，直接用此已核有限資料，避免再重建案例表或再問已答形態；真正重要新核心歧義才附廣角可放大實圖問。不改原核心參數策略庫歷史舊頁案例及main，不部署付費交易訊息子代理，不新增自動選關／正式解除／量權重或買賣門檻。
