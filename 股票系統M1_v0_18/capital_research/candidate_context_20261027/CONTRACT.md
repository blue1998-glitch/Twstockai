# 獨立數量候選入口數值環境驗證與有限修復0.1

基線9efc3f34ae46df21411ef738a57d61c2fca7a540。只確認quantity_candidates.generate在不經quantity_replay保護時的呼叫端Decimal影響。先存精確來源／輸入／預期、Context與修前source，再定向重現；有actual才最小修復，不能重現則留反證，不改oracle。

## 重用原件及控制

明示從quantity_context_20261027已保存的完整原件，取得initial第0輪與old-trigger第1輪的quantity_request及generation。input.json保存原件path／bytes／SHA、確切round index、request指紋及原generation指紋；不補資料、不更換來源、不改數量、參數、基底、時點、原帳或前身。原五組Context及preset直接讀固定SHA的舊控制檔，不重建另一套情境。

每組獨立直接generate的完整輸出預期與原保存generation相同，不只候選數或股數；呼叫端Context及input保持。initial原件四個候選為續抱A100/B0/C2、部分A50/B20/C2、指定A退出留現金A0/B0/C2及全換A0/B94/C2；前三當期可行、全換等待交割重評，不能標立即可買。原資本2230、一般reserve100、現金及A10待交／80應收權利保持。

old-trigger原件原持股A80/B7/C2、現金1056.660及原權利仍在；新增B8及全換B94的候選均因NO_NEW_INDEPENDENT_TRIGGER拒絕，不能改family、換ID或Context重算而放行。續抱與減A留現金候選仍可存在，不永久封鎖股票。只產生互斥候選，不選勝者、建單或simulate。

另先凍結搜尋上限反例：由initial精確請求只將max_grid_combinations改0；預期REFUSED_SEARCH_LIMIT、候選空、enumeration_complete=false，不補成成功或默默抽樣。

## 若重現的最小修復

只固定公開generate內部local Context為原標準50位／ROUND_HALF_EVEN、Emin=-999999／Emax=999999、capitals1／clamp0、空flags與標準InvalidOperation／DivisionByZero／Overflow traps，不繼承getcontext或DefaultContext。revision0.2.1，原0.1／0.2輸入輸出schema保持；本輪用已保存0.2請求驗證，不冒稱重跑全部舊版測試。

不改候選列舉、可行性、帳務、風險、成本、權利、分批／去重、來源與授權邏輯。正常環境的全文／指紋必與保存原件相同。舊READ不重算、不遷移，舊source指紋屬其歷史版本，不要求目前source相同。

## 證據與驗收

before／after各存actual／例外及source版本；相同完整JSON只內容定址存一次，若與既有generation完全相同則直接綁既有原件的精確pointer／SHA，不重複複製。所有差異原件完整另存，不截斷來通過；不覆寫舊log、actual、manifest或oracle。

必要驗收只含兩份保存請求×五組既有Context、preset caller flags／DefaultContext隔離、候選／拒絕／WAIT保持、原account／continuation／reserve／latest／全部tokens不變、搜尋上限仍拒絕、fresh程序無simulate／Journal.save／寫檔／網路。既有continuity可能重用action_ledger核checkpoint，非新增會計或成交，不能宣稱所有ledger函式呼叫0。

不重跑整套舊suite、舊回放producer、九路徑、市場六方案、UI／Android或樣本外；無新行情／來源、bootstrap或私人文件。1101 cash_claims UNKNOWN、70／2／其中8／真實總淨合格0、正式flags false／主壓力null及來源parents／圖形／人工基底保持。R2/F、信用、期初應付、外部單、來源認證等原未支援不擴張。Work與使用者決定未定策略，這項只由原唯一Codex依里程碑完成、自審、正常保存讀回。
