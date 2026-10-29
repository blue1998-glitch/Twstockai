# 全帳戶評估受控轉接里程碑報告

基線64d2bd5dc17012743b07f8ef15bb8771ca2c1a7b，本地與遠端一致且起始工作區全淨。原/workspace/Twstockai、dev/m1-v018-chart-annotations、唯一既有Codex；未開代理／worktree／分支。固定交付SHA見Git記錄及回覆，不把自引用SHA填入oracle。

## 完成能力

新增純 `action_account_metrics.evaluate_saved`，以完整原行動請求／checked／執行結果及可選一份原單續播保存結果為來源。支持原0.1 HOLD／BUY及0.2 SELL；來源、原帳、close.available_at、委託／fills、權利／一般reserve、latest、fact history／token須精確相連。僅讀保存原件，不執行／決策／重播／重建checkpoint，不認證原件真偽。

最小產品差異為新增一個受控來源adapter、`account_metrics._evaluate_snapshots`抽出既有共用檢查／公式，以及原CLI的明示`--source-kind action`。舊quantity API、數值公式、成本、帳本、執行器、來源catalog、策略與歷史schema均保持。舊CLI預設quantity仍原樣；不新增另一套指標或帳本、READ並列工具或自動協調器。

## 凍結、實作與自審

先存新契約、29份精確input／expected、原件指紋及兩份變動前source。`frozen.json`、`intake.json`固定；修前舊quantity入口拒絕新來源的actual保存在`before/`。此為欠缺格式接線，不是舊會計失效。

初版29案status皆符合預期，自審另發現兩個實際漏檢，均是新adapter的來源綁定，不是舊帳本錯誤：

1. 續播保存結果若自行更換原日終可知時間證明，初版仍接受。另存`diagnostics/resume-close-binding/input.json`、expected與before-actual=EVALUATED後，補原root close proof及原決策／帳／可賣／委託身分的精確比對；最終REFUSED，reason=SAVED_CONTINUATION_ORIGINAL_PROOF_CHANGED。
2. 外層請求／收據指紋重新綁定，但derived decision_input的B基底已換、實際保存fact source仍舊時，當時版本仍接受。另存`diagnostics/derived-source-binding`完整input／expected及before-actual=EVALUATED後，沿原source_snapshot校驗宣告與ledger資產source／basis。先由原helper拒絕但文字與事前對外錯誤碼不一致，tests-reviewed.log如實FAIL；不改expected，明確統一SAVED_DECLARED_SOURCE_CONFLICT後最終通過。

兩反例的input／expected與修前actual不覆寫。initial、after-final、final各階段原樣留史；**final-corrected才綁現行產品source**。最終只重驗受新變更／失敗影響的定向集合，沒有為增加PASS重跑無關舊suite。原oracle未修改。

## 實際驗收

最終29凍結案例均符合預期：減碼／退出／拆單／部分續播完整結果、舊0.1 HOLD／BUY及等價UTC時區可評估；部分前綴／停止、缺原輸入、跨結果、改委託、錯前身／原帳／reserve／token、缺fact history、未知權利、缺價／缺日、改日曲線前綴、未來mark、過早評估與資格改寫均拒算且statistics=null。另兩個自審反例最終明確拒絕。

本輪最終8個唯一方法通過。保留三批log：tests-final.log早期8PASS；tests-reviewed.log同集合7PASS／1FAIL（錯誤碼）；tests-corrected.log最終8PASS。只計8個唯一方法，不相加、不加29案例／控制或歷史8／其他PASS。原始freeze／每階段來源／中間結果完整可回查。

手算以原8日日帳驗證：減B3期間應計成長及最大回撤=-3.20/1180；退出B7=-3.28/1180；拆3+4=-5.28/1180；部分賣7後續播=-3.54/1180。原1/5峰值到1/12均未恢復、截尾7日。費稅3／3／5／3已在各自原曲線，只保存不重扣。期末假想退出成本另列，不將cash當NAV，也不將未成剩13當退出完成。

完整原帳1180、一般reserve100、其他C持股／現金股份權利、最新decision／全部token原樣連結。父輪只核對，最終原帳曲線用一次，不把多個累積ledger加總。`validation-corrected/test-evidence/continuous-book.json`與manual-check.json保存核對結果。

必要回歸只重新評估一份既有quantity完整原件，輸出包括evaluation_id與歷史保存expected完全相同；未重跑原quantity producer或舊suite。CLI預設quantity路由以保存expected作回傳控制，action明示路徑在新程序實跑。兩個惡劣完整Decimal Context下，新API完整結果與正常保存結果相同，caller／DefaultContext／input不變。

fresh process禁止載入capital core、execution、continuity、cash_action、quantity及rotation_research，並在API呼叫時禁止IO／網路，仍得到與保存actual相同的完整評估。這證明本入口沒有執行上述producer或ledger，不冒稱重新驗證每筆歷史會計。

## 限制與保存

只支援完整保存合成行動及至多一份同原單的精確續播。未知權利、原未支援帳務、多段續播來源矩陣、通用來源認證／自動解除衝突、R2/F、真實市場回放、策略與樣本外不擴張。29合成案例不是獨立市場樣本或績效；不排名、不定比例／門檻或勝者。

70拒算／2不足／其中8換股影響未支援／真實合格0、1101期初cash_claims UNKNOWN、全部正式false／primary_pressure_id=null、來源0.10全部parents、P0-3/P0-4／reaction_facts／人工基底及原未支援保持。Astra、Work原件、第一工作區救援未取得未讀，不宣稱Work獨立驗收。

保存前核凍結／protected／原件與最終source、函式原文／AST的公式不變、所有擬提交檔及敏感內容。只正常提交本輪相關成果並從GitHub固定SHA讀回，不強推／重設／覆蓋。無bootstrap／真實producer／市場六方案／九路徑／UI／Android／樣本外或部署、交易、付費、訊息。無需人工操作。下一項若授權先核既有保存流程的可重用部分，不新造協調器或未定策略。
