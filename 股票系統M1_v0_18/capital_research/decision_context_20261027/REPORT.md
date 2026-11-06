# 直接決策及續接數值環境：實際結果與自審

## 身分與保存次序

原/workspace/Twstockai、dev/m1-v018-chart-annotations；起始HEAD及遠端均5f18238d6b2d2e1dec87da22d23a5bd3e1ff351a，tracked／index／untracked均0。只原唯一Codex，無代理／worktree／新分支。先存CONTRACT、input／expected／regression-specs、來源版本與完整修前core.py，再直接執行兩公開函式；沒有原回放RUN、simulate、新行情或參數。

精確來源是quantity_context_20261027已保存的完整兩輪結果。第0輪與第1輪execution_job提供全部原呼叫參數；期望decision取各execution.decision_records[decision_id]，metadata按既有return契約取原input.source_integrity_metadata，resume再綁原checkpoint.integrity。這是明示的原件欄位投影，input.json在執行前保存完整wrapper投影指紋，不是執行正常決策後才補預期，也不冒稱原件另外保存過該wrapper。

## 修前及修後actual

| 直接入口 | normal／ROUND_UP／ROUND_DOWN／Inexact修前 | 狹窄Emin/Emax修前 | 五組修後 |
| --- | --- | --- | --- |
| decide，初始決策 | 四組完整相符 | Overflow，無結果 | 五組完整相符 |
| resume_decision，下一輪原帳 | 四組完整相符 | Overflow，無結果 | 五組完整相符 |

本例沒有重現Inexact或捨入差異，不把其他模組過去的缺陷搬成本輪結論。修前resume的Overflow發生在bind_resume→validate_checkpoint／make_checkpoint→原action_ledger核帳，當時inner_decide0、bind_resume1、ledger_replay1，明確早於舊內部localcontext。initial的Overflow發生在inner_decide估值。例外stack、實際呼叫數與當時source指紋逐筆留存。

五個事前宣告的拒絕變體各跑normal及preset，從相同resume輸入只作明示變更：合法但錯前身、checkpoint token刪改、一般reserve刪除、現金權利刪除及缺checkpoint。修前normal均為預期ValueError；preset前四個被Clamped數值例外遮蔽，缺checkpoint仍正確拒絕。這些輸入沒有被接受或成交，不是已證實資格繞過。修後十組均回到原預期ValueError，精確理由、input與caller保持。

完整相符是全decision／layer／continuity／metadata及全部身分相等，不只股數或金額。相同輸出直接精確引用原件欄位投影；若不同則完整內容定址另存，本例沒有不同的成功輸出。before／after與原件版本分開，不覆寫log、oracle或actual。

## 最小修復及機械保全

只改core.py的Decimal import、implementation revision及兩個公開入口local Context。明示prec50、ROUND_HALF_EVEN、Emin=-999999、Emax=999999、capitals1、clamp0、空flags與標準InvalidOperation／DivisionByZero／Overflow traps，不繼承getcontext或DefaultContext。

resume_decision用同一完整Context包住原全部流程；原函式本體原樣移到私有_resume_decision，連舊內層prec=50區塊都保留，不更改前置驗證／same_order_id／tokens合併／fact history／metadata或decision_id公式。自審用AST確認私有helper的簽章及本體精確等於修前公開函式，所有其他邏輯相同。implementation revision0.9.1；decision schema0.8／同單0.9與checkpoint0.7／0.8保持，舊READ不重算或隱式遷移。

## 必要驗收與額外資金複核

六個唯一方法、六次執行首次通過：保存前後與續接中斷位置、原帳及歷史、五個拒絕變體、preset純呼叫、兩個fresh程序、既有候選入口完整相依整合。沒有中間失敗或重跑舊suite；不累加前後控制、子程序或歷史PASS。兩入口×五組前後控制共20次、五項拒絕×兩設定×前後共20次，另兩個preset直接呼叫及兩fresh呼叫；候選整合另一次沿原產生器，不把其內部多次decide當新增測試或獨立樣本。

- 原本金2230與續接當期估值2226.660分開；原現金1056.660、reserve100、A80/B7/C2、現金應收80與待交A10逐欄保留，沒有把權利當已結現金或重開本金。
- 原checkpoint／opening／完整fills／order_states及未成交歷史不變。原r1-A-fill-0與r1-B-fill-1兩筆部分成交仍在，原A剩30、B剩13為EXPIRED_UNFILLED且預留0，沒有復活舊單、掉權利或另造帳。這不是新增全輪帳務回放或只看終點等式。
- 精確latest前身／帳戶與checkpoint ID一致；原9個reviewed token為當期12個reviewed token子集，輸入中的空consumed列表仍沿既有合併機制接續，沒有把有效舊事實強制改成新事件。
- 所有外部資格false、主壓力null，研究推薦與正式授權分開；未新增交易／排名／策略欄位。原候選整合在惡劣preset下全文／身分仍相符原generation，WAIT與各資格狀態不變。
- fresh程序各修改DefaultContext及getcontext，結果仍相符原欄位投影、輸入／caller／DefaultContext皆不變。initial的ledger核對0；resume沿原帳核對2次，simulate／replay_sequence／Journal.save均0，禁止寫檔／網路。不是宣稱所有帳務函式0，也未執行原producer。

## 邊界與分工

只對兩份既有schema0.8決策請求及上述拒絕作定向新驗證，未重跑完整同單schema0.9／C原單矩陣、來源更正／完整分叉或所有數值域。獨立execution.simulate、直接原單重評、allocation.full_transfer、直接checkpoint／action_ledger及舊trend等其餘入口，不因本次core隔離就全面修好；本輪不擴張其實作。

R2/F、信用、期初應付／外部活單、來源認證、自動解除衝突等原未支援保持。1101cash_claims UNKNOWN、70拒算／2不足／其中8換股未支援／真實總淨合格0、正式false／主壓力null、來源0.10全部parents、action_resolution0.4、P0-3／P0-4、reaction_facts及人工基底不變。Astra與救援原件未取得／未讀，不推定歷史890檔存亡。

沒有bootstrap／hydrate、真實producer／資格重算、九路徑、市場六方案、新行情／來源、UI／Android、樣本外、部署、交易、付費或訊息。原唯一Codex沿里程碑自審、正常保存及GitHub固定SHA讀回，無人工操作，不預設Work逐輪工程驗收。Work／使用者仍決定未定策略，本項只證合成機制。

下一項可留Codex，有限確認既有公開EXECUTE／execution.simulate在decide返回後的外層數值環境，先用已保存job／actual反證，不重跑整套回放；有重現才最小修復，否則留反證。不是新策略或新帳務，也不在本輪擴張工程。
