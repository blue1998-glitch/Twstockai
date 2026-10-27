# 明示合成回放與另存評估0.1

## 已完成的能力

新增外部`evaluated_replay.run_evaluated_replay`／`read_evaluated_replay`及RUN／READ CLI。新RUN沿原quantity_replay.replay_sequence，再將保存並讀回的完整原結果交給原account_metrics.evaluate_saved；Journal分別保存request、replay、evaluation、result。原數值回放／候選／帳務／評估器及舊schema／READ完全未改。

重用原Journal、既有明示id規則與persist保存讀回處理。每一階段確認SAVED_AND_READ_BACK才前進；evaluation record綁operation／header／request、完整replay、評估輸入與evaluation_id；最終結果綁原評估的必要投影。結果qualified與保存成功分開，不自動提高任何正式資格。

READ只核保存指紋、引用、原來源／帳與snapshot、時間、latest／全部token及摘要投影，不載入數值引擎或重算指標。缺結果留INCOMPLETE_SAVED_PREFIX、錯配UNREADABLE；已保存的拒算即使READ_ONLY仍是REFUSED，統計null。既有id不RUN，UNKNOWN不當成功，不自動續跑／修檔。

## 先保存的精確案例與實際結果

契約、三份完整input／expected、來源長度／SHA及故障／錯配規格先凍結，再實作。從既有prefix-only輸入建立**新的明示合成fixture**，parameter_source明標新工程；沒有重算或覆寫舊actual，沒有新行情。完整／不完整案例明示續抱且orders／tape皆空；資格停止案例保留原明示提案，但當期B新資金不合格，不執行它。

1. complete：原回放COMPLETED_PROVIDED_ROUNDS、評估EVALUATED、四階段保存成功。原資本2230，原帳應計2230，成長與回撤0；期末假想退出成長另列。原帳權利正常到位後A110/B0/C2、已結現金1080、一般reserve100、latest與全部token保持。這不是任何交易策略勝出的例子。
2. incomplete：回放完成所給輪次，期末尚有待交股份；評估REFUSED／LEDGER_RETURN_REFUSED，指標與帳戶投影null，原回放原件留存。
3. stopped：當期B資格不合格，原quantity閘門STOPPED_CANDIDATE_GATE；評估REFUSED／INCOMPLETE_SAVED_RESULT，不從停止前狀態補績效。

三個最終新RUN各呼叫原回放1次、評估1次；完整／不完整各委派原simulate1次，停止案0次。原action_ledger是既有回放內必要計算，不謊稱本輪引擎呼叫0。測試裡的排序與四階段故障使用這三份新原件的cached test doubles，不冒額外新回放。

## 驗證、自審與失敗診斷

8個唯一方法首次執行全部通過；只計本輪8次方法執行，不累加上輪8／14、舊suite、案例或CLI子程序。內容含三個精確新RUN、保存先後／讀回同一source、原帳權利／reserve／latest／token、同id重送／異內容衝突、四階段UNKNOWN、六項缺檔／跨階段錯配／自洽改寫摘要反例、fresh READ禁數值引擎／寫檔／網路、真實來源／缺欄位／非法id預檢拒絕。

四個故障為先完成Journal寫入、再模擬遺失ack：RUN均STOPPED_STORAGE／UNKNOWN；前三階段的明示READ只能顯保存prefix，結果階段已完整寫入則能READ_ONLY，均不重算。不是實際斷電驗證。六種損壞僅動新暫存副本，原件前後bytes保持。fresh成功／拒算READ共六個子程序，加一個READ禁止input的拒絕子程序，數值回放／評估呼叫均0。

初次build的監看程式把Journal正常os.fdopen(int_fd)誤當Path參數，產生INPUT_REFUSED，**未進入回放或評估**。保留build.log、actual/complete、空request及監看source快照；只修監看以核fd實際指向明示store，改新runs-final位置繼續，沒有修改production或oracle迎合結果。這是一個先於方法測試的工具診斷失敗，不是額外方法PASS；最終三案皆在build-final.log與actual-final。

自審核對：沒有把停止原件當完整結果、沒有加總重疊帳／費用、沒有更動原數值source、沒有從已保存意圖自動下單、沒有把READ_ONLY當正式資格。既有源檔／fixture與新請求原件前後SHA一致。原checkpoint與token由原引擎保存，新層僅保存／核對引用，不建第二帳。

## 未完成與未執行

只有意圖的generation／choice／supplement不接成交；不補1/13行情。原未支援帳務、外部現金流績效、來源認證、複雜身份合併／完整分叉、自動恢復、多程序exactly-once、R2/F與策略閾值不擴張。沒有實際市場績效、真實producer、資格重算、市場六方案、九路徑／整套舊suite、UI／Android或樣本外測試。

1101帳戶cash_claims UNKNOWN及70拒算／2不足／其中8換股未支援／真實總淨合格0保持，正式flags false、主壓力null。來源0.10及全部parents、正式action_resolution0.4與圖形／人工契約不改。Astra及第一工作區救援原件未取得／未讀；不猜測890檔存亡。Work沒有獨立驗收本輪原件。

目前不需人工操作。下一步需要Work研究：提出一個續抱／移轉的可反駁比較假說，事前列共同市場、風險與資本權利條件，並指出尚未確認的觸發或門檻；工程不自行發明策略或預定勝者。不再增加READ／並列工具，不重做本輪工程驗收。此研究尚未執行。
