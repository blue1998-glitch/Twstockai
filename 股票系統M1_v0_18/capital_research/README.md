# 最新：研究選擇與明示完整來源純READ核對並列0.1

入口[說明與命令](research_choice_source_20261027/README.md)、[CONTRACT](research_choice_source_20261027/CONTRACT.md)、[來源相符仍遭拒](research_choice_source_20261027/actual/rejected/readable.txt)及[同ID錯來源拒比](research_choice_source_20261027/actual/wrong-source-same-candidate-id/readable.txt)。新check_saved及source_read CLI沿原校驗，完整綁定與唯一快照相符才兩欄。核對狀態與研究資格分開，不重選／改帳或接成交；缺綁定不猜，無快照明示。

12輸入、2 IO診斷及5唯一方法首次通過，不加歷史PASS；actual另存、舊原件／source不改。全部正式false/null與來源拒算保持；工作方式沿根里程碑，不預設Work逐輪驗收。下方原文完整保留。

---

# 最新：研究選擇紀錄純READ文字摘要0.1

入口[白話說明](research_choice_text_20261027/README.md)、[CONTRACT](research_choice_text_20261027/CONTRACT.md)、[一般意圖](research_choice_text_20261027/actual/grid-intent/readable.txt)、[條件意圖](research_choice_text_20261027/actual/conditional-intent/readable.txt)及[拒絕理由](research_choice_text_20261027/actual/rejected-old-trigger/readable.txt)。既有CLI READ新增--format text，預設JSON及退出碼保持；純view沿原讀取／校驗，不重選、改帳或接成交。目標未執行，時間／來源／latest／reviewed tokens照保存值，缺資料不補零。

三份保存原件與六項拒讀診斷、4唯一方法本輪通過；無舊suite／producer，不加歷史PASS。正式false／主壓力null及全部來源／帳務未知保持；工作方式沿根既有里程碑。下方原文完整保留。

---

# 最新：保存候選的明示研究選擇紀錄0.1

入口[白話說明](research_choice_20261027/README.md)、[REPORT](research_choice_20261027/REPORT.md)、[CONTRACT](research_choice_20261027/CONTRACT.md)及[一般意圖](research_choice_20261027/views/grid-intent.json)／[條件意圖](research_choice_20261027/views/conditional-intent.json)／[拒絕原件](research_choice_20261027/journal/rejected-old-trigger.json)。純API research_choice.choose_saved；保存與READ沿原Journal。來源／帳／截止／latest／全部token綁定，必須唯一明示選擇與理由，保留外層資格；相同目標ID不能借用另一generation資格。

18個事前案例符合預期；7唯一方法最終通過，測試監看誤判修正後只補1方法，總執行8次不加歷史。失敗診斷／原測試／oracle留史，after-final綁原production；三份Journal及receipts可READ不重算。等待交割只記條件意圖，不修改原generation、帳、reserve或token，不建單／成交、補行情或選勝者。一般工作方式沿根有效文件；來源UNKNOWN／正式false／主壓力null與原未支援保持。下方原文完整留史。

---

# 最新：0.3結果接回數量候選0.1

入口[quantity_after_retry_20261027/README.md](quantity_after_retry_20261027/README.md)、[完整候選白話表](quantity_after_retry_20261027/views/new-independent-trigger.txt)、[舊觸發拒絕](quantity_after_retry_20261027/views/old-trigger.txt)、[REPORT](quantity_after_retry_20261027/REPORT.md)及[CONTRACT](quantity_after_retry_20261027/CONTRACT.md)。純API quantity_after_retry.generate_after_retry，核0.3完整原件／checkpoint／latest，沿原帳導出account及全部token，再交原數量產生器；無活單／應付、原A可識別且仍正持股才接。不換family、不建單／成交。

after-final20案符合事前預期；6唯一方法通過，換綁最終證據僅補1方法，7次執行不加成7唯一。原A自審反例、首修欄位錯誤及中間source留史；最終actual與views不混舊批。新觸發走完整外層，舊觸發／UNKNOWN不能追加；原資本1430／當期估值1425.100、權利／reserve／latest／歷史token保持，全部正式false/null及來源拒算不變。工作方式沿根既有規則；下方原文完整保留。

---

# 最新：C原單遭拒後再次重評0.1

