# 里程碑：0.4候選明示研究選擇來源綁定

起始9d7931c4dad658044385751533736f216423a91f，本地與遠端相同且淨；原/workspace/Twstockai、dev/m1-v018-chart-annotations及唯一Codex。只完成使用者指定選擇接線，未開代理／分支／worktree。

## 可用能力

既有choose_saved／Journal SELECT／READ與來源核對接受明示choice-input/0.2 → choice/0.2。新增純READ的research_quantity_source helper；來源包裝capital-saved-quantity-source/0.1內必有原完整0.4 quantity_request及generation。原choice/0.1及after-retry 0.2來源保留。不是只放寬schema，不把0.4降版、不偽造after-retry包裝。

完整綁來源／request／generation／baseline指紋、原account快照、權利／reserve、截止與時點、原始合成opening或checkpoint類別、origin/latest及全部reviewed token／attempt IDs、完整單位來源／通道／基底／版本／available_at、full_search政策及逐點收據。明示incumbent/destination另在choice/0.2的source_roles保存，來源整體指紋已綁原角色；READ及來源核對均核角色，不靠數量推定。

直接重用quantity_choice_rules與原_qualified；另檢查保存單位、變動量、FULL角色與搜尋收據一致。只對原成員作明示選擇，不重新估成本／風險／最佳量。原帳權利與一般reserve留存；新opening的checkpoint／latest=null，不捏造原帳；既有checkpoint只接受已結清無活單／應付／未解除不可賣股的受控狀態。

主例B93記RECORDED_CONDITIONAL_RESEARCH_INTENT，等待交割仍需重評；非單調正例B2記一般研究意圖。HOLD／明示GRID／退出A可沿自身資格選擇；FULL不合單位不會誤擋合法HOLD。舊觸發FULL只有0新增，不能冒新買資格。完整UNKNOWN／錯配／超限或不存在候選拒絕，不轉選勝者或續抱。

## 凍結、修正及實際結果

實作前凍結32份精確input／expected、source指紋、baseline及三份舊版控制。凍結原件全部不變。actual/保存首次接線結果：三個checkpoint正例因新READ guard誤套after-retry的輸入token慣例而遭拒。追查原resume發現它本來就會union checkpoint／previous全部token，原始輸入token清單可以空，但保存baseline已含完整歷史；新READ應檢查保存union，不要求重寫舊input。

修正這一個新guard；原帳、core、continuity及所有數值程式未改。initial新helper source以單一已知差異還原並與actual/source-versions的長度／SHA完全相符，留在diagnostics；原先診斷存檔因目錄不存在失敗，也如實記於token-intake.json。修正後final/全部checkpoint正例通過，原空input仍原樣保存，沒有補token或重算generation。

另發現凍結missing-token反例的input與checkpoint-new-trigger正例bytes完全相同：原輸入本來就是[]，所謂「刪除」沒有改變任何資料。其REFUSED預期被實際內容反證，沒有改oracle迎合結果；原件／第一次actual／final實際結果保留，該案在final合法成為條件意圖。32原凍結案中31與原預期相符；這1份錯誤反例不計已驗拒絕。另在corrections事先凍結真正刪去保存baseline歷史token的結構反例及REFUSED預期，保留checkpoint並重簽baseline自有指紋以測內部回連，沒有執行數值引擎；保存actual精確拒絕SAVED_TOKEN_HISTORY_CONFLICT。

有效驗收為31原案＋1更正後反例，另1份原錯誤oracle留史，不稱全部原32預期符合。原數值producer的判定、oracle與歷史全部保持。所有案例是合成／READ診斷，不是獨立市場樣本。

## 必要驗證與自審

tests-initial.log本輪8個唯一方法首次全部PASS；不加案例數、build兩階段或任何歷史PASS。方法驗證凍結／原件／protected source、有效綁定與全部原帳token、錯配及真正漏token、Journal相同內容重送bytes／mtime不變／ID衝突保留／IO UNKNOWN、READ不選擇或寫檔、已重簽但內部矛盾的單位／delta／收據／角色／帳戶拒絕、fresh process禁止數值producer imports與網路、三份舊choice結果精確相容、既有文字讀取與完整Decimal環境／input不變。

沒有重跑generate、decide、resume、replay、simulate、ledger、舊suite／九路徑／市場六方案或producer。checkpoint只用原lifecycle._snapshot純READ校驗，不呼叫continuity或重建帳。Journal、原匹配、CLI、view及數值source保護指紋全部不變；僅research_choice.py／research_choice_source.py新增分支與一個標準庫helper。修改既有有效交接時，原prefix與所有歷史bytes完整保留。

## 尚未支援與複核界線

保存指紋及結構核對不是外部來源認證，不防任意重新造假及重簽整份相容資料；搜尋收據只驗保存序列／端點一致，不重新證明數值最大量。拒絕或未知資格保持；不能單看內層core feasible繞過外層batch／unit。舊choice READ不重算／不隱式遷移。

新choice/0.2尚未接舊research_operation／supplement／多份比較，不新增同類READ工具。未接任何成交、條件單啟動或策略執行；無行情／來源擷取或市場回放。1101 UNKNOWN、70／2／其中8／真實總淨合格0、正式flags全false／主壓力null、全部來源parents／P0-3/P0-4及圖形人工保持。R2/F、來源認證、自動解除衝突、原未支援帳務、Astra／第一工作區救援原件未讀狀態保持。

依里程碑自審、原分支正常commit/push及GitHub固定SHA原件讀回。無人工操作、搬檔或例行Work驗收需求。下一步只先核既有明示研究操作如何重用這份來源／選擇，不另造選擇、保存、READ或策略工具。
