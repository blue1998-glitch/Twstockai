# 明示研究選擇紀錄0.1：交付與驗證

基線c5b966f52eb38715b6871362ef610469f282297e。原唯一Codex、原工作區及原分支依既有功能里程碑授權完成。固定提交以Git／交付回覆為準。

## 實際新增能力

`research_choice.choose_saved`純讀取已保存quantity-after-retry/0.1，核結構／指紋與帳戶、截止、latest、全部歷史token及當期reviewed token，再以共用規則唯一匹配明示候選。外層classification／feasible_for_research與內層結果須一致；不合格不轉選其他候選。

`research_choice_workflow`及SELECT／READ CLI重用未改的rotation_research.store.Journal，沒有另建會計／儲存引擎。SELECT記錄原因、候選快照、source binding及來源版本；READ驗保存紀錄，不重新選擇或呼叫數值引擎。

只把既有quantity_replay._select比對本體抽至quantity_choice_rules，舊wrapper仍傳原quantity解析器；數值／帳務／回放流程與schema不變。新入口另用既有純READ整股字串解析器，不擴張舊回放輸入。舊wrapper的端點、整股格式、錯誤與拒絕語義有直接相容檢查；沒有重跑任何舊回放。

## 事前輸入與實際結果

CONTRACT、intake、cases/*/input與expected在實作前保存。原件採庫內完整JSON引用、長度／SHA及materialized input ID，沒有複製另一份600KB帳務或生成器。兩個結構變體僅測READ拒絕，沒有數值producer。

after-final共18案符合事前預期：4個成功意圖（其中全換僅為條件意圖），14個拒絕。涵蓋指定B1、續抱、退出A留現金、全換端點；舊觸發、UNKNOWN、跨generation同ID、錯帳戶／latest／token、缺理由、未保存股數、端點覆寫、非完整來源、多重匹配、外內資格矛盾、錯紀錄時間與要求自動選最佳。

三份Journal實際原件、SELECT與READ receipts、views另保存。`grid-intent`為A60/B26/C2；`conditional-intent`為A0/B63/C2且WAIT_SETTLEMENT_REASSESSMENT；`rejected-old-trigger`無selected。讀回均等於原after-final choice，不提高資格。原資本1430、當期估值1425.100、現金275.100／一般預留100、歷史12token與當期reviewed15token仍來自原件；新增紀錄不更動它們。

## 本輪必要測試與診斷

7個唯一方法最終通過，實際執行8次：首批7方法中6通過、1失敗，只修正測試監看器後補跑該1方法。不是8個唯一方法，也不加計歷史PASS或18案。

失敗原因是測試監看器把os.fdopen的檔案代號當相對路徑，誤判原Journal的合法寫入。tests.log、test_choice-before-audit-fix.py及diagnostics-audit.json原樣留史；修正為核對該代號實際路徑，仍禁止範圍外寫入。tests-audit-fix.log是相依補驗，不修改oracle／production／已保存actual。

測試覆蓋：全部凍結結果、相同目標ID跨來源拒絕、舊wrapper比對相容、純函式無IO且輸入不變、Journal去重／衝突／故障UNKNOWN／partial保留、READ拒絕竄改且不重選、fresh subprocess的SELECT只寫指定store與READ不寫檔／無引擎import／無網路。部分測試故意注入fsync失敗，不把UNKNOWN冒稱成功。

## 能證與不能證

已證本次合成來源的選擇、拒絕、條件意圖與不可覆寫保存機制。所有選擇的正式flags均false、execution_authorized=false、主壓力null。這裡的指紋是內容一致性，不是來源真偽認證，亦不防止任意自行重簽整套假資料。

沒有新行情、生成器RUN、會計／決策重算、回放、委託或成交；原帳窗口止於1/12。recorded_at為明示合成紀錄時間，不能回填歷史公開時間。等待交割仍須當期新帳／證據及重評；本功能沒有把已保存研究意圖接成可執行單，也沒有驗證此種未授權接線。

Journal沿既有單機／檔案及fsync界線，不宣稱跨程序交易級一致性、目錄持久性或完整稽核服務；partial與IO不明保留現況。完整分叉、來源認證、複雜身份合併、R2/F及原未支援帳務不擴張。

1101期初cash_claims維持UNKNOWN／拒算；70拒算／2不足／其中8換股影響未支援／合格真實總淨0與來源0.10全部parents、正式action_resolution0.4、圖形／人工契約保持。Astra與第一工作區救援原件仍未取得未讀，不重建或推定890檔。沒有真實producer、舊suite、九路徑、資格重算、UI／Android、樣本外、bootstrap、新來源、私人文件、部署交易付費訊息。

## 最小下一步

可留在Codex：先唯讀確認這份選擇紀錄能否被既有純READ摘要使用，提出最小顯示缺口；不接執行、不補1/13行情、不制定交易門檻。這是既有研究資料的可讀性，不需要先做策略研究。
