# 保存generation的明示研究選擇紀錄0.1

基線c5b966f52eb38715b6871362ef610469f282297e。只從既有quantity-after-retry/0.1完整保存結果記錄明示研究意圖，不重算generation／會計、不延長原行情窗口、不建單、成交或升正式資格。

## 輸入與重用

純API `research_choice.choose_saved(request)`，schema=`capital-research-choice-input/0.1`，固定synthetic=true、saved_result、source_binding、selection、recorded_at。source_binding綁整份原件、generation、quantity_request、帳戶、checkpoint／state／原ledger／execution、latest accepted decision/account、截止、原帳與決策reviewed tokens、原receipts及來源版本。不能只靠候選ID或同股數；同一目標在舊觸發原件仍可能被拒絕。

保存原件須為GENERATED，內層generation須COMPLETE／enumeration_complete，原selected_id／ranking為null、正式flags全false。重用既有純READ snapshot／指紋檢查，核q request ID、原帳／截止／前身／token與原候選的綁定；不匯入或呼叫數值／ledger引擎，不重新證明來源或任意造假。完整指紋是內容一致性，不是外部來源認證。

原quantity_replay._select的比對本體抽到標準函式庫共用模組，舊wrapper仍傳原quantity解析器，原0.1回放行為／輸出schema不變。新選擇紀錄使用既有READ整股解析器：GRID數量為非負ASCII整股字串；端點股數null。selection仍為mode／sell_A／additional_B／reason；mode限GRID／HOLD／EXIT_A_KEEP_CASH／FULL_TRANSFER，必須唯一匹配原件成員。reason必為非空文字，不預設或fallback。

選中後保留原外層classification及feasible_for_research檢查，並拒絕與內層狀態／理由矛盾的保存宣告。CURRENTLY_FEASIBLE僅記RESEARCH_INTENT；WAIT_SETTLEMENT_REASSESSMENT僅記CONDITIONAL_RESEARCH_INTENT，仍需當期新帳／證據／重評，不視為現在可買。不合格／UNKNOWN／NOT_IMPLEMENTED／不存在／多重匹配均REFUSED，無選中record，不轉選續抱。

recorded_at是明示紀錄時間，含時區且不早於保存decision_at；不回填資料available_at，也不是實際送單／成交／歷史訊號時間。本輪fixture使用明示合成紀錄時間，不宣稱真實操作時刻。

## 保存與READ

輸出choice schema=`capital-research-choice/0.1`，附request_id／record_id、來源綁定、原明示selection、原候選快照與條件分類；ranking=null，正式flags全false、主壓力null、execution_authorized=false。只有新choice紀錄的selected欄能有值，原generation／帳／現金／預留／fills／tokens完全不改。

外部workflow與CLI重用rotation_research.store.Journal的rotation-record/0.1，不另建store／會計或改舊schema。SELECT可保存成功或REFUSED審查紀錄，READ僅讀保存value及校驗record指紋，不再選擇或重算；同ID相同bytes沿Journal去重，不同內容衝突保留原件。既有partial文件不修復、不覆寫；IO失敗保存結果可能UNKNOWN，明確READ核對，不假稱成功。此保存沿原Journal durability／單機界線，不升格為通用交易稽核服務。

## 事前驗收

先凍結來源原件／指紋、精確引用／edits、materialized request ID與expected。正例為保存四格中的新增B1、續抱、退A留現金與原全換條件意圖；反例為舊觸發、UNKNOWN、跨generation同ID借用、錯latest／帳戶／tokens、缺理由／未保存數量／端點覆寫、多重匹配、停止來源、資格欄矛盾及錯紀錄時間。結構變體僅是READ拒絕診斷，不冒新數值producer actual。

必要驗證涵蓋共用比對抽取前後舊wrapper相容、來源／帳／tokens輸入不變、fresh process禁止數值引擎import與網路、Journal保存／READ相同／衝突保留／UNKNOWN、READ不重算。只跑本輪定向集合與直接必要相容檢查，不跑舊suite／回放／真實producer。

原窗口止1/12，這裡不新增1/13行情或擴回放resume。1101期初cash_claims UNKNOWN／拒算、70／2／其中8／真實總淨合格0、正式false／主壓力null、來源0.10／parents、正式action_resolution0.4及圖形／人工契約保持。R2/F、來源認證、原未支援帳務／活單不擴張。無bootstrap、新來源、私人文件、UI／Android、樣本外、部署、交易、付費或訊息；僅原唯一Codex／原工作區／原分支，依里程碑保存讀回。
