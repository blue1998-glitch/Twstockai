# 同原帳兩輪明示合成案例0.1（事前契約）

本輪只完成原已授權的兩輪連續使用案例，先重用cash_action.evaluate及cash_action_execution.execute，不另建協調器、READ工具或會計。若既有入口直接支援，不改任何產品模組；只在定向actual證實缺口時最小修復。所有候選、數量與模型為明示假想fixture，不定使用者N、比例、政策或策略。

## 第一輪只READ，不重跑

原件為cash_execution_20261028/cases/opening-B20/input.json及actual/opening-B20/result.json，固定基線5d41b937144a239a64e016c7b8accde20c49b3ae。完整checkpoint於1/8 16:00，原始資本1180、B20/C2、現金598.6、一般reserve100、無活單／應付；另有現金權利80及C2股份權利，原窗口1/5～1/12。這是已保存合成帳，不是使用者實帳，不能把當期淨值1178.6重設成新本金。

核原件的完整檔案指紋及原execution/result/checkpoint身分。此READ不執行第一輪、producer或歷史suite，不升資格。完整原checkpoint與origin ledger原樣承接，不能手填帳、清權利或重用原始現金1000。

## 第二輪明示RUN

1/8 17:00決策、截止1/8 16:00。帳戶只能從該checkpoint取得，expected_latest精確綁第一輪。當期review可用原有效B-event，但新增買進是ADDITIONAL_BATCH，明示獨立B-step2事件及不同形成點／量柱／事件token；不能假稱FIRST_ENTRY或用舊觸發重置批次。

正例明示新增B20、family由原入口固定C；edge／成本／風險沿原明示合成模型。外部委託採原保存1/9 B20的委託參數，只改唯一order ID；tape原樣重用cash_execution_20261028/cases/exited-A-buy-B20/input.json的execution_spec.tape，沒有補行情、搬日期、加1/13或推盤中價格。calendar、origin、close proof都取第一輪原件。只呼叫既有execute，不改策略、會計、成交或資料資格。

第二輪輸入／expected與來源版本先凍結，才RUN。完整checked_action沿evaluate產生並保存，execute必重驗完整回條；不是跳過外層gate只看core。六個第二輪請求互斥，只有正例可進入simulate；不把各分支一起花同一現金。

## 手定預期及必要反例

- 正例第二輪B20成本401.4＝20×20.02＋原整元進位費1。第一輪本金1180仍在，不能另注資。1/8已結現金598.6、reserve100；1/9成交後現金仍598.6，應付401.4、嚴格可用197.2，reserve100另列。1/12才現金277.2＝598.6＋原現金權利80－401.4，B40/C4、應收／應付及活單0。
- 原B-event已消耗，第二輪換trigger回舊ID須REJECTED／STOPPED_ACTION_GATE，simulate0。
- 第二輪假稱FIRST_ENTRY，即使原core單獨可行，也須外層拒絕，simulate0。
- 新增B25需501.5，高於598.6－reserve100＝498.6，必須拒絕；不能使用一般預留。
- 新增B30需601.6，高於當期已結598.6，不能把未到位的80應收當現金，必須拒絕。
- expected_latest改成非第一輪前身時，純檢查拒絕；不得給第二輪新帳／新token，simulate0。

逐日核現金／應收／應付、舊及新fills、原單狀態、股份權利、一般reserve、原opening／原資本、latest與所有token。第一輪9個token完整保留，獨立第二輪事件新增3個，合計12，不回收舊事件。新結果READ不重算，不以終點相等代替中途對帳。

## 範圍與保存

本輪僅新案例、必要定向驗證、自審及原分支正常commit/push/GitHub讀回。舊Decimal、未來隔離與未成交機制證據重用，不無故重跑。第一輪歷史PASS不算本輪，六案例不等六個獨立市場樣本；本輪只計實際唯一測試方法。沒有新UI、producer、資格重算、市場回放或績效排名。

原活單／期初應付不中斷續接、限售釋放、R2/F、來源認證、完整分叉矩陣等未支援不擴張。1101期初cash_claims UNKNOWN、70拒算／2不足／其中8換股影響未支援／真實總淨合格0、正式false／主壓力null、來源0.10全部parents／正式action_resolution0.4／圖形人工契約保持。Work原件、Astra與救援仍未讀，不要求搬檔，不部署、交易、付費或發訊息。只原唯一Codex、原工作區／分支，無代理／worktree。
