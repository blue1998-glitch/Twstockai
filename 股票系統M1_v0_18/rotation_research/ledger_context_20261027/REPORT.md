# 獨立action_ledger.replay RUN定向結果

## 能力與最小修復

基線43bc493fa592ced26202116b22337d66183313f1，原工作區/原分支/唯一Codex。原CLI action_cli.main RUN直接呼叫replay，是可獨立使用的既有入口，不經capital已隔離的外層。原replay只在_replay前改prec=50，仍繼承traps/rounding/exponent/clamp；現在公開replay以完整Context(50, HALF_EVEN, Emin=-999999, Emax=999999, capitals=1, clamp=0, flags空, traps=InvalidOperation/DivisionByZero/Overflow)隔離整個資格與計算。

原replay本體原封移入_replay_checked；測試AST比對原args/body與新helper完全相同，除Decimal import、IMPLEMENTATION_REVISION及公開wrapper外，整個module AST相同。qualify、_replay、compare、費用、權利、日終交割與來源邏輯不改。revision=0.1.1-deterministic-decimal-context，schema仍rotation-action-ledger/0.1，既有結果READ不遷移。不是消除所有可能的Decimal錯誤，也不是任意巨大/非法輸入保證可算。

## 先凍結，再取得修前actual

prepare凍結既有engineered-input、三份engineered-examples完整input/result、五控制及preset來源、兩個只將資格聲明改UNKNOWN的合成變體、明示expected、source-before。frozen.json與intake.json綁長度/SHA；任何部分準備重入只接受完全相同內容，不覆寫。

首次準備錯用project-relative info()處理根AGENTS，拋ValueError；緊接的before命令因缺frozen.json停止，沒有數值呼叫。原prepare及診斷留在diagnostics/，run-before.log保留前置失敗；修正根文件指紋路徑、保留已有input/expected bytes後完成準備。真正修前數值證據是run-before-final.log及before/；oracle未改。此準備錯誤不是帳務重現，也不計測試方法。

## 保存actual

|案例/控制|修前|修後|
|---|---|---|
|原現金分配normal/up/down/Inexact四控制|全文相同原result|仍相同|
|原現金分配narrow-exponents|Overflow，valuation初始1000超窄指數|全文相同原result|
|原配股、減資normal|全文相同原result|仍相同|
|原配股、減資preset|Clamped|全文相同原result|
|期初權利UNKNOWN normal/preset|OPENING_ENTITLEMENTS_UNKNOWN拒算|仍拒算|
|淨分配UNKNOWN normal/preset|NET_DISTRIBUTIONS_TAX_FEES_UNKNOWN拒算|仍拒算|
|CLI RUN normal|保存原result|仍保存原result|
|CLI RUN preset|Clamped、save=0、無record|原result、replay=1/save=1|

數值API共13控制，CLI兩控制；都不是獨立市場樣本。caller Context含flags與DefaultContext、input均保持。原現金分配100股，1/6先確認毛100/淨80.0應收，1/9才入現金；初始1000/終值980.0/scenario=-0.02，total_net_return=null。配股及減資的每日股份、待交權利、交付/可交易日、日終現金及journal逐欄比對原result，沒有補零或補未知。

CLI診斷明示使用嵌入main()前設定的Context；不是聲稱一般新shell會自動受另一Python程序影響。Journal保持，修前normal及修後normal/preset共三份READ在獨立子程序封鎖ledger import和寫入/網路後全文相同RUN收據，無引擎呼叫。舊record不用新source重算。

## 必要驗證、自審與保全

tests-final.log：6個唯一方法首次通過，分別核凍結重現/完整結果、權利與拒算、fresh caller與DefaultContext及無IO、CLI RUN/READ、共享continuation consumer、AST最小範圍。不是重跑原44或其餘舊suite；不加歷史PASS、控制數或子程序數。

fresh純API守衛在資格檢查與帳務kernel入口均記錄完整私有Context，未寫檔/網路/子程序；環境和input保留。一次既有capital execution.simulate continuation必要回歸：完整execution相同原保存actual，包含原帳/權利/reserve/fills/latest/tokens及委託歷史；頂層simulate1、內部ledger replay12/qualify13、generate0/replay_sequence0/save0。這是共享依賴回歸，不冒新增完整市場路徑或無引擎READ，不靠終點相等推定中途沒重用現金。

before/after來源分開，after綁最終action_ledger；verification-source-versions.json綁測試/守衛版本。preservation與manifest核原件及本輪檔案，舊manifest仍只對舊snapshot，不要求它等於新source。根有效接續文件與rotation README只前置本輪進度，舊內容完整留史。正常原分支保存，固定SHA與GitHub回讀結果在本輪對話，無封包/解壓重驗。

## 未做、未證與下一步

沒有策略/比例/天數/觸發新規則，不選勝者，不新增委託或行情，不宣稱真實績效。既有合成fixture的VERIFIED聲明原樣保留，非來源真偽認證；正式policy/historical false、actual_realized與主壓力null、total_net_return null保持。

未執行真實producer、資格重算、九路徑、市場六方案、UI/Android/樣本外、舊suite或新來源擷取；不修獨立compare/qualify/checkpoint/舊trend等其他入口，不宣稱全部公開工具已隔離。R2/F、來源認證及原未支援帳務不擴張。1101於2026-01-02期初cash_claims UNKNOWN與70拒算/2不足/其中8換股未支援/真實合格0保持。Astra/救援原件未取得未讀。

本輪已完成指定RUN缺口；沒有新變更或具體疑點就停止同類重複驗收。下一步可留Codex唯讀按既有優先順序確認一項已定義能力，沒有就列相依點停下；未確認的策略取捨仍交Work/使用者，不自訂門檻。無人工操作需求。
