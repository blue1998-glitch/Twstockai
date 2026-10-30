# C類原單保存結果唯讀並列範例0.1

基線`63a81306b0d181dd47339b3bca01fd6347b94881`。只補既有C原單結果的使用範例與必要READ驗證，不改任何數值／帳務／比較核心、歷史schema或舊結果。不呼叫回放、生成器、真實producer，不補行情、不截短窗口、不改原JSON使條件相同。

## 來源與執行界線

公開入口重用`lifecycle_compare.compare_saved`及stdout-only `lifecycle_compare_read`；版本仍comparison0.1，C原件review0.2／execution0.9／checkpoint0.8，舊E控制仍原版本。範例只保存來源路徑／bytes／SHA和固定Git基線，載入時核對完整原件，不複製或改寫其內容。新的input／expected先凍結，執行後另存comparison actual與文字。

原件必須通過既有摘要及共同條件閘門；共同完整期初帳戶／權利、截止、初始環境／模型及完整外生市場路徑一致才有columns。容量、交易狀態、可得時間、價格、來源／基底及交割沿原閘門，不放寬。不同期末現金／持股／應付是保存結果，不能要求相同或重設本金。

## 六個事前指定範例

1. C原單重評合格，對照當期資格UNKNOWN、原單等待：同起點／市場，可並列。前者原B20成交、後者0成交且活單20；後者並不是「完全未重評」案例，不得改名為無重評控制。
2. 相同當期前綴、未來撤銷尚不可知：可並列，window identity相同而完整來源／execution ID可以不同。只證本對原件，不宣稱任意未來metadata中立。
3. B容量20對7：拒比，不能把市場容量不同當作分批策略效果。
4. B交易狀態OPEN對LIMIT_UP_NO_BUY：拒比，不能把漲停未成交當作較差策略。
5. 保存觀察截止1/9對1/12：拒比，不擅自延伸行情或截短成共同窗口。
6. C原帳資本1430／期初B5，對舊E原帳1330／期初B0：拒比。舊E只是另一合成帳控制，不冒稱同C單，也不重算舊版。

COMPARABLE只表示原比較入口所列的共同明示條件一致；後續review／當期資格宣告可以不同，不等於每一輪完整候選資訊相同或已驗政策因果。這裡沒有同C市場下「完全未重評且完整觀察至1/9」的新回放，缺這種原件就明列缺口，不造一份。

## 驗收與輸出

先保存六案的input引用、expected與全部來源／READ source指紋，才呼叫比較。actual必須符合兩個可並列／四個拒比的預期；拒比columns=[]並保留精確差異路徑。可並列的原單family／scope／remaining／全部token、權利／reserve／latest只投影原結果，沒有新批准、委託或成交。

必要驗證限這六個READ範例、API輸入不變，以及新C原件成功／拒比CLI在fresh process禁止引擎import、寫檔／網路／子程序仍回傳相同保存comparison與正確exit code。原有PASS不累加，不跑舊suite。builder只寫本輪新的證據檔；CLI仍只stdout，使用`python3 -B`避免bytecode寫入。

ranking／selected_label保持null，正式資格全false、主壓力null。六個範例不是六個獨立市場樣本，也不是新增策略績效。來源認證、job→execution通用因果、完整更正／分叉、R2/F與原未支援帳務不擴張。1101期初cash_claims UNKNOWN／拒算、70／2／其中8／真實總淨合格0與全部來源／圖形／人工契約保持。無新來源、私人文件、bootstrap、UI／Android、樣本外、部署、交易、付費或訊息。
