# 獨立action_ledger.replay數值環境驗收0.1

僅合成診斷，不是市場績效、來源認證或策略批准。基線43bc493fa592ced26202116b22337d66183313f1；既有ledger schema rotation-action-ledger/0.1與Journal schema保持。

先凍結原engineered-input、engineered-examples三份input/result、既有五控制與preset、source指紋及expected，才執行before。正常、ROUND_UP、ROUND_DOWN、Inexact、窄指數五控制只用原現金分配案例；配股、減資及兩個明示UNKNOWN變體限normal/preset。已保存的合成VERIFIED聲明原樣保留，不升真實來源資格。

預期：所有合法原input全文相同原保存result，拒算變體仍拒算；caller Context含flags與DefaultContext不變，input不變。修前如非重現，保存反證，不修改oracle；如重現，只固定完整公開replay的50位標準Context，不改qualify、_replay、compare或帳務公式。

獨立CLI RUN經action_cli.main與原Journal；此診斷明示在嵌入呼叫前設定Decimal Context，不宣稱一般全新shell會自行繼承Python Decimal環境。READ新舊record不載入引擎、不重算、不寫檔。只一次既有capital continuation simulate作共享依賴必要回歸，完整比較原帳、權利、reserve、fills、前身及tokens，無新策略或批次。

先存input/expected/source，before/after分開exclusive寫入；舊結果READ不遷移。純數值API不得寫檔/網路/呼叫子程序，測試本身的保存與CLI明示IO分開。不同控制、子程序、歷史PASS均不當新增測試方法累加。

不修compare/獨立checkpoint/舊trend等其他入口，不重跑舊suite、真實producer、資格重算、九路徑或市場方案，不補新行情來源。1101期初cash_claims UNKNOWN及70拒算/2不足/其中8換股未支援/真實總淨合格0保持；正式資格false、主壓力null、所有parents與未支援能力保持。