入口[c_order_retry_20261027/README.md](c_order_retry_20261027/README.md)、[REPORT](c_order_retry_20261027/REPORT.md)、[CONTRACT](c_order_retry_20261027/CONTRACT.md)及[成功白話摘要](c_order_retry_20261027/readback/qualification-restored.txt)。純API conditional_retry.retry_rejected，先核原0.2完整閘門與保存拒評原件，再沿原帳／原單／remaining追加一次當期review；不換family、不增量，新批仍須新獨立觸發。新wrapper0.3只增READ識別，原決策／執行0.9及帳務不改。

17個精確合成input／expected符合結果；7唯一方法首次全通過，補READ schema防線後只重跑2相依方法，不加成9唯一。最終數值actual在initial/與additional/，純READ文字在readback/；新限制於較晚啟動前生效明示未支援，不假裝成交。原帳／權利／reserve／latest／全部token與拒評紀錄保留。全部正式false/null、1101與來源拒算保持，工作方式沿根既有規則。下方原文完整保留。

---

# 最新：C原單保存結果唯讀並列範例0.1

直接讀[c_order_compare_20261026/README.md](c_order_compare_20261026/README.md)、[合格／未知等待主表](c_order_compare_20261026/actual/reviewed-versus-unknown-wait/readable.txt)、[拒比範例](c_order_compare_20261026/actual/capacity-mismatch/readable.txt)、[REPORT](c_order_compare_20261026/REPORT.md)及[CONTRACT](c_order_compare_20261026/CONTRACT.md)。沿既有純READ API／CLI，原source不改、不重跑；共同起點／截止／市場一致才並列，否則columns空。

六個保存原件組合：兩組可並列、四組拒比；共引用七份原件，不是六個獨立市場樣本。主表等待欄是當期資格UNKNOWN遭拒後仍等待，不是無重評控制。4個必要唯一方法通過，不加歷史PASS；原帳／權利／reserve／latest／token與正式false/null保持，不選勝者。工作方式沿根有效入口；下方原文完整保留。

---

# 最新：C類原條件單同單重評0.1

入口[c_order_review_20261026/README.md](c_order_review_20261026/README.md)、[REPORT](c_order_review_20261026/REPORT.md)、[CONTRACT](c_order_review_20261026/CONTRACT.md)及[原單白話摘要](c_order_review_20261026/readback/valid-C-same-order.txt)。原API新增明示input／review0.2處理C原單，綁原trigger／order／remaining，維持C及原token；新批仍須新獨立觸發。數值檢查與帳務沿原機制，新scope決策／execution0.9、checkpoint0.8，舊版不隱式遷移。

最終14案看after-checkpoint-fix，下一批資格對照看new-batch-final；initial／after-final／new-batch是留史中途結果。13唯一方法首批2失敗，修正版本指紋後5相依方法通過，共18次執行不加成18唯一。舊E相容、READ無引擎／寫檔、部分B7保留與撤銷13、原帳／權利／reserve／latest／token有保存證據。全部合成，無新批成交／1/13行情，非策略有效性。原阻塞與正式false/null不變，工作方式沿根既有有效規則。下方原文完整留史。

---

# 最新：保存生命週期摘要唯讀並列0.1

API `lifecycle_compare.compare_saved(request)`及`python3 -B -m capital_research.lifecycle_compare_read 標籤=原件路徑 ...`。入口[REPORT](lifecycle_compare_20261026/REPORT.md)、[CONTRACT](lifecycle_compare_20261026/CONTRACT.md)、[合法並列表](lifecycle_compare_20261026/views-final/wait-versus-reviewed.txt)、[容量不同拒比](lifecycle_compare_20261026/after-final/capacity-mismatch/readable.txt)。期初帳戶／權利、截止、共同模型與完整保存市場路徑相同才並列，不比較期末帳相等、不重算、評分或選勝者。

21個READ規格、11唯一方法通過；只補2顯示相依方法，實際13方法執行不加歷史。after-final JSON與views-final文字綁最終；initial保留。沒有原job／tape、歷史停止帳或市場錯配就拒比。原核心／帳／摘要／來源不改；UNKNOWN、false/null、1101與70／2／其中8／真實總淨合格0保持。下方原文保留。

---

# 最新：原批次生命週期唯讀摘要0.1

