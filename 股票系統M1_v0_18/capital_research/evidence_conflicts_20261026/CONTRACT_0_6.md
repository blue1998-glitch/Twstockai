# 遭拒宣告中的限制衝突：研究契約0.6

本輪使用者已明確答覆：授權定向重現、最小修復及必要測試，先不commit/push。基線4339a146d22dd849a6131a8c13f08f2e56145a2f。原0.5保存結果不重算、不修改；新數值結果為capital-decision/0.6、capital-execution/0.6、capital-comparison/0.6，checkpoint為capital-account-checkpoint/0.5。原輸入外殼及來源宣告capital-fact-declarations/0.1不變。

## 失效資訊與遭拒提案分開

原0.5會拒絕改寫accepted root的宣告，但精確原件恢復後可解除該提案的rejected標記。此次修正保護同一宣告內新出現的限制資訊：不能因宣告其他部分遭拒，連帶忘記新限制／衝突。

capital-fact-history/0.2新增restriction_conflicts，以已解析原事實root為key。每筆保存observed_at、原宣告identity、content_id、restriction_fields、可知validity及拒絕原因。只有同股、同kind、同來源、基底及調整版本且已解析至該root者可寫入；未解／錯scope連結不能對另一root施加限制。

新增限制比較包括新可知invalidation、較早valid_until，以及較晚valid_from。比較採visible投影，未來撤銷尚未同時到達發生與可得時間時不納入。限制metadata仍須通過明示same-source validity檢查。這不是認證遭拒宣告為真，也不覆寫accepted root；其狀態是未解衝突。

相關事實出現未解限制衝突時，issues輸出FACT_RESTRICTION_CONFLICT_UNKNOWN。既有新資金資格、提案及standing BUY檢查沿原接線拒絕／取消。恢復舊bytes、更換review／decision_id或有效別名，都不能清除此root衝突。本輪沒有衝突自動解除或來源更正認證介面。

只遭拒value改寫而沒有新增限制，或只是企圖放寬期限、沒有新增限制者，精確且仍有效原件仍可接受當期review，且不增加獨立事件token。真正獨立新事實可由當期review選用；不永久封鎖股票。舊衝突仍留在其原root，不由新事實刪除。

## 合成案例與時間界線

主案例保持原資本2180、一般reserve100、80現金權利、A10股份權利及原始ledger。第一輪A-zero／空委託至1/8 16:00；第二輪1/8 17:00加入遭拒期限放寬與已知撤銷、仍空委託至1/12 16:00；第三輪1/12 17:00恢復舊原件並提議E-partial。第三輪只驗資格及candidate_ids，不造1/13行情、委託或交割。

未來撤銷四個變體明示採較早checkpoint：第一輪1/6 16:00、第二輪1/6 17:00至1/8 16:00、第三輪1/8 17:00，使用原已存在1/9觀察及1/12交割。沒有新增行情、交易日或真實交割規則。保存B取消、較晚公布仍可成交、恰好同時到期及無tape watermark取消的完整execution-input與actual。

每案先以create-only寫入specification、first-input、expected，再逐輪保存完整round2-input、第三輪input，最後才算actual。涉及第三輪成交者另先存execution-input。before綁修前0.5、after-final綁修後0.6；前身按各版本明示產生，經濟輸入與固定oracle相同，不隱式遷移checkpoint。

## 保全與能力界線

baseline_0_5保存36份原source／根文件／manifest／patch及tracked diff。舊0.5 manifest中的source應查封存原件；未變的舊證據仍查原路徑，不要求目前0.6 source等於0.5。原0.5 manifest、before／after／log與所有舊validation不改。

沿原action_ledger入帳；新增歷史不操作現金、股份、權利、fill或reserve。原origin、latest前身、帳戶、全部token及READ不重算規則保持。舊checkpoint不由新引擎默默升版。

本輪13新方法及12必要回歸，最後25唯一方法；修前主單例FAIL在此集合內，不另加1。12個合成案例及額外prefix控制均非獨立市場樣本。有效原件的標準三輪正例只驗決策資格，沒有第三輪成交；B20成交只屬明示早期時序的晚公布反例及所選舊正例回歸。

valid_from較晚分支有保守接線，但本輪沒有該分支的獨立合成案例；完整來源更正、複雜身份合併、任意造假偵測及完整分叉矩陣仍未實作。R2/F及原未支援帳務不擴張。不改正式策略、圖形、P0-3/P0-4、人工模式或來源資格；70／2／其中8／真實總淨合格0、正式資格false、主壓力null保持。無真實producer、樣本外、UI／Android、bootstrap/hydrate、部署、交易或commit/push。
