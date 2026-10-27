# 全專案進度盤點及數值環境隔離修復

## 本輪直接核對的狀態

GitHub、/workspace/Twstockai的原dev/m1-v018-chart-annotations均從829fd4af25e12f061e49e0c77446ed2ac4528119接續，初始tracked／index／untracked皆0。沒有新分支、worktree或子代理。GitHub正式工具實讀七份固定SHA進度文件並以完整bytes／SHA核等；補讀各主線契約、實作入口及保存報告。這是整體工作進度盤點，不冒稱逐檔閱讀全repo原件／私人教材。

|主線|已存在的可用工程|仍有限制；與本輪關係|
|---|---|---|
|圖形與主圖|圖形研究核心、獨立日K／量／MACD、人工Raw／Adjusted路由、P0-3結構狀態及主圖接線|自動完整帶／主要壓力、正式型態與生命階段及用途認可未完成；不能由助手補規則。Android實機未測，不重開已結清顯示驗收|
|價量證據|reaction_facts、明示段最大量、密集量峰候選|研究峰群／最大量不是正式代表線，不用新量門檻代替策略決定|
|資料與期初權利|來源0.10／全部parents、第58頁月份角色附錄、期初權利缺口檢查器|真實1101期初cash_claims仍UNKNOWN，公開財報不證個人權利；來源資格與拒算不變，不擋獨立合成機制修復|
|儲存與讀回|SQLite／獨立period保存、Journal、明示RUN／READ與中斷界線|原事故根因與真實斷電、完整分叉／多程序exactly-once不因工程測試就已證；不重跑舊可靠性套件|
|資金研究|有限數量候選、明示選擇、C原單重評／受控再評、原帳承接、逐輪回放、全帳戶評估及另存評估|只屬合成機制；無策略勝者、正式交易資格。新工作流程仍沒有將保存意圖直接接成交|
|本輪可獨立修復|既有全帳戶評估受呼叫端Decimal設定影響|與策略觸發、比較期間、金額或分批比例無相依；先重現再有限修復，沒有為續作另造功能|

盤點依據包含根AGENTS／CONTINUE／PROJECT_VISION／GRAPH_CORE_RESUME最新有效節、REQUIREMENTS_TRACE、專案README／CODEX交接，以及graph_core、structure_state、reaction_facts、volume_peak_research、保存契約與資金研究交接／原碼。較舊的未支援敘述與後來已完成的接線分開判讀，不因舊表仍寫待辦而重做。

## 缺陷及實際重現

account_metrics原evaluate_saved用localcontext()且只設prec=50，保留了呼叫端的rounding、traps與Emin/Emax。使用同一份已保存完整合成帳務及同一evaluation_at，先凍結契約、輸入／預期／原件指紋及完整修前source，再執行：

- normal、ROUND_UP：與原正常保存結果完整相同。ROUND_UP在本例未造成差異，不稱重現。
- 另於執行前凍結ROUND_DOWN追加控制：與原正常結果不同，期間成長尾數及evaluation_id不同；不把這個尾數差異宣稱成實際投資績效影響。
- Inexact trap：有效輸入拋出decimal.Inexact，未回傳評估。
- 狹窄Emin/Emax：有效輸入拋出decimal.Overflow，未回傳評估。

before及before/source/account_metrics.py完整保留；input／expected與追加控制未改。這不是策略假說或來源資料不足造成的失敗。

## 最小修復及驗收

只改account_metrics公開評估入口的內部Context，明示50位、ROUND_HALF_EVEN、原標準Emin/Emax、capitals／clamp與標準traps／空flags。不繼承getcontext或DefaultContext，不污染呼叫端。回撤／恢復、費用、權利與帳務公式全部不改。implementation revision0.1.1，schema0.1不變；在原正常環境的完整輸出及evaluation_id與舊保存原件相同，不隱式遷移歷史結果。

修後五組控制全數與原正常結果完整相等，輸入及呼叫端設定皆不變。5個唯一新方法、5次執行首次通過：

1. 保存的修前／修後及控制組逐一核原oracle，不執行修前source第二次。
2. 帶既有flags／traps與低精度／狹窄指數的呼叫端，在禁止純函式IO下成功，呼叫端與輸入保持。
3. 缺淨值的舊結構反例，沿原oracle仍REFUSED、statistics=null，false/null資格不變。
4. 既有evaluated_replay的評估hook沿用修復，原資本2230、reserve100及完整帳／token不變；不執行新回放或保存流程。
5. 新程序刻意修改DefaultContext及getcontext，仍得原正常結果；禁其他引擎、回放、寫檔及網路。

既有READ source未改，沿用原不載入評估／回放的保存證據；本輪沒有重跑其套件。只有新的純評估重現與必要測試，不累加舊8／14／8、前後控制或子程序數。沒有新行情、交易、帳務重播／producer或策略參數。

## 限制及接續分工

本輪只修全帳戶評估，不宣稱其他數值引擎也已隔離所有ambient Context；巨量／極端數值領域不是本輪驗收。原未支援帳務、來源認證、R2/F、自動恢復／完整分叉及正式型態／主要壓力仍未實作／未確認。原70拒算／2不足／其中8換股影響未支援／真實總淨合格0、1101權利UNKNOWN、正式flags false與主壓力null保持。

Work與使用者決定續抱／移轉觸發、共同期間、風險取捨、金額及分批規則。「A整理、B突破回測後再推，移轉可能提高成長且不增加回撤」仍是待驗假說；不因此接自動選擇或成交。這些未定策略沒有阻擋本輪修復，也不要求Work重做工程驗收。

Astra全文與第一工作區救援原件仍未取得／未讀，未猜測890檔存亡。沒有bootstrap、新抓來源、私人文件、UI／Android、樣本外、部署、下單、付費或訊息。只有原唯一Codex／原工作區／原分支，自審後正常保存並GitHub固定SHA逐檔讀回。

下一個Codex可做的有限確認：既有回放入口也有只設prec的localcontext，若另行接續，先定向反證同類呼叫端污染，不重跑原suite；只有實際重現才另存證據及修復。此項不在本輪擴張實作，不預定需要修改。策略研究仍由Work平行推進。使用者目前無人工操作需求。
