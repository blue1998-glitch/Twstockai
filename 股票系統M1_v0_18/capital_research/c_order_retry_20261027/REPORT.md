# C原單拒評後再次重評：完成報告

開工實核原工作區／原分支，遠端與HEAD均為3fb991255cdba69df97cdd677e5ea53c01122a8a，tracked／index／untracked全0。依本輪明確任務與既有功能里程碑授權，完成有限工程、必要定向驗證、自審及正常保存讀回；不另開代理、工作區或分支。

## 實際新增能力

新純入口`conditional_retry.retry_rejected`接收原0.2輸入、完整保存拒評結果、精確前身、當期review及明示新觀察。它先委派原完整quantity／條件單閘門，重建結果須與保存原件完全相符；核原checkpoint及latest accepted decision／account、全部token和原單狀態，才能再評。這是新的明示合成RUN，不是READ重算或歷史遷移。

原拒評decision不能冒充latest。前身綁document／execution／checkpoint／latest account及完整tokens；不能只換review ID、省略拒評receipt或手填另一份帳。帳戶由原checkpoint導出，目標由當期實股加原remaining取得，family C、原trigger、原order、限價、期限、原資本與其他資產保持。新API沒有數量／family／account／plans輸入欄位，額外欄位拒絕。

原job追加一個review與嚴格在watermark之後的新tape，其餘ledger／opening／calendar／clock／歷史tape／orders／reassessments保持。成交、交割、成本及共同風險仍由原機制處理；新函式不入帳、不另寫風險公式。執行後核所有既有fills、decisions、fact_sources、拒評attempt與token原樣保留；原單數量不變。

唯一原有source變更為lifecycle的明示review0.3／新狀態READ識別；舊schema不能借用新狀態。原core、execution、continuity、order_review、eligibility、fact_lineage、quantity及action_ledger完全不改。新輸出review0.3，決策／執行0.9、checkpoint0.8、scope0.1保持。

## 先存規格，再執行

`CONTRACT.md`、16個精確input／expected與來源／保護source指紋先凍結於`intake.json`，才實作、執行；額外刪除拒評歷史案例先凍結於`history-tamper-intake.json`再單獨執行。沒有改oracle迎合結果，也未覆寫舊source／原件／log。

沿保存UNKNOWN拒評案例：原A100/B5/C2、現金100、reserve100、cash80/A10權利，原資本1430。第一次review在1/8決策、1/9接收後遭拒，原B20仍等待；以保存1/9日終作cutoff，1/9 17:00再次review，明示觀察至原窗口1/12。1/12 tail重用既存合成原件最後三個觀察，歷史prefix未改，無1/13行情。

## 保存actual

| 案例 | 實際結果 |
| --- | --- |
| qualification-restored | 先前REJECTED保留，新增ACCEPTED；有效原B-event原ID重評、新token空，原B20成交一次、總B25。期末A60/B25/C2、現金275.100、應付0、原權利交付完畢、一般reserve100及資本1430保持。 |
| still-unknown | 新review仍拒絕，兩個REJECTED receipt都在；B0成交、remaining20依原1/12 16:00期限到期。未把到款或review本身當批准。 |
| currently-revoked／conflict-retained | 當期撤銷或同ID改寫加限制衝突仍拒絕並取消原單；B0成交，原第一次拒評及新限制保留。 |
| partial-seven | 只買原單7，剩13依原期限到期；A60/B12/C2、現金535.360，無重複權利／成交／資金。 |
| limit-up-no-fill | review可接受但漲停買不到，B0成交，剩20依原期限到期，未假定換股完成。 |
| wrong-predecessor／missing-tokens | 前身帳戶或完整token不符，先拒絕，沒有用新ID重設歷史。 |
| wrong-order／extra-quantity-forbidden／review-id-reused | 不能借單、增加數量、換family或冒用已收到的review ID。 |
| cancelled-no-revival／accepted-order-not-retry | 已取消單不復活；已接受／已成交的結果不能當作這個拒評入口的新前身。 |
| wrong-cutoff／wrong-basis | 非保存watermark、來源／基底錯配拒絕。未建立盤中或跨缺口續接能力。 |
| limit-before-activation-unsupported | 決策當時仍可行，但1/12首次新觀察前限制已生效，明示NOT_IMPLEMENTED；保留舊prefix和新request／decision，沒有後續execution或假定撤單／成交。 |
| tampered-rejected-history | 即使重填表面前身，刪除原拒評attempt仍與原輸入重建結果不符，拒絕。 |

首16案`initial/summary.json`及補充1案`additional/summary.json`皆符合事前預期。partial／漲停尾段與成功案的cutoff decision及舊prefix完全相同，未來行情只改後續實際成交／到期，不改當時數值決策；完整來源ID自然可不同。沒有主張全面未來metadata中立。

`new-batch/`在1/12完成原單及權利後，用同一原帳接出當期候選：另增B1沿舊B-event仍被`NO_NEW_INDEPENDENT_TRIGGER`拒絕，真正新獨立event／formation／bar可行。兩份精確input及expected先保存才執行；只驗資格，未建單或成交，不新增1/13資料。

## 必要測試、自審與限制

本輪實際7個唯一unittest方法首次全通過；自審補上READ新狀態只限0.3的防線後，只重跑2個受影響方法亦通過。合計9次方法執行、7唯一；17個合成案例、2個新批資格對照和歷史PASS不累加。原測試斷言未減少，首次source／測試保存於diagnostics；沒有失敗或需修改oracle的案例。

驗證包含：所有凍結oracle、原帳opening／cash／股份權利／reserve／fills／latest／全部token及拒評歷史、API輸入不變／決定性、未來tail不改cutoff、未支援範圍停止、新批獨立觸發、舊C／E READ逐值相容，以及fresh process阻擋數值引擎import／寫檔／子程序／網路的新0.3 READ。只在本輪明示retry RUN中重建必要原閘門；沒有重跑整套舊suite、舊九路徑或真實producer。

本輪`initial/`綁最終數值source；之後READ防線不影響數值actual，未再執行16案。`readback/`為既存actual純投影，停止前歷史帳明標HISTORICAL_BEFORE_STOP。沒有從單一終點相等推定中途資金安全，另核舊fills／attempt／原job prefix逐項不變及原Ledger journal／權利承接。這仍不是任意來源／job→execution造假的通用認證。

只接一份0.2拒評原件的一次再次重評，未自動循環0.3結果；REPLAYED_RETRY_NOT_ACTIVATED為防禦分支，本輪沒有專用actual，不稱已驗完整時序。新的限制在較晚啟動前生效採明示停止，未擴原引擎延後生效矩陣。多活單、期初應付、無來源限售解除、外部單完整重播、更正／分叉／來源認證、R2/F保持原未支援。

1101期初cash_claims UNKNOWN／拒算、70拒算／2不足／其中8換股影響未支援／真實總淨合格0、正式false、主壓力null及所有來源／圖形／人工契約保持。未跑資格重算、市場六方案、UI／Android或樣本外，無新來源、私人文件、bootstrap、部署、交易、付費或訊息。Astra及第一工作區救援原件仍未取得未讀；不冒Work獨立驗收。本輪沒有需要人工操作的阻塞。

下一步可留在Codex：若使用者指定，再釐清0.3完成後接回既有數量候選入口的最小範圍；只接無活單／無期初應付的受支援checkpoint，不擴帳務或自行選策略。本輪不另啟此工程。
