# 一次明示合成研究操作：RUN／READ 0.1

現在可用一次明示RUN，把原候選生成、保存讀回、明示選擇保存與來源核對串起來。程式不幫你決定股數、比例、候選或來源；沒有明示選擇就停在候選清單。一般與等待交割的條件意圖分開，仍沒有委託、成交或正式交易資格。

直接閱讀最終文字：

- [一般意圖：明示新增B1，目標A60／B26／C2](views-final/general.txt)
- [條件意圖：原全換仍須等待交割重評](views-final/conditional.txt)
- [舊觸發：保存拒絕，不改選其他候選](views-final/old-trigger.txt)
- [沒有選擇：保留候選並停止](views-final/no-selection.txt)
- [搜尋超限：生成停止，沒有選擇](initial/actual/search-limit/readable.txt)

## 可直接使用的READ

在`股票系統M1_v0_18`下：

```sh
python3 -B -m capital_research.research_operation_cli READ --store capital_research/research_operation_20261027/initial/runs/general --id demo-general
```

這只讀本輪保存原件。預設文字，`--format json`可看完整回覆。READ不接受`--input`，不生成、不重新選擇、不重新執行來源核對verdict，也不寫檔。顯示原結果與分階段保存狀態；缺最終結果只顯示已保存前綴，不補算或自動續跑。

新RUN的完整合成請求已在[example-request.json](example-request.json)，包含原始生成輸入、明示選擇／理由及紀錄時間；不需要使用者搬檔。工程使用時執行：

```sh
python3 -B -m capital_research.research_operation_cli RUN --store <明示的新保存目錄> --id <新的明示操作ID> --input capital_research/research_operation_20261027/example-request.json
```

此例固定為合成研究，非真實建議；不要套入真實交易。已存在操作ID的RUN不重跑，只要求明示READ；不同請求沿相同ID亦拒絕。原選擇／來源核對CLI完全不改。

## 保存與停止界線

純數值仍由原`quantity_after_retry.generate_after_retry`負責；外部`research_operation.run_operation`沿原Journal保存四個固定key：`ID--request`、`ID--generation`、`ID--choice`、`ID--result`。完整請求以canonical `request_json`字串保存、指紋綁定，不改原輸入數值或舊schema。選擇與核對只使用同一份生成後保存並讀回的結果，來源binding由此導出，沒有自動挑來源。

每一階段的保存與研究結果獨立。`SAVED_AND_READ_BACK`不代表資格合格；`UNKNOWN`不假稱保存成功。任何保存失敗就停止，保留已有檔案；明示READ可確認已保存事實。若最終結果已寫入但回應不明，READ可讀回原結果；缺結果則`INCOMPLETE_SAVED_PREFIX`，不靠重跑修復。

生成拒絕、缺選擇、選擇遭拒、條件意圖、一般意圖與來源核對狀態分開。只有一般／條件意圖會繼續來源核對；拒絕的選擇會保存拒絕並停止。省略selection欄位拒絕輸入，明示`selection:null`則先生成候選再停止，不自動選HOLD。

## 本輪實際驗證

先保存[契約](CONTRACT.md)、[精確輸入引用與預期](input-expected.json)、[故障預期](fault-input-expected.json)及版本指紋，再執行。完整操作／Journal在`initial/runs/`，RUN／fresh READ回覆在`initial/actual/`；[summary](initial/summary.json)列五種結果。五個新明示合成RUN各呼叫原生成入口一次；不是舊suite、九路徑或真實producer重跑，也不是五個獨立市場樣本。

[6個唯一測試方法](tests.log)首次通過，實際執行6次，不加歷史PASS。驗證原本金1430、A60／B25／C2、現金275.100、一般預留100及完整checkpoint state未改；所有歷史權利、latest、fills、未成交狀態及tokens沿原帳保存，沒有新會計。

[四階段UNKNOWN診斷](initial/fault-actual.json)在暫存副本用明示cached backend，原Journal保存後注入OSError；只證停止／保存／READ機制，不冒新數值RUN或真實斷電。請求、generation、choice回應不明時不繼續後段；result回應不明可明示READ讀回已保存結果。診斷保留回覆、READ及前後指紋，暫存副本不當長期原件。

[同ID重送／不同請求](initial/idempotence.json)不重跑、不覆寫；[四種跨階段錯配](initial/corruption-actual.json)在暫存副本驗READ拒絕且不修復，包括不同generation、缺choice、跨操作result與缺歷史token。fresh READ禁止數值引擎import、生成／選擇／來源check／Journal.save、寫檔、刪改與網路。公開RUN另驗只寫指定store及不連網。

自審補上「明示選中目標」文字：`initial`數值與JSON結果未改，舊CLI／原文字留史，最終文字看`views-final`。只補驗四種受影響的fresh文字READ，沒有新候選RUN或重跑六個方法；CLI main的AST不變，僅渲染函式增加已保存選擇顯示。最終來源指紋以`source-versions-final.json`為準。

## 尚未支援與未驗

本版不提供缺選擇後補選、失敗／中斷自動續跑、多程序競爭的exactly-once保證。真正斷電、撕裂partial及目錄持久性未在本輪重測，沿原Journal拒絕／保留界線。SOURCE_CHECK_REFUSED保留防衛分支；本輪核對成功與跨階段READ錯配已驗，未另造替換來源的完整RUN矩陣。

READ的指紋與接線校驗不是來源認證或通用防造假。候選目標、估計成本與假想意圖不是實際持股、成交、策略勝負或市場績效；沒有擴行情或1/13成交。原條件仍須當期新帳與證據重評；新批仍須新獨立觸發。全部正式flags false、主壓力null，1101 UNKNOWN／拒算、70／2／其中8／合格真實總淨0及原來源／圖形／人工契約保持。

基線2ccfae04a71124ce36b581181ab131666e0c6850；原唯一Codex／原工作區／分支依既有里程碑自審、正常commit/push及GitHub固定SHA讀回。固定SHA以Git／回覆為準。沒有人工操作需求，不預設Work逐輪驗收。R2/F、來源認證及原未支援帳務不擴張；Astra及第一工作區救援原件仍未取得未讀。無新來源、私人文件、bootstrap、UI／Android、樣本外、部署／交易／付費／訊息。
