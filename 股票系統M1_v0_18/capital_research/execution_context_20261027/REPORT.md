# 直接execution.simulate：定向重現、有限修復與自審

## 身分及原件

原/workspace/Twstockai、dev/m1-v018-chart-annotations；起始HEAD及遠端均cef4d09f08d9d0850adb4c03a9eac651146cded3，tracked／index／untracked皆0。只有原唯一Codex，無代理、worktree或競爭分支。

先保存CONTRACT、input／expected／regression-specs、來源指紋及完整修前execution.py，再重用quantity_context_20261027完整保存兩輪內的execution_job／execution／checkpoint。不是重新生成候選或執行原quantity回放producer；全部原行情、容量、狀態、價格、單、日曆、時點、來源、基底與研究參數保持。只有本輪明示直接simulate診斷，不冒稱原歷史版本重跑。

## 修前實際結果

| 原job | 正常 | ROUND_UP | ROUND_DOWN | Inexact控制 | 狹窄指數 |
| --- | --- | --- | --- | --- | --- |
| initial | 完整相符 | 完整相符 | 完整相符 | Inexact，無結果 | Overflow，無結果 |
| continuation | 完整相符 | 完整成功但尾數／身分不同 | 完整相符 | Inexact，無結果 | Overflow，無結果 |

共五組控制相符、一組成功輸出差異、四個例外。續接ROUND_UP只有/ledger/scenario_net_return最後尾數…97758變…97757及/result_id不同，完整差異內容及路徑另存。fills、order_states及每日帳相同，不宣稱現金、持股或投資人實際收益改變；其他相符控制不當缺陷。

四個例外都在修前execution.py:87的state=replay(...)發生，已從原decide／resume_decision返回。initial有decide1／ledger1／risk0；continuation有resume1／ledger3／risk0（含續接原帳核對）。stack指向action_ledger除法／估值，證明core隔離無法保護之後的外層。輸入及caller仍保持，沒有數值錯誤後假定成交。

三個事前凍結拒絕變體：成本模型錯配、ledger期初現金權利刪除、合法但非latest前身。前後normal及preset共各六組，都為原預期ValueError及相同理由，不曾接受或提升資格。

## 最小修復與修後

僅execution.py：Decimal import、implementation revision及simulate的local Context。完整明示prec50、ROUND_HALF_EVEN、Emin=-999999／Emax=999999、capitals1／clamp0、空flags及InvalidOperation／DivisionByZero／Overflow traps，範圍涵蓋整個_simulate。原_simulate本體、core、action_ledger、費用／交割／風險／資格及所有其他engine全不改。revision0.9.1，execution schema0.8／同單0.9保持；舊READ及原schema不重算、隱式遷移或重寫。

修後十組完整原始輸出及result_id均精確等於原保存execution，不只摘要或最終金額。正常環境亦與舊原件全文相同；input／caller／DefaultContext保持。相同內容使用固定來源bytes／SHA／輪次及完整輸出指紋引用，ROUND_UP差異完整內容另存objects，不截斷或覆寫舊actual、oracle、log或manifest。

## 必要驗證及額外資金複核

六唯一方法、六次方法執行首次通過：保存前後與中斷邊界、逐日原帳／成交／權利、三類拒絕、preset純呼叫、兩fresh程序、既有checkpoint相容。無失敗後補跑，也無舊suite；前後控制／子程序／歷史PASS不累加。直接simulate共36次有限診斷（兩job×五組×前後20、三拒絕×兩設定×前後12、preset2、fresh2），不是36項測試或獨立市場樣本；另兩次原checkpoint驗證不新增simulate。

- 原本金2230與一般reserve100保持，不從當期估值重開帳。首輪只有r1-A-fill-0賣A20及r1-B-fill-1買B7；期末A80/B7/C2、現金1056.660、現金應收80與待交A10。A剩30、B剩13仍EXPIRED_UNFILLED／預留0，續接不復活舊單。
- 後輪僅r2-B-fill-2買B1。完整原fills／order_history、逐日ledger及journal均為新結果精確前綴；原origin ledger／common account、latest與全部reviewed token保留。三筆fill ID唯一，沒有重新入帳或另造資金帳。
- A20售款197.800於原1/8交割，B7應付141.140亦於原1/8結清；B1應付21.020於原1/12結清。各筆原journal僅一個匹配的交割紀錄，日期等於原fill.settlement_date，沒有將應收直接視為可用現金。
- 原80現金及A10股份權利各僅一筆1/12到位，delivery與tradable分開；原逐日曲線、risk_observations、現金／股份權利與預留狀態全文保持。終點現金1115.640、A90/B8/C2、應計2225.640、原三筆fill費稅合計4。不以終點等式代替中途prefix／journal／order_state核對。
- 首輪原ledger未完結，沒有end_net_equity或fees_and_tax_on_fills彙總，scenario_net_return為null；仍保持原缺欄／null，不補成0或完整淨績效。後輪也仍為合成情境、total_net_return=null，不能升正式績效。
- 兩個修後結果交給既有make_checkpoint，完整checkpoint均等於原保存原件，原execution不變。只用標準環境驗相容，不冒稱獨立checkpoint入口已全面隔離。
- fresh程序各直接simulate1次，實際ledger核對initial11／continuation12、risk各4；quantity replay_sequence／候選generate／Journal.save均0，禁止寫檔及網路。simulate與原ledger就是本輪明示診斷，不冒其呼叫0；沒有跑原quantity producer。preset與fresh均確認輸入、flags／traps／指數範圍、caller及DefaultContext不變。

## 未擴張、未測與下一步

只測兩份原schema0.8 job及三個直接相關拒絕反例，未重跑完整同單0.9／C原單矩陣、全部分叉／更正矩陣、未來前綴矩陣或所有數值域。原時序／事實歷史／READ接線不改，重用舊證據。獨立C原單重評／再次重評、全換、直接checkpoint／action_ledger及舊trend入口仍不宣稱全面隔離，不能無限逐helper擴張或將靜態疑點當已重現。

1101cash_claims UNKNOWN、70拒算／2不足／其中8換股未支援／真實總淨合格0、正式false／主壓力null、來源0.10全部parents、action_resolution0.4、P0-3／P0-4、reaction_facts及人工基底保持。R2/F、信用、期初應付／外部活單、來源認證、自動解除衝突等原未支援不擴張。Astra與第一工作區救援原件未取得未讀，不猜測890檔存亡。

無bootstrap／hydrate、真實producer／資格重算、舊suite／九路徑／市場六方案、新行情來源、UI／Android、樣本外、部署、下單、付費或訊息。原唯一Codex沿里程碑自審、正常commit/push及GitHub固定SHA讀回，無人工操作，不預設Work逐輪工程驗收；未定策略由Work與使用者決定，本輪只證合成機制。

下一項可留Codex，有限確認C原單重評與一次再評兩個既有公開外層，重用原保存input／actual與控制，先修前證據，有重現才最小修復，否則留反證；不新增批次規則、帳務或資格，不重跑整套C矩陣。本輪不擴張實作。
