# 直接execution.simulate外層數值環境定向驗證0.1

基線cef4d09f08d9d0850adb4c03a9eac651146cded3。只確認原公開execution.simulate的完整外層，尤其decide／resume_decision返回之後的預留、成本、成交、風險及原ledger核對；不再修改已修的core。先存精確輸入／預期／原件及修前source，再定向修前actual；重現才最小修復，不能重現則保存反證，不改oracle迎合推導。

直接重用quantity_context_20261027已保存完整結果中的第0輪及第1輪execution_job／execution／checkpoint。輸入保持原job完整bytes語義與指紋，原成交、行情、容量、狀態、時點、交割、原資本、權利、reserve、前身及token均不改；不是重跑原quantity回放producer。初始期末權利未完結不能補齊費用／淨報酬缺欄或改成合格總淨；完整原結果保持null／缺欄與拒算。

沿用既有五組contexts及preset flags／DefaultContext控制，完整execution及result_id必與原保存actual相同，不只終點現金。原首輪A20／B7部分成交，剩A30／B13到期；後輪只有新B1且保留原兩筆fill，現金80與A10權利各到位一次，原本金2230、reserve100、latest及全部token不重設。不產生新策略或新單，不改原成交條件／會計公式。

另先凍結三個直接相關反例：由初始job只將ledger_input.terminal_costs.fee_rate改為0，必拒絕成本模型錯配；只刪原ledger opening.cash_claims，必拒絕開帳權利不一致；由續接job只將previous_decision換為同來源合法但非latest的保存baseline，必拒絕錯前身。normal與preset都不得被接受；actual若被數值例外遮蔽也如實保存，不將例外當成交或策略缺陷。

若重現，只在simulate公開入口明示原標準完整Context：prec50、ROUND_HALF_EVEN、Emin=-999999／Emax=999999、capitals1／clamp0、空flags及InvalidOperation／DivisionByZero／Overflow traps。implementation revision0.9.1，原execution schema0.8／同單0.9保持；_simulate、core、action_ledger、成本／資金／風險／交割／資格與來源公式全不改，舊READ／歷史schema不重算或遷移。

before／after逐筆保存source、caller前後／input指紋、完整差異或固定原件pointer／SHA／result_id、例外stack與呼叫計數。相同完整輸出直接引用原件，差異內容完整另存，不截斷或覆寫舊原件／oracle／actual／log／manifest。

必要驗收僅兩job×五控制、三個拒絕變體×normal／preset、preset純呼叫與兩個fresh程序DefaultContext、原帳／逐輪prefix／權利／交割／預留／費用／latest／token、既有checkpoint接收新結果仍精確等於原保存checkpoint。禁止IO／網路／quantity回放producer／候選生成／Journal.save；simulate及既有原ledger重播本身就是本次有限診斷，不冒稱其呼叫0。只計唯一新方法，不加歷史PASS、前後控制、子程序或市場樣本。

本輪只驗原兩個schema0.8 job，不冒稱完整C原單0.9矩陣、全部入口或市場成效已驗。1101期初cash_claims UNKNOWN、70／2／其中8／真實總淨合格0、正式false／主壓力null、來源0.10全部parents／action_resolution0.4／P0-3／P0-4及人工基底保持。R2/F、信用、期初應付／外部活單、來源認證／完整分叉等原未支援不擴張；Astra與救援原件未取得未讀。

原唯一Codex、原工作區及原分支沿里程碑必要實作、自審、正常commit/push及GitHub固定SHA讀回。無bootstrap／hydrate、真實producer、舊suite／九路徑／市場六方案、新行情來源、UI／Android、樣本外、部署、交易、付費或訊息；未定策略仍由Work及使用者決定，不預設逐輪Work工程驗收。
