# M-DU1本輪收尾：工程已驗；真實新交易日BLOCKED

## 實際基準與保全

起始933212b，先核遠端已有f2f96c16，再以fast-forward保留該環境阻塞紀錄。此原工作區 `/workspace/Twstockai` 的Git外FM3根實際存在，原單一補建程序已結束；沒有另一更新者，不啟新Codex／代理／分支。依原bootstrap --hydrate-missing成功，恢復0檔、7個歷史差異原樣保留。舊preflight.json和舊README全文留史，不冒其環境狀態為當前事實。

原core0.2、market_daily、market_finmind、MACD、MA原碼與起始提交逐bytes相同。原FM3 head、最終批、歷史原件與10/30 HTML保持；HTML仍為4,296,767 bytes／SHA256 47d520d3b079d2ccea9e1563a538e5c575ef85b3069da9005aed9ffb5197c222。沒有重抓1986檔、重跑全歷史或移除原件。

## 新增工程與時間／來源契約

- `market_increment.py`是IO協調接點，呼叫原Journal和未改core，不是第二引擎／資料庫。只承接明確FM3或本協調器保存批次；校驗種子完整結果、input/context、股票／市場／Raw基底／股數單位、歷史與原result SHA，拒跨producer不明遷移。
- 六官方整批來源須完整、原件SHA／長度一致、兩市同日、早於台北當日且不是未證週末交易日。此規則不因開市或傍晚取數而放寬。單股無價、零成交、品質錯誤與缺種子分開終態；不沿前價。當整批來源不合格時也保存逐股未套用診斷，來源／參照角色另列。
- 保留原歷史原值、原可知缺日、basis resets、來源context及seed結果指紋。新官方日因跨來源與公司行動完整性未認證，明確分段；MA／MACD及core比較於新段重啟。不能將保留多日K根數當新段已足夠或認證連續帶。舊批次仍可獨立看原結果及ID，新批不回寫它。
- 相同來源重送在RUN層0核心、0新成品寫入。傳入保存capture不發網路；正常新capture只呼叫既有六官方端點各一次，不使用FinMind全歷史API。來源同日修訂必須明示correction_of與reason，另產不可變run／結果／圖；不替換原件。不要把重新擷取當成0網路。
- 原daily.lock序列化，逐股checkpoint指向保存結果；中斷只續未完成股票。checkpoint來源／seed／身分／截止與依存損壞拒用，不藉重算修補。基礎IO失敗停整批；單股品質失敗隔離。
- 結果／歷史先保存讀回，再建立原M-G3 lazy圖及指紋批次目錄、核檔案存在與長度，最後fsync／replace最新指標。驗證、預覽或容量失敗保持前一有效head。發布後若目錄fsync失敗，回COMMITTED_DURABILITY_UNKNOWN，明示head已換且持久性未知，不假稱已回滾；此極端故障路徑未注入。
- `market_preview`沿原renderer、MA／MACD公式及lazy loader，只擴增量來源標籤。每次僅一股series在瀏覽器記憶體。`mobile_private --head`讀不可變目錄並在head改變後刷新白名單，批次與分片同需owner驗證、同源／Host／路徑限制；瀏覽只讀，不補算。保留原 `--preview` 行為。

## 真實來源與逐市場結果

本輪六項官方GET各一次：5完整保存、1 TPEx日線 `IncompleteRead(245353 bytes read, 5000964 more expected)`，沒有重試或替代端點。原capture helper將該項記為SOURCE_FAILURE，未保存不完整回應當作完整原件；未補造HTTP完整header或原件時點。完整原件和收據在原Git外root/raw與captures。TWSE完整回應日期仍10/30；TPEx日期未知，不具可接受共同新交易日。

| 市場 | 11/2參照普通股 | 本批逐股未套用診斷 | 真實新日套用 | 新日多日分析 |
|---|---:|---:|---:|---:|
| TWSE | 1089 | 1089 | 0 | 0 |
| TPEX | 897 | 897 | 0 | 0 |
| 合計 | 1986 | 1986 | 0 | 0 |

這1986是診斷覆蓋，不是新核心處理成功數。未通過整批gate，個股新日品質拒用數**未評估／null**，不填0冒「全部正常」。原1439多日／1469圖是保留的歷史成果；本輪新增可搜尋真實圖0、新日核心呼叫0。單次入口使用已保存真實capture實跑，exit2／BLOCKED，舊head未改，未再取網路。不是11/2實際更新通過。

