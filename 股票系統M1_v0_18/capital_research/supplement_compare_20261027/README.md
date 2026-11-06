# 同父補選：共同條件核對與唯讀並列0.1

現在能把同一父操作的多份補選放在一張文字表中。每份先沿原READ完整校驗，再核對完整父綁定；一致才並列，錯配就拒比。一般、等待交割及遭拒意圖各自保持，不會因並列變成可交易，也不加總互斥部位。

直接看本輪保存輸出：

- [一般與條件意圖](actual/general-vs-conditional/readable.txt)
- [加入拒絕對照：未選中／未提供／未執行保持](actual/with-refusal/readable.txt)
- [兩份各自可讀、父ID相同，但原件不同：拒比](actual/same-parent-id-different-content/readable.txt)
- [較晚補記仍是同一保存決策環境](actual/later-record-time/readable.txt)
- [九案例索引](summary.json)、[契約](CONTRACT.md)、[六方法log](tests.log)

## 使用

在`股票系統M1_v0_18`下：

```sh
python3 -B -m capital_research.supplement_compare_read --input capital_research/supplement_compare_20261027/cases/with-refusal/input.json
```

預設文字；加`--format json`可檢視完整結果。manifest明示每欄標籤、父store／ID及補選store／ID，不自動選來源或找最新資料。限2..8欄、唯一單行標籤，沿用舊比較器的資源上限，超限直接拒絕，不抽樣或截斷候選。

外部`read_and_compare`逐份呼叫未改`read_supplement`，核request／choice／result與父原件、來源／資格／保存接線；只有完整READ_ONLY結果才進入純`compare_read_receipts`。純API只校驗已讀回投影的指紋及一致性，不能取代原READ檔案校驗，也不認證任意自填receipt的真偽。

共同條件比較整份parent_binding：父operation／header／request／result、完整generation與source_binding的原帳、截止、latest、token、版本等。相同父ID或股數並不足夠。重用舊欄位差異helper，所有差異都會檢查，只將診斷顯示限制在沿用的64項；截斷不會放行。

## 狀態與數值含義

`COMPARABLE`只表示共同保存條件一致。等待交割仍是條件意圖；遭拒補選可作拒絕對照，目標null顯示未選中、沒有成本顯原件未提供、來源check null顯未執行，均不補零。來源核對失敗或其他未支援結果不提供相符並列。

目標、估計成本、原請求、拒絕理由及補選時間都從保存內容投影。補選時間可以不同，逐欄顯示；不把較晚補記變成新決策或新的available_at。每欄是互斥替代意圖，不能加總股數、成本或資金。ranking／selected_label為null，正式flags false、主壓力null。

沒有後續行情／回放，不比較政策支配、收益或策略優劣。沒有重新生成、選擇、來源check verdict、保存原件、帳務或成交，也未改舊schema或入口。

## 本輪證據與自審

先凍結CONTRACT、精確manifest／expected、[結構fixture配方](fixture-recipes.json)、materialized檔案指紋及來源版本，再實作。原件與所有新READ fixture前後SHA相同，見[preservation](preservation.json)。各案JSON、預設文字、退出碼及fresh READ trace均在`actual/`。

九案符合預期，6唯一方法首次通過，不加歷史PASS。案例包含一般對條件、加拒絕欄、相同父ID不同內容、部分保存、缺歷史token、錯generation、重複標籤、超限及紀錄時間不同。fresh process禁止數值引擎import、生成、選擇、source verdict、Journal.save、所有寫檔／刪改及網路。原件與純API輸入不變；重複標籤／超限在讀任何原件前拒絕。

結構fixture只是從已保存JSON明示改寫並重新指紋的READ反例，不是新producer原件或來源認證。不同父內容案保留同父ID、同generation、同帳戶，僅將無選擇父請求內未用於決策的紀錄時間改成明示13:00，再同步父／child鏈指紋；兩份原READ各自通過，最後由完整共同條件比較拒比。稍晚補記案僅改child明示時間與相依指紋，父綁定不變，因此可並列。這些改寫只在新fixture，舊保存原件不動，沒有新帳務或行情。

## 限制與保存

未做來源真偽認證、任意重新簽署造假防護、完整分叉／並行競爭矩陣或策略績效驗證；來源核對遭拒分支採拒比，未另造完整案例矩陣。1101 UNKNOWN／拒算、70／2／其中8／合格真實總淨0及原來源／圖形／人工契約保持，R2/F與原未支援帳務不擴張。

基線841ab8cdd9750eb4915f69c5924d7bc8ffae52a6；原唯一Codex／原工作區／原分支依里程碑自審、正常commit/push及GitHub固定SHA逐檔讀回，固定SHA以Git／回覆為準。沒有人工操作需求、不預設轉Work。Astra與第一工作區救援原件仍未取得未讀。無新來源、私人文件、bootstrap、舊suite／producer、UI／Android、樣本外、部署／交易／付費／訊息。