純API `lifecycle.summarize_saved(saved)`，CLI `python3 -B -m capital_research.lifecycle_read <保存JSON>`。入口[REPORT](lifecycle_20261026/REPORT.md)、[CONTRACT](lifecycle_20261026/CONTRACT.md)、[白話表](lifecycle_20261026/after-final/partial-pending/readable.txt)。只讀現存JSON，不匯入引擎／重算／下單。原提案一次列共享order；核准原單量、成交、待交割、活單、取消／到期、reserve與重評理由分開。現金權利／latest／token原樣保留；缺交割journal不因日期已到就補結清。

19個最終READ案例、13唯一方法通過；首批12＋最終13是25次方法執行，不加歷史／副本。原producer與source不改不重跑，正式資格false／主壓力null、1101及來源拒算保持。after-final與tests-after-final.log才綁最終source，initial留史。工作方式沿根有效規則；下方原文保留。

---

# 最新：原數量條件單中途重評0.1

API `conditional_quantity_review.reassess_conditional(request)`；入口[REPORT](conditional_quantity_review_20261026/REPORT.md)、[CONTRACT](conditional_quantity_review_20261026/CONTRACT.md)、[最終保存結果](conditional_quantity_review_20261026/after-final/summary.json)。先核原quantity完整外層閘門，再以真實原帳prefix綁當期review，續用同一條件B買單的原remaining，不創新單／新批／比例。被拒宣告與限制、已成交B7及取消13、應付及預留保持；有效舊事實可review。

17個合成案例、16唯一方法本輪實跑通過，不加歷史／中間批。原quantity0.2、replay0.1及core／execution0.8不改，舊READ不重算。C追加單續評、多活單及外部既有單未支援；一般工作方式沿根有效規則，全部來源／資格／UNKNOWN限制保持。下方原文完整保留。

---

# 最新：數量候選受控逐輪回放接線0.1

API `quantity_replay.replay_sequence(request)`；入口[quantity_replay_20261026/REPORT.md](quantity_replay_20261026/REPORT.md)、[CONTRACT.md](quantity_replay_20261026/CONTRACT.md)。由明示合成選擇／orders／tape串接未改的quantity0.2與execution0.8，不產生策略、最佳數量或委託。先核外層閘門，實際回放後才用原checkpoint接下輪帳戶。等待資金仍須新重評；部分成交、過期／取消、原權利及全部token完整承接。

最終18案例、15唯一方法（僅補跑1個強化fixture方法，未重跑其餘）為本輪證據；最終結果在after-final，修前case actual／log及測試斷言留史。同區間原條件單重評未接入，原帳務／活單未支援仍停止，不fallback或自行撤單。一般讀取不執行引擎；工作方式沿根有效入口，不另立規則。下方原成果完整保留。

---

# 最新：同一數量候選功能補齊0.2

沿原`quantity_candidates.generate`接受`capital-quantity-candidates-input/0.2`：明示sell_A／additional_B域，涵蓋A全賣但B僅部分配置；FIRST_ENTRY／ADDITIONAL_BATCH／UNKNOWN分開檢查。首次須原帳階段邊界及當期新資金資格，追加仍須新獨立token，不藉標籤或review重置。既有B買單預留保持，新批次完整承接未支援時NOT_IMPLEMENTED；不撤單或生成委託。0.1 schema行為保留，舊JSON不重算。

入口[quantity_candidates_v02_20261026/REPORT.md](quantity_candidates_v02_20261026/REPORT.md)與[CONTRACT.md](quantity_candidates_v02_20261026/CONTRACT.md)。27新定向案例、14必要方法（含兩個0.1相容案例）屬本輪，不累加歷史。外層classification／feasible_for_research仍為完整閘門；內層core_evaluation不是建單授權。工作方式沿根有效接續文件。下方原0.1交付完整留史。

---

# 最新功能里程碑：分批換股數量候選0.1

入口[quantity_candidates_20261026/REPORT.md](quantity_candidates_20261026/REPORT.md)及[CONTRACT.md](quantity_candidates_20261026/CONTRACT.md)。純API為`quantity_candidates.generate(request)`；原資金框架仍0.8，沿既有decide／resume_decision、allocation.full_transfer及token檢查，不改帳務、資格或歷史。有限完整整股域產生續抱、退A留現金、部分換股及全換端點，分開當期可行／交割後重評／拒絕／未支援；不選比例、不建單／成交。新增B固定family C，依已知本股前綴及獨立token，不能用family或未來原件尾段繞過。

