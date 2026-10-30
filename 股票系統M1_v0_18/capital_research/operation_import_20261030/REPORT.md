# 里程碑：research_operation明示承接保存結果

起始本地／遠端同為36b9e2779286537579f6680dd382fee1143b03e2，原/workspace/Twstockai、dev/m1-v018-chart-annotations，修改／index／untracked皆0。只用原唯一Codex，沒有代理、worktree或競爭分支。

## 實際完成

在原research_operation.py新增import_operation及既有CLI的IMPORT選項；仍用原Journal四個階段與_persist讀回，不另建協調器、store、READ工具或數值引擎。新輸入operation-import-input/0.1必須明示完整保存0.4來源與既有choice/0.2；header／result／receipt明示operation 0.2。RUN拒絕偷用IMPORT輸入，舊RUN不變成讀檔或降版入口。

匯入前重用bind_saved_source及validate_record核來源、資格與單位／搜尋收據，核既有choice.request_id與完整原choice-input/0.2及指定來源相符，唯一候選快照精確屬該來源。從既有choice讀取selection與recorded_at只為指紋核對，不重新選量或判斷資格。原source、choice、account／權利／reserve、origin/latest與全部token原樣保存，沒有重新建立本金或新帳。

一般與條件意圖在IMPORT沿既有純來源核對一次，保存verdict；條件B93仍只COMPLETED_CONDITIONAL_INTENT，不代表現在可買。已綁完整來源的REFUSED choice存CHOICE_REFUSED，source-check階段不再前進；不因來源相符而升級。沒有choice不改選HOLD；無可回查binding的REFUSED、舊choice、錯配或不完整來源均拒絕，不假稱已承接。

READ沿原四階段讀取，只校驗保存鏈／指紋及verdict結構，不重新呼叫生成器、選擇器或check_saved。若缺檔則顯示INCOMPLETE_SAVED_PREFIX／UNREADABLE，header雖保留原request副本，也不拿它自動補檔或續跑。

## 凍結與保存actual

先凍結19份精確input／expected及來源版本、原source bytes，並確認反例與正例沒有相同指紋；再實作。五份舊operation READ控制亦於改程式前保存，不呼叫舊RUN的數值路徑。

19案首次全部符合預期：六個可承接結果（B2一般、B93條件、checkpoint新觸發條件、舊觸發零新增、HOLD、UNKNOWN仍拒絕）；十三個INPUT_REFUSED（跨來源、缺source、缺／null choice、舊choice、錯request_id／歷史token／角色、改帳／單位／搜尋政策、不完整generation及缺binding）。INPUT_REFUSED前未寫四階段；valid REFUSED則四階段照存但意圖保持拒絕。所有input原樣未變，actual/summary.json明列每案狀態與來源核對呼叫數。

完整來源與choice讀回值精確等於原輸入；checkpoint正例原資本2180、原持股／權利、一般reserve100、latest及12個歷史／新reviewed token一併保留。這是保存／承接核對，不是新的帳務或總淨值計算。

## 必要驗證與自審

本輪tests-initial.log八個唯一方法首次全部PASS，沒有失敗、修補或重跑；不累加19案例、五舊控制或歷史PASS。測試含：凍結及所有受保護source原件、一般／條件／拒絕完整承接、相同ID無寫入／異內容衝突、四階段after-write回應遺失後UNKNOWN及明示READ、缺中間／最終檔與跨來源階段錯鏈、fresh CLI IMPORT／READ禁止引擎及選擇與網路、舊READ逐值完全相容／既有ID RUN不生成、完整Decimal／input不變。

fresh-cli.json顯示IMPORT只核對來源一次、READ來源verdict重算0；generate／choose／select呼叫0，READ寫檔0。四階段UNKNOWN使用新暫存store保存成功但回應遺失的故障注入，非真實斷電／多程序持久性證明。三個中間階段READ仍不完整；result已落盤但回應遺失時READ可核實原結果，沒有重跑。所有既有檔案保留，IMPORT重送仍只要求READ。

原choice、完整來源binding、Journal、匹配／資格helper及所有數值／帳務source均未改。只改research_operation.py與research_operation_cli.py及既有有效接續文件，另存本輪契約／fixtures／actual／定向驗證。原五份READ完全相等，既有RUN只驗「已存在ID不跑」路徑，沒有重新生成舊結果或重跑舊suite／producer。

## 範圍與限制

本能力只承接完整保存的合成研究來源與既有choice，不新增決策、不選勝者、不生成新batch或訂單。來源指紋與結構核對不是來源認證；不能防重新造假且完整重簽的外部資料。不接缺choice補選、自動續跑、舊supplement／多份比較或成交，也不保證跨程序原子交易。

70／2／其中8／真實總淨合格0、1101 UNKNOWN、正式資格false、主壓力null、來源0.10全部parents、P0-3/P0-4與圖形人工保持。R2/F、來源認證、自動解除衝突與原未支援帳務不擴張。未跑真實producer／資格重算／市場回放／九路徑／UI／Android／樣本外，不補行情或私人權利。遠端救援封存只保留，不解壓套用；Astra及封存內原件未讀不作新增認證。

依功能里程碑由原Codex自審、原分支正常commit/push及GitHub固定SHA讀回；無人工操作或例行Work驗收需求。下一步先依既有優先順序核下一項已定義能力，沒有具體缺口就停止，不為延續而再加READ／並列包裝；尚未決定的買賣規則、比例或風險取捨仍由Work與使用者研究。

保存前遠端新增d12c19e12c7fe6e9eef4ef299f8316d8c66dd742，只同步四根交接及Work保存盤點文件；已讀新增有效節，原文與本輪工程進度並存。舊draft manifest原樣留diagnostics/manifest-before-work-sync.json，現行CHANGE_MANIFEST綁整合後bytes；未動任何舊里程碑manifest、source或oracle，沒有重跑產品測試。正常合併保留遠端父提交及兩份Work核對文件，不把Work研究0.9摘要當Codex已讀全文或已接策略。
