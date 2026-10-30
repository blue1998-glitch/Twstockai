# 已確認 P0-3 結構狀態附層 0.1

這是 `p03-structure-state/0.1`，不是公司行動來源0.11，也不是自動選帶／主要壓力／買賣策略。直接重用原 `reaction_facts.core.evaluate` 的精確 close/high/low、三態及路徑；不改原reaction_facts、graph_core參數、策略、指標、庫或歷史。核對未見同等角色／P0-3狀態實作後才新增此附層，人工模式解析沿原manual_basis，沒有再做第二套路由。

## 確認規則與相等

在明示、已知、同源／基底／版本、有效角色及突破後返回情境下：

|收盤事實|輸出|
|---|---|
|嚴格高於回檔高點|STRENGTHENING／轉強|
|沒有高於回檔高點，也沒有低於原箱下緣|CONSOLIDATING／整理|
|嚴格低於原箱下緣|WEAKENING／轉弱|
|缺角色、尚不可知、角色失效、來源／基底／版本不符、中斷或矛盾|INSUFFICIENT／證據不足／不可判定|

EQUAL另存`equal_boundaries`及原close/high/low關係；等於高點不算突破，等於箱底不算跌破，因此有效情境下仍為整理。淺回檔線可另存來源事實，但不是判弱界線。量、MACD正負與前筆描述比，分列支持／反面／缺證，不會取消已發生的嚴格收盤過線。沒有容忍百分比、確認天數、量倍數、OSC門檻、機率、主壓力或自動進出規則。

## 純數值、來源與時間

`core.evaluate(facts_input, scenario, as_of=...)`無檔案／網路／UI／資料庫IO，無時計依賴；`source.prepare(comparison_data, choice)`是純來源綁定adapter；`cli.py`／`build.py`才做外部IO。price字串使用既有Decimal比較，不受全域精度或JS浮點影響。錯來源輸入明示拒用，不補缺值、不整理或猜日期。

`p03-explicit-roles/0.1`要求PULLBACK_HIGH、ORIGINAL_BOX_FLOOR、ORIGINAL_BOX_UPPER；最後一項只驗最初突破，淺回檔線SHALLOW_OBSERVATION可選。每個角色有reference_id、語義evidence、HUMAN_CONFIRMED／RESEARCH_CANDIDATE／ENGINEERING_FIXTURE資格、原值occurred_at／known_on、角色known_on／valid_from／valid_until／invalidated_on及實際selected_at。原參照同時保留來源K或研究候選ID、source/frame/prefix、價格基底及adjustment_version；角色ID另綁版本。未知選取時點不造歷史已選，來源條件不足就不可判定。

原箱候選的上下緣必同一已保存候選，帶完整原K見證日，不可任意拼兩價或升作HUMAN_CONFIRMED。回檔高點必明選返回階段K成員與全部同最高日，核與原K、已知時點相符；不自動拿最近pivot。**選定返回階段本身是明示語義輸入，不是新自動切段公式**。核心不自動猜開始、結束或完整原箱。錯角色／候選／來源見證／階段時間拒用。

只分析as_of以前的K／MACD。全來源指紋是完整性metadata，數值事實及狀態只取前綴；追加／修改甚至弄壞未來OHLC不會改既有records／events。來源整檔／frame／result ID可因整檔前綴變動而不同，不能冒稱metadata也相同。狀態／事件ID不綁未來行情；最初突破、返回、轉弱與再次轉強都追加保存。日OHLC不推盤中先後。

已知／待核日曆缺口、缺價格或基底中斷自情境來源開始保守使結構不可判定；不沿價或在恢復資料後默認舊參照有效。必須另給有來源的新情境／角色版本，不做自動復活。缺量或MACD只列缺證，不虛構零值或擋已知價格事實。所有歷史公布可得／Raw完整公司行動限制保留。

## 真實案例資格

`examples/retained-case.json`只作**後來明示的研究角色案例**，不是演算法內硬寫日期／股票／答案。使用原1101五年Raw及B88（155筆來源、正式price_bounds仍null）。研究下緣20.25原K為2025-11-19；研究上緣26.95原K為2026-01-27，來源末轉折2026-07-14、確認2026-09-01與真正價位發生日分開。10/12收盤27.00越研究上緣、10/13收26.35返回；此次明示以10/13完成日高26.85作該返回階段的高點研究角色。**首次返回一日不是通用波段切法，也未獲使用者確認為完整回檔或正式原箱**。

依這組條件式參照，10/13整理、10/14轉強、10/15整理、10/16轉強；原突破10/12保留。真實此例沒有轉弱與收盤相等邊界；工程反例另存，絕不補行情湊齊。該研究角色不是原①④或G1/G2正式案例取代，不能因同價26.85借用5/13來源。來源定位、原精度與UI／JSON實際核對見主圖報告。

## 無網頁重現

完整repo先依AGENTS準備，在本專案目錄執行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m structure_state.build --data cross_scale_chart/generated/comparison-data.json --selection structure_state/examples/retained-case.json --as-of 2026-10-16 --output structure_state/output/new-result.json
```

或只用已交付的純輸入（不依賴網頁、原DB或indicator計算）：

```bash
python3 -m structure_state.cli --input facts-input.json --scenario scenario.json --as-of 2026-10-16 --output NEW-result.json
```

CLI以新檔寫入並讀回核等，既有不同輸出拒絕覆寫。不是正式signal store或交易帳，daily／journal／六方案未執行。

## 完成界線

已確認P0-3規則的工程接入不等自動選完整帶、主要壓力、全市場辨識、策略／勝率／換股或資金飛輪完成。人工Raw／Adjusted切換已有manual_basis／manual_basis_chart，不能再列為未實作；Adjusted仍限既有候選資料，缺者拒絕、不退Raw。新頁重用該功能。

正式來源0.10及全部parent、Raw／UNKNOWN、所有歷史成品與Fontconfig／xref警告不改。完整行動／權息、個人權利等缺口仍在，不作本輪P0-3工程無限來源研究前置條件。execution_qualified=false、imputed_close／valuation=null、historical_signal_eligible=false、primary_pressure_id=null、policy_authorized=false。分類品質NOT_VALIDATED／用途NOT_ESTABLISHED／行動與飛輪NOT_EVALUATED；Android NOT_TESTED_NEW_BUILD。全部已拒入口不重試或繞過，不部署付費交易訊息或子代理。