最終結果只讀`after-final/*/actual.json`與summary；`cases/*/actual.json`為修前結果，input／expected皆凍結不改。21個最終合成案例符合oracle，18必要方法PASS，不累加中間批／歷史數字。已按本輪明確功能里程碑授權由原Codex自審及正常保存，固定SHA以Git提交／回覆為準；下方未提交／無保存授權為歷史。一般工作方式沿根AGENTS／CONTINUE，不另立政策。

---

# 遭拒宣告限制衝突0.6（本地未提交）

入口[evidence_conflicts_20261026/REPORT.md](evidence_conflicts_20261026/REPORT.md)／[CONTRACT_0_6.md](evidence_conflicts_20261026/CONTRACT_0_6.md)，完整交接見根M1_CAPITAL_RESEARCH_CONFLICTS_20261026_HANDOFF.md。0.5主三輪資格復活先實跑重現，0.6保留遭拒宣告的新限制衝突UNKNOWN；有效原件及獨立新事實正例保持。25唯一方法＝13新＋12必要回歸PASS，不累加修前單例或歷史結果。原0.5 source對新baseline_0_5封存，舊證據原樣；無commit/push、正式資格或策略成效結論。

---

# 跨輪事實保全0.5（本地未提交）

最新入口[evidence_lineage_20261025/REPORT.md](evidence_lineage_20261025/REPORT.md)／[CONTRACT_0_5.md](evidence_lineage_20261025/CONTRACT_0_5.md)，完整交接見根M1_CAPITAL_RESEARCH_FACT_LINEAGE_20261025_HANDOFF.md。基線4339a146，沒有新commit/push授權；已知失效跨輪不被ID／review洗掉，有效舊事實及真正新事實仍可競爭。最終35唯一方法＝25新＋10必要回歸，不累加舊結果；原帳、正式資格及來源限制保持。以下舊文完整保留。

---

# A/B定向修復0.4

0.3固定保存：`34b5dfa22b77cfe5c85a818e156389d5d0f9a444`。最新研究入口 [repair_ab_20261025/REPORT.md](repair_ab_20261025/REPORT.md)／[CONTRACT_0_4.md](repair_ab_20261025/CONTRACT_0_4.md)，完整交接見根 M1_CAPITAL_RESEARCH_AB_20261025_HANDOFF.md。只修本股證據所有權及未承接活單區間；舊結果原樣READ，0.3歷史指紋對固定快照。單批20唯一方法＝11新＋9必要回歸PASS，不累加舊證據；沒有市場績效或正式資格結論。以下舊文留史。

---

# 當前本地研究修復0.3｜尚未提交

最新入口：[repair_20261025/REPORT.md](repair_20261025/REPORT.md)、[CONTRACT_0_3.md](repair_20261025/CONTRACT_0_3.md)及root `M1_CAPITAL_RESEARCH_REPAIR_20261025_HANDOFF.md`。原0.2全文、source差異與證據保存在新baseline_0_2與原review_20261025，沒有覆寫舊before／after／log。最新遠端／本地基線仍6be4333d，不commit/push。

純數值core／execution 0.3增加每股新資金review及有效期、明示日終可知證據；checkpoint0.2分開origin／latest身份與完整token，保留fill/order／預留；無來源限售解除明確拒絕。趨勢加碼資格不再只顯示標籤。所有入帳仍由原action_ledger。38唯一方法＝33新＋5必要回歸PASS，舊51／46不累加；不證策略績效。

