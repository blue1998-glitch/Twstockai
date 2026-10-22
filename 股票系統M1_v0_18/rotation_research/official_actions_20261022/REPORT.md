# 本輪實測與來源缺口

## 實際完成

- 分支起點6185297ed145f325bc1a19d99067a6aab084ce65，包含使用者指定50d8c5e及全部後續；fetch／ff後沒有遠端後續被覆蓋。重新bootstrap --hydrate-missing成功，0補缺、7合法差異保留，見bootstrap.log。
- Runtime spec 3且觀察current，兩官方域列入允許；network policy state仍unknown，不以設定證明可讀。實際取得兩個玉山官方PDF：議事錄1,572,950bytes、完成報告64,317bytes；URL／時點／SHA及PDF／文字對照均封存。
- 2025-06-13會議／2024盈餘同次增資議事錄PDF第19頁明載每股面額10元、股東股利增資1,602,000,000元／160,200,000股；第20頁表決通過並授權調整配股率。議事錄「約每千股10股」與最終金額分開。
- 依已存最終每股金額0.10015129／有來源面額10，導出0.010015129股／原股，保留公開精度；不認為已驗最終未圓整比例／每人實配。
- 官方執行情形PDF第1頁報告7/28基準、8/27發放完畢；只補公司層級報告，不補新股掛牌日或個人淨到款。零股政策與現金元以下捨去已存證據，實際截止／處置未核。
- 新catalog 0.2僅補原一個股票股利組件，保留父ID及新指紋／來源欄位；四個現金組件完全相同。原0.1／日曆與策略不變。
- 執行17項新定向unittest全部通過，重建122價量原件／原輸入一致，70日曆合格研究窗仍全部拒算、2不足，真正總淨報酬0合格。沒有六方案新回放／排名或市場績效。

## 失敗及修正（保留原證據）

1. MOPS官方入口server-java/t39sb01?quick=1回應HTTP200、800bytes，但正文是「因為安全性考量…THIS PAGE CAN NOT BE ACCESSED」。原HTML與SHA已存；判為SECURITY_DENIAL_NOT_EMPTY_DATA，停止該來源，不重試／繞過、不執行其外部腳本。這不是公司行動查無資料。
2. 初次producer因pdftotext -layout把表格兩欄交織而拒絕解析後續執行報告；initial-producer-failure.log及原-layout文字／抽字收據均保留。改用同原PDF的pdftotext -raw依閱讀順序另存文字／收據後才通過，不改PDF或憑猜測填值。
3. 初次17測試有1項錯誤：測試預期簡寫REFUSED，而原引擎實際完整狀態是REFUSED_INCOMPLETE_EVENT_ACCOUNTING。tests-first.log保留；只修正新測試oracle，未改原引擎狀態。修正後17項通過（tests.log）。

## 仍未完成

- 整段完整公司行動／減資與其他權利異動覆蓋、2026-07-25～10-16權息；MOPS安全拒絕不能替代完整名冊。
- 2884最終直接未圓整配股比／實際配股精度、新股可交易日、零股併湊截止／每人處置與現金。
- 股利淨分配的投資人證據，或來源明確且稅籍／情境明示的稅費模型；真實淨到款、期初持有／除權息權利。不得預設零稅、零費、零既存權利。
- 真正總淨報酬窗口仍0；沒有合格新成交路徑比較、勝出比例或正式全換／分批規則。
- 原1101 2025-08-13及2884 2025-11-05市場開市但個股無報價，原因UNKNOWN，未補價。Raw公司行動共同基底／五年Adjusted、歷史公布可得及SQLite根因未完成。
- 原44、18／9982、Chrome36及前輪15測試是歷史，本輪未重跑；無新UI／瀏覽器／Android，Android保持NOT_TESTED_NEW_BUILD，file://不重試。

打包後另以新目錄解壓執行17項及離線producer，校驗原375包成員、雙層舊manifest與新manifest並逐檔遠端回讀；實際結果見delivery bundle-receipt、package-verification及GITHUB_READBACK，未執行前不得引用為通過。保留檢核見preservation.json。
