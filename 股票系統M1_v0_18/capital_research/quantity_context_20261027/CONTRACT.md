# quantity_replay數值環境隔離驗證與有限修復0.1

基線ea33452d9cc15c626b87748444a4b6377e3d84a3；只處理quantity_replay公開入口繼承呼叫端Decimal設定的疑點。先凍結精確輸入、預期、版本與原碼，實際重現後才最小修復；不能重現則留反證，不改oracle。不是新策略／帳務／READ或並列功能。

## 明示研究輸入與預期

兩份新合成請求以既有partial-then-independent與old-trigger-blocked的精確input為素材，只改各輪decision_template.parameter_source及run_policy.parameter_source以標明本次工程診斷；不改任何數量、單、價格、來源／基底、權利、時間、日曆或資格。不改寫舊input／actual，不以目前source重跑後冒稱舊版結果。

主要案例沿同一原帳兩輪：A部分賣20、B部分買7，後續新獨立觸發買B1；期初待交A10及現金權利80仍沿原帳處理一次。預期原始資本2230、一般reserve100，首輪A80/B7/C2、現金1056.660；終點A90/B8/C2、現金1115.640、應計2225.640。原帳、未成交／取消、fills、latest、全部token與完整來源身分保持，無新比例或成交假設。

先以本次source在明示標準環境產生新的正常控制actual；其經濟欄位須符合原獨立已知預期。其他呼叫端環境的**完整原始輸出**預期與這份正常控制完全相同，不只終點NAV。保留獨立的normal、ROUND_UP、ROUND_DOWN、Inexact trap與狹窄Emin/Emax五組；相符者不冒稱缺陷。呼叫端Context與原輸入均不得改動。比較範圍包含來源完整性metadata，因資料本身完全相同；不是更改未來行情的測試。

若重現，只在replay_sequence中建立與原標準環境相同的Context：50位、ROUND_HALF_EVEN、Emin=-999999／Emax=999999、capitals1／clamp0、空flags及標準InvalidOperation／DivisionByZero／Overflow traps。不改任何下游公式、授權、資格或帳務。implementation revision0.1.1，輸入／輸出schema0.1保持；正常原控制的全文／指紋不得改變。其他入口若繞過quantity_replay，數值環境行為不在此輪驗收。

## 證據、必要驗證與保持

before／after另存各環境actual、source版本、例外、input與Context前後指紋；大輸出存新objects/的內容定址原件，同一內容重用而不重複複製或覆寫。修後正常若與修前正常一致，可引用同一原件；source版本仍逐次記錄，不混用版本。

必要驗證只含：前後反例與正常完整結果等價、每輪完整帳／權利／reserve／fills／latest／tokens承接、呼叫端flags／DefaultContext隔離、舊觸發追加仍被閘門拒絕及保存停止前權利、新程序不寫檔或上網。可用cache test double確認外部協調入口沿用，不能冒新實際回放。沒有新增行情、建單或調整觸發；沒有整套舊suite／九路徑／真實producer／來源擷取。

資金／權利／成交部分需集中自審；終點相等本身不足，須核全文、各輪checkpoint與已知權利。既有未來隔離／READ不重算程式未變，沿用原保存證據，不重跑既有相同驗收。1101期初cash_claims UNKNOWN與70／2／其中8／真實總淨合格0、正式false／主壓力null及全部來源parents／圖形／人工契約保持。R2/F、信用、期初應付、外部單、來源認證等原未支援不擴張。不bootstrap、UI／Android／樣本外、部署、交易、付費或訊息。原唯一Codex依里程碑自審、正常commit/push及GitHub固定SHA讀回。