本專案目錄的當前重現入口（只寫新的輸出目錄）：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m capital_research.repair_20261025.verify
PYTHONDONTWRITEBYTECODE=1 python3 -m capital_research.repair_20261025.build --output /tmp/NEW-capital-repair-evidence
```

下方0.2與0.1命令／結果為歷史契約，不能拿新0.3 source重跑後冒舊版重現；歷史原碼見baseline_0_2或固定工程，不能覆蓋現況。READ維持原樣。R2/F、信用、期初應付、外部既有單完整重播、無來源限售解除及市場資格仍不足；Astra Codex仍未取得未讀。

---

# 當前本地研究修復0.2｜尚未提交

2026-10-25最新工程入口：[review_20261025/REPORT.md](review_20261025/REPORT.md)、[0.2契約](review_20261025/CONTRACT_0_2.md)、[樣本外條件](review_20261025/OUT_OF_SAMPLE_PROTOCOL.md)及root `M1_CAPITAL_RESEARCH_REVIEW_20261025_HANDOFF.md`。遠端與本地基線仍為6be4333d；本輪依使用者指令不commit／push，下面0.1段落與46 PASS只作舊工程歷史，不代表當前0.2重跑結果。

目前有逐觀察真實持股／權利／可能買單風險閘門、交割後新決策綁定、共同外生tape身份、原帳檢查點與有限連續追加回放；靜態目標Pareto不再宣稱政策支配。新增趨勢延續研究狀態與九條共同前綴合成路徑、五種數量意圖的逐輪競爭，不是新正式圖形／交易策略。51項本輪實測＝46新增＋5必要回歸，中間批不累加。

本輪精確重現命令（在本專案目錄）：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m capital_research.review_20261025.verify
PYTHONDONTWRITEBYTECODE=1 python3 -m capital_research.review_20261025.build --output /tmp/NEW-capital-review-evidence
```

數值core無IO，外部builder只寫新檔。舊`build_evidence`已明示凍結，防止0.2產生冒稱0.1結果或覆寫舊證據；原0.1完全重現只看固定ea380cf source，不從舊ZIP覆蓋此工作目錄。舊READ仍可用，版本與原bytes不改。R2/F、信用借還款、期初應付、不中斷承接既有委託完整重播及真實樣本外驗證仍未實作。Astra全文仍僅Work已讀證詞，Codex未取得未讀。

---

# 資金決策獨立研究 0.1｜第一階段（歷史保留）

本目錄驗證資訊與資金機制，**不是策略批准、真實績效或正式持倉系統**。全部數值案例都是合成研究。Astra Library 報告全文未取得／未讀；本輪依使用者第一階段完整指令實作，沒有將指令或摘要冒稱全文。

先讀 [CONTRACT.md](CONTRACT.md)、[INVENTORY.md](INVENTORY.md)、[REPORT.md](REPORT.md)。下一輪完整指令在 root `M1_CAPITAL_RESEARCH_PHASE1_HANDOFF.md`。工程固定提交／GitHub讀回在 root `deliveries/m1-capital-research-phase1-20261024/`。

在 `股票系統M1_v0_18` 可無網頁執行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest capital_research.test_mechanisms -v
PYTHONDONTWRITEBYTECODE=1 python3 -m capital_research.build_evidence --output /tmp/NEW-capital-synthetic-artifacts
python3 -m capital_research.cli RUN --input capital_research/validation_20261024/artifacts/input.json --store /tmp/NEW-capital-records --id decision-v1
python3 -m capital_research.cli EXECUTE --input capital_research/validation_20261024/artifacts/execution-input.json --store /tmp/NEW-capital-records --id execution-v1
python3 -m capital_research.cli READ --store /tmp/NEW-capital-records --id execution-v1
```

新 checkout 依最新 AGENTS 準備；上述命令供重現，不代表下輪必須重跑。`build_evidence` 不覆寫不同檔案，CLI 沿用 `rotation_research.store.Journal`。READ不匯入決策或帳務引擎；同ID不同結果拒絕，中斷檔保留。單檔exclusive/fsync限制與舊Journal相同，沒有新增跨檔交易／斷電保證。

`core.decide` 分開三層證據／新資金／移轉，`allocation.full_transfer` 只枚舉成本與風控允許的最大整股數，`execution.simulate` 處理明示委託／撮合觀察並重用既有 `action_ledger.replay`。沒有第二套帳務公式。`resume_decision`／CLI `RUN --prior-id` 帶入先前已看證據身分，避免同一事件再次當新證據。

R1為明示事件／研究預算與風險限制的可行性框架；C／E的數量是外部合成提案，不是演算法找出的最佳比例。R2／F只保留契約，`NOT_IMPLEMENTED`。券商額度只作另列且明示資格的合成可行性情境，既有帳務不支援，所以拒絕數值重播。期初應付及既有待成交的決策預留已支援，其完整帳務重播明確拒絕。

沒有UI、人工模式重製、正式規則／歷史schema變更、真實公司行動producer、六方案市場績效或Android執行。來源0.10及全部parent、原件、null／UNKNOWN與false資格保持。
