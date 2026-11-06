# M-R2 受阻補正實際交付

## 範圍及來源判斷

原工作區／原分支／唯一Codex，起始本地與遠端同9143573b0964be9446884d9bac43e2c9a3e2240a，工作區淨，未發現其他活躍工程程序。來源條款、Library與2408的前輪盤點直接重用，不重新擷取或要求使用者搬檔。

原Journal可保存研究／未合格結果，沒有一律要求官方原回應的閘門。資金的`capital_research.evidence.from_saved_layers`與`real_source_gate`另有嚴格資格，本輪不接入、不修改。依使用者本輪明確提供的用途，把四份有原URL及reported原件SHA的少量摘要用於獨立回顧日簿，沒有把它們改稱官方原件認證或已驗available_at。新角色／版本詳父目錄CONTRACT_0_1.md。

**連結本身完成；真實來源資格PARTIAL。** 不能把「有總監讀回聲明」寫成「Codex取得原件」；未重新抓受限歷史端點，市場與FinMind新查詢均0。

## 真實日簿結果

| 日期 | 原完整K前綴 | 當日新增確認pivot | 同日兩市場摘要 | 後續 |
|---|---:|---:|---|---|
| 2026-07-21 | 97筆 | 0 | 總監讀回研究摘要，各自日期相符 | 沒有新增事件，不造事件／結果 |
| 2026-07-22 | 98筆 | 1個HIGH | 總監讀回研究摘要，各自日期相符 | IMMATURE；沒有失守定義／窗，不判成功 |

HIGH原occurred_at=7/21，first_observed_at=confirmed_at=7/22；原ID／body／參照保留。7/21日行與7/22完整結果內的同一日行逐值一致；市場摘要亦逐值等於本輪原輸入，沒有倒填或借別日資料。市場漲跌家數只作原摘要與描述比較，沒有權重／門檻／市場狀態策略；沒有前一供應指數時指數方向UNKNOWN，不擅自借M-R1其他日期。

新存兩個原Journal紀錄，同內容不重寫、異內容衝突；原BLOCKED兩筆仍完整可讀。完整數字、reported報表SHA、原圖形與日簿均在Git外，公開real-actual-final-summary.json只保留日期、來源角色、狀態及核對布林。個股原始回應SHA本輪親自讀回相符；四份市場報表SHA本輪未取得對應bytes，只是總監報告的聲明。

## 後續狀態與拒判能力

不是新辨識算法：只用原箱既有CLOSE_ABOVE_RESEARCH_RANGE與原FAILED_UP_RETURN_IN_RANGE／FAILED_UP_AND_CROSSED_BELOW_RANGE事件，且須同原箱、在原事件之後。已知失守保留原事件，即使研究窗未滿也揭露KNOWN_EARLY_FAILURE；完整供應研究窗分FAILURE_IN_COMPLETE_WINDOW／NO_FAILURE_IN_COMPLETE_WINDOW，後者不等成功。跨資料／基底中斷UNKNOWN，但已知失守不消失。

窗由外部明示日期及來源，不推定最佳天數。合成測試用了明示三筆窗，只是測機制；真實案例沒有窗，不套用。新pivot沒有已核失守定義，當下沒有後續觀察可標IMMATURE，失守評估仍UNKNOWN。沒有窗但已知失守時，status=UNKNOWN並明列known_failure及原事件，不用IMMATURE隱藏。

錯來源／日期／報表URL時點、缺欄、未知數量、基底／缺口metadata錯配、保存結果簽章不符、F-01被改回數值、偽稱原件已讀、母體／散布權被升格、正式許可被設true皆拒絕。檢查的fingerprint只是內容完整性，不是來源真偽認證，也不聲稱可防任意重簽造假。真實資料不能靠改synthetic標記通過；合成結果另標NOT_APPLICABLE_SYNTHETIC，不能冒真實接線。

## 實際測試及失敗修正

14唯一方法最終PASS＝12新增＋2必要F-01回歸。不是九案例／兩個真實日期或分批log相加，未跑舊全套、81日或敏感度矩陣。

- tests-first.log：10方法，9 PASS、1方法因缺價輔助fixture出ERROR，且該方法末尾案例數斷言FAIL。這是同一方法，不加算兩個失敗方法。
- 原core正確拒絕在缺收盤當日生成snapshot；原預期其實要在後續完整日觀察歷史缺價。只修fixture helper不在缺價錨點生成snapshot，**原缺價列／凍結input／expected皆不改**，後續仍UNKNOWN。
- tests-targeted-final.log：該方法、相依來源／事件方法、一個新增缺口與失守接線方法，以及2個必要F-01方法，6 PASS。自審補原缺口metadata精確綁定、沒有窗已失守的揭露，不改原圖形算法。
- tests-label-final.log：合成不得稱真實接線新方法與受影響Journal方法，2 PASS。
- tests-source-final.log：總監角色URL／日期反例及純函式禁止圖形重算／IO／網路的新增斷言，2個原方法PASS，不增加唯一方法數。

合成9案actual與原oracle相符，原首批log留史。最終14方法各自最後狀態全PASS；source-versions-final.json綁最後程式，final-equality.json另證最後程式與兩筆已保存真實結果及九合成後續actual逐值相同。初版source-versions及log不覆寫／不冒充最後版本。

原graph_core0.2、F-01、FinMind adapter／RUN、Journal、正式來源gate及前輪M-R2 evidence bytes均不改。原BLOCKED manifest只對照其固定9143573版本，根接續文件新增段落後不要求仍等舊根文指紋；歷史原文完整留史。

## 限制與停止

市場原件／Library ZIP未取得／未讀、歷史available_at／完整普通股母體／公司行動／散布權UNKNOWN；全市場比率與真實淨績效拒算。1101 UNKNOWN、70／2／其中8／真實合格0、來源parents與正式false／主壓力null保持。2408沒有原件不納入真實結果，人工505參照亦未升格。未改M-R1等待次數、未挑門檻或資金策略。

本次已補成兩日日簿的有限研究能力，原件重新驗證與歷史資格仍未完成；不把PARTIAL改稱全面PASS。自審／正常提交／推送及固定SHA讀回後停止，無需人工搬檔或例行轉Work工程驗收。下一階段唯一主要阻礙是原始市場證據與歷史可得時間的來源資格，非再增加READ工具或挑新策略。

保存前格式檢查發現tests-first.log第1行原始unittest stdout有行尾空白；保留原bytes，不修飾失敗證據。whitespace-evidence.json記精確路徑／行號／SHA，只有該原log例外；其餘本輪程式／文件皆須通過diff --check。這不是新增測試方法或產品修復。
