# 本輪失敗、修正及未測

1. 官方文件接件腳本初次匯入requests失敗：本環境無該套件，當時0網路請求／0輸出；改用stdlib urllib，沒有安裝依賴或改環境。見initial-diagnostic。
2. bundle-v01在寫bundle成員前觸發PILOT_BUNDLE_SIZE_LIMIT，未提高上限。原65根合成週期的重複核心證據過大，改用同一既存fixture的40根有界尾段，完整精度保留；snapshot保存原輸入及結果／指標SHA並引用完整原series，不重複大物件。修復前build source及失敗記錄在獨立Git外任務根，舊來源／真實結果不動。
3. 初次15瀏覽器流程PASS後視讀發現固定底部導覽遮住部分圖，未將自動PASS當視覺完成。隔離版將原導覽置於頁首正常流；最終加入不交疊斷言，390／844／1280全部通過並實看PNG，未修改原LITE1。
4. 後續加入獨立包無repo匯入／啟動／owner讀回及script邊界檢查，最終16唯一Python PASS。前14與修正批不累加；瀏覽器只有最終15組作本輪主結果。
5. intake的4為git status折疊untracked目錄條目，非4檔；後用git ls-files --others完整列路徑，扣除本輪兩目錄外仍880原檔。保留此口徑修正，不沿用錯誤檔數。

未發生Oracle建立錯誤：因無正式管理存取，從未送建立請求。Home Region／帳戶／配額、真正HTTPS、ACL、外部未授權拒絕、Oracle重啟、Android實機均未測，不能用本機owner安全測試替代。原Fontconfig／xref／SIGKILL及舊限制沒有在本輪重驗或宣告消除。
