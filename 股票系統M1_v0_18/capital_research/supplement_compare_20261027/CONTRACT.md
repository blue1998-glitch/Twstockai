# 同父補選純READ共同條件並列0.1

基線841ab8cdd9750eb4915f69c5924d7bc8ffae52a6。新增獨立並列API與stdout-only READ CLI；沿原read_supplement逐份完整校驗，再用原欄位差異helper比較完整parent_binding。原選擇、保存、帳務、READ、schema與歷史成果不改；不生成／重選／重新來源verdict／寫檔／評分／建單或成交。

READ manifest明示每欄label、parent_store／parent_id、store／id；不找最新來源。重用既有MAX_ITEMS=8，限2..8欄且標籤唯一、單行，不靜默截斷或抽樣。純API只處理原READ回覆投影及保存指紋，完整檔案校驗由外層reader負責，不把任意自填receipt當來源認證。

每欄須READ_ONLY、request／choice／result均完整READ_ONLY且保存結果簽章／回覆身分一致。只並列一般、條件及選擇遭拒結果；來源核對拒絕、未知／不完整／錯鏈拒比。全體parent id、header／request／result、generation及source_binding（完整帳／截止／latest／token／版本）完全一致才COMPARABLE並提供columns；同父ID但不同內容仍拒絕。差異全數檢查，僅顯示沿原64項診斷上限，不以截斷放行。

比較狀態不等資格；保留各欄outcome、目標、原請求、條件／拒絕狀態、原件估計成本、來源check與紀錄時間。拒絕欄目標null顯未選中、check null顯未執行，沒有成本顯原件未提供，不補零；不得把拒絕對照變合格方案。紀錄時間可不同且逐欄顯示，以原決策／資料截止判定共同環境，不因晚補記宣稱新決策。互斥意圖不加總股數、成本或資金，ranking／selected_label為null，正式flags false、主壓力null。

只證同一保存決策環境的意圖／估計，不是未來市場路徑、政策支配或績效。先凍結原件引用、精確manifest、結構fixture配方／指紋與expected，再實作驗證。案例含一般對條件、加拒絕欄、相同父ID不同內容、部分保存、缺token／錯generation、重複label／超限及紀錄時間不同。fixture僅從原保存JSON明示改寫及重新指紋的READ結構反例，無新生成／帳務或來源認證。

1101 UNKNOWN／拒算、70／2／其中8／合格真實總淨0、原來源／圖形／人工契約與未支援帳務保持。R2/F、來源認證／完整分叉及自動續跑不擴張。無新來源、私人文件、bootstrap、舊suite／producer、UI／Android、樣本外、部署／交易／付費／訊息。原唯一Codex／原工作區／原分支依里程碑有限工程、自審、正常保存及固定SHA讀回。