## 定向驗證與失敗紀錄

27個唯一Python方法＝18新增＋9相關回歸（MOB1安全7、原日協調與MA分段2）。涵蓋同源零重算／零成品寫入、明示修訂、checkpoint中斷續跑、未來不回寫、同日未成熟／兩市日期差、原缺日延續、缺價零量、單股錯誤／缺seed依存隔離、轉板／名冊缺失、不足容量不計算、下載／catalog篡改、舊head保全、服務不重啟讀新head及owner保護。`tests-current.log`為最終唯一方法清單，不累加任何中間批或舊FM3／MOB1 PASS。

初次12方法有1FAIL／2ERROR，原log完整保留：兩個UI批次測例用了真實當日11/2卻期待接受，改用明示測試時鐘11/4，生產時間gate不改；另一個測例故意損壞原件後沿用同目錄導致immutable helper正確拒絕，僅reset合成fixture隔離後續子例，未加產品自動修復。再審查發現需要保留parent.expected_dates及core已知resets，已補原缺日續接測例，沒有用bar聯集偷蓋舊缺口。

Chromium分開記：

- **合成**兩批、四尺寸（1280×900、390×844、844×390、320×800）：28檢查／16完整下載；批次選擇、精確截止、搜尋、lazy單股、K／量／MACD共軸、分段暖機null、縮放／移圖／觸控不改分析日、無橫溢、JSON與保存core／bars／MA／MACD一致。
- **原真實10/30**兩股、手機直橫：6檢查／4完整下載；確認1469描述項仍在，代表股按需載入且core／bars精確相符。只抽查，不冒1469張逐張重新驗收或新日圖。沒有1986原API全量重驗。
- JS錯誤／外部請求0。PNG與下載均Git外，登入一次性憑證測後刪除、loopback服務停止。不是Android實機驗收。

## 保存、持久性及Oracle待接

原根約20GiB；可用約2.8GiB。以已保存結果／歷史metadata、結果加lazy投影保守估算下一全批約17.8GiB需求；只是容量估算，非已實跑新日或精確資源保證。新協調器在任何新核心呼叫前檢查剩餘容量，估算不足即拒絕；不刪舊版本、唯一資料或checkpoint騰空。中斷亦保留完成部分。現有overlay不等獨立持久備份，沒有為驗復原而重啟。

未來單次執行：在原project Python路徑下使用 `python3 -m graph_core.du1_20261102.run_once --root PRIVATE_FM3_RUNTIME`；它由原完成狀態取得seed，不啟FM3補建。亦可沿 `graph_core.daily_update --increment --seed-run ...`。測試或來源修訂可傳保存capture，修訂必須同時明示predecessor與reason。`execution-config.example.json`只是停用設定，沒有scheduler安裝。

Oracle需掛接完整且有容量的私人持久磁碟（含raw、source receipts、Journal、歷史／結果、checkpoint、preview及head），支援flock、exclusive create、fsync與同目錄原子replace；另有獨立加密備份與隔離還原驗收。實際容量依留版與備份政策核算，不保證免費額度足夠。手機需另核私人HTTPS／身分入口。未申請帳戶、未外傳資料、未建主機、未啟日排程或正式手機服務；等使用者明示帳戶完成，再交總監決定部署，當前里程碑不擴張。

## 明確未完成項

工程定向驗證完成；真實新交易日驗證、實際新批圖、全市場新日資源實測未完成。Android固定入口／實機、每日排程、Oracle、獨立持久／重啟還原未完成或未知；不以本機Chromium互認。原來源0.10／全部parents、Raw／公司行動／五年Adjusted／歷史可得／主檔／SQLite未知、私人權利與淨分配缺口維持，正式false／主壓力null、imputed_close／valuation null，不跑每日淨帳／六方案或稱績效成立。

未取得：TPEx本次完整日線、新交易日共同合格來源、獨立持久備份。
未讀：中斷未取得的回應全文；舊Work救援包資格沿歷史，不冒本輪已收。
未實作：正式跨來源／公司行動連續性認證、外部部署與排程（本輪不授權）。
未執行：真實新日全批重分析、帳務／策略／樣本外、重啟。
未測：Android實機、Oracle復原、實際全批新日效能、發布後fsync故障注入。
未讀回：本輪GitHub固定工程逐檔讀回見另存GITHUB_READBACK收據；未涵蓋其他對話或未交付私人備份，不宣稱它們已保存。
