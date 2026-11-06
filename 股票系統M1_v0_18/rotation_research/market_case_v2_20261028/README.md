# ②主線案例情境0.2：可保存與查當期前綴，尚無市場成交／績效

本輪只完成能力核對的第1項：舊①案例另版適配為②。原0.1程式、資料、manifest、actual與保存JSON全部留原樣，沒有改寫帳務、來源資格或合成capital入口。

- [白話報告](REPORT.md)、[事前契約](CONTRACT.md)
- [原②輸入](input.json)、[手定預期](expected.json)、[精確正反例](cases.json)
- [最終原②actual](final/actual/draft-II.json)、[13項最終診斷摘要](final/summary.json)、[8方法測試log](tests-first.log)
- [未來變體前綴證據](test-evidence/future-prefixes.json)、[純呼叫／零引擎證據](test-evidence/fresh-pure.json)
- [舊成果保全](preservation.json)、[變更manifest](CHANGE_MANIFEST.json)

|案例截止|新增可保存的案例事實|不能由此推定|
|---|---|---|
|4/9|②淺回檔承接機會；24.80守位|4/10已成交、24.80自動全退|
|4/10|③圖形機會；普通開25.35、零股首筆25.60兩素材|既有持股自動加碼、兩通道同價同容量|
|4/15|④較深失守；B截至此時圖形可進場；局部32.85與原35.50並存|自動賣A、正式買B許可、已知⑤反證|
|4/17|尚未完成後續新低|提前知道4/22的低點及反證|
|4/22|⑤回升未收復、再低於④低點的反證|回填4/15／4/17決策、批准X5退出|

25.35與原4/10 RAW open相符；25.60僅有使用者轉交Work摘要，逐筆原件／首筆時刻／容量仍未知。普通日開盤不當零股成交，日量不當首筆容量。①4/9開25.50另存排除上下文，不作②成本。B的32.85沒有擅找原K日，原35.50仍具獨立參照角色；6488不加入本案例。

本金、N、股數、減少比例、預留、共同期間、風險／概率／排名／執行模型仍全null；K/X4/R4_X5/X5全UNAPPROVED。原輸入不選素材，控制正例才明示單一素材ID，亦不批准模型、生成委託或成交。

純API為`market_case_v2.prepare_context(request,saved,work_summary)`與`prepare_context_prefix(...,as_of='2026-04-15')`。日期、價位、參照和案例角色由外部輸入；不是新入出場策略。case_context_on是回顧研究時軸，不是已認證的歷史available_at，usable_historical_signal_ids仍空。

前綴只投影有日期的類型化角色／參照，不直接複製可能包含後續內容的整段來源文字；原文保留在input及work-summary.json。完整來源／input身分與prefix_id分開。後來價格、反證或未來模型價無效，不改較早前綴。

外部IO只用`market_case_v2_io.prepare_and_save_context`，重用原load_saved與Journal exclusive保存讀回；沒有新READ工具、CLI或回測系統。直接看final/saved/II-context-draft.json可審閱保存結果，不需使用者操作終端或搬檔。

最終證據看final/。根actual、summary與source-versions-before-run是初始診斷；當時6488已被拒絕，但拒絕碼較早落在主線綁定；補明確範圍檢查後另存final，沒有改oracle或覆寫原件。diagnostics保存初版source與說明。13案例不是13項測試或市場樣本；8唯一方法一次通過，不加歷史PASS。

來源0.10／全部parents仍不完整、正式旗標false、主壓力與報酬null；市場數值回放／qualify／帳戶重建均0。Work v0.24及JSON0.16兩Library原件未讀，work-summary.json只是使用者摘要。Astra／救援未讀及原1101 UNKNOWN、70/2/其中8/真實合格0不變。


保存期間新增的遠端文件已正常合併：32a8cbd、52e95b2、d226ba0及2d211f1的純價量市場環境/資金閉環目標全部保留。最新三根目標節置前，本輪②進度緊接，歷史原文不刪。新增目標文件已全文讀，沒有據此擴本輪到冠西電/市場閘門或新策略。程式與已測source不變，未重跑測試。原本輪manifest已留diagnostics，最終CHANGE_MANIFEST核合併後實際檔案；詳upstream-integration.json及最終對話固定SHA。
