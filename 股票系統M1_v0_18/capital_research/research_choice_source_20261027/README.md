# 研究選擇與明示來源：純READ核對並列0.1

現在可把已保存選擇紀錄和它的完整來源放在一起核對，確認沒有拿錯generation或只憑相同候選ID借用資格。來源相符與候選合格是兩件事：原來遭拒的意圖仍遭拒，等待交割的仍只是條件意圖。

直接看本輪保存的輸出：

- [一般研究意圖：來源與快照相符](actual/general/readable.txt)
- [等待交割的條件意圖](actual/conditional/readable.txt)
- [來源相符，但候選仍遭拒](actual/rejected/readable.txt)
- [相同候選ID、不同來源：拒絕並列](actual/wrong-source-same-candidate-id/readable.txt)
- [有來源綁定但沒有候選快照](actual/no-snapshot/readable.txt)

## 實際入口

在`股票系統M1_v0_18`下執行：

```sh
python3 -B -m capital_research.research_choice_source_read --store capital_research/research_choice_20261027/journal --id grid-intent --source capital_research/quantity_after_retry_20261027/after-final/new-independent-trigger/actual.json
```

預設文字，`--format json`可看完整核對結果。必須明示完整來源wrapper，不能只傳內層generation或候選ID；不會自動找較新來源。原選擇CLI的READ／SELECT格式與退出碼完全不改。

新命令退出碼0表示來源核對相符，**不是候選合格或可以交易**；錯配／無法核對／讀取失敗為2。JSON中`check_status`與`choice_status`、`candidate_qualification`分開。缺綁定拒絕核對；有綁定無快照只證來源相符，`NO_SAVED_CANDIDATE`不推定已選中。

純API為`research_choice_source.check_saved(choice_value, explicit_source)`，重用未改的`validate_record`、`bind_saved_source`；新CLI沿未改`read_choice`／Journal讀紀錄。所有內容／帳戶／截止／latest／checkpoint／版本／歷史與當期reviewed tokens／receipts綁定須完全相符，再核候選是唯一ID且完整快照相同；來源不對就`columns=[]`。MATCHED才提供選擇保存值與來源保存值兩欄，不改原件、資格或token。

## 本輪證據與驗證

[CONTRACT](CONTRACT.md)、[精確輸入引用／變體／預期](input-expected.json)、[IO預期](io-input-expected.json)與source指紋先保存，再執行；舊oracle、actual、manifest、log與原件不覆寫。

12組定向輸入涵蓋一般／條件／遭拒相符、有綁定無快照、無綁定、不同來源但同候選ID、內層generation、紀錄竄改、快照內容不同、重複候選ID、錯latest及缺歷史token。[summary](actual/summary.json)與各案result.json保存純核對實際值；CLI另保存stdout／stderr／退出碼與READ前後指紋。

其中快照改寫後重新指紋、重複候選並同步內容指紋、錯前身／缺token是明示合成結構變體，用來讓核對防線獨立受驗，不冒新producer輸出或合法來源更正。READ用暫存Journal envelope包裝原保存value；沒有呼叫SELECT／Journal.save或創造新的研究選擇。一般／條件／遭拒三案直接引用庫內保存的合成原件。

新增5唯一測試方法首次通過，見[tests.log](tests.log)，不加歷史PASS。另有缺明示來源、錯Journal ID兩項IO診斷；fresh CLI阻擋數值引擎import、選擇／生成／Journal.save、寫檔、mkdir／刪改、網路及子程序。原始來源及暫存READ輸入前後不變；舊suite、回放、producer執行0。

## 限制

核對只證兩份明示保存內容一致，不證來源真偽、任意自行重新簽署資料的可信度或市場績效。沒有比較兩個策略／外生市場，也不推導哪個候選較好。`NO_SAVED_CANDIDATE`不證候選資格。

兩欄目標／估計成本不是實際持股或成交；不重建完整帳本、現金、reserve或權利，不找行情、不加1/13，不提升資格。完整token仍在JSON；token數不等新批批准或已消耗數。舊READ／schema不重算、不遷移。所有正式flags維持false，主壓力null。

最低基線424689ce351e6fb548e6ff5a3d1c74c84a12e820；固定提交以Git／回覆為準。由原唯一Codex在原工作區／原分支依既有里程碑自審、正常commit/push及GitHub固定SHA原件讀回。沒有人工操作需求、不預設再轉Work。

1101 UNKNOWN／拒算、70拒算／2不足／其中8換股影響未支援／合格真實總淨0、來源0.10全部parents、正式action_resolution0.4、圖形／人工契約及原未支援帳務保持。R2/F、來源認證、完整分叉／複雜身份合併不擴張。Astra與第一工作區救援原件仍未取得未讀，不推定890檔。沒有新來源、私人文件、bootstrap、UI／Android、樣本外、部署／交易／付費／訊息。
