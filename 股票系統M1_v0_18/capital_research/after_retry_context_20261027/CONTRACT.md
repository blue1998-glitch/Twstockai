# 完成重評至候選外層數值環境驗證0.1

基線3b472ae8575f4f4f6c5acaf504f29d0ded078bdd。只定向確認 quantity_after_retry.generate_after_retry 的公開外層，包含進入 quantity_candidates.generate 前的 checkpoint 核對／原帳導出。先保存精確來源、輸入身分、預期、控制版本與修前 source，再執行修前 actual；實際重現才最小修復，否則保留反證。禁止修改 oracle 迎合推導。

重用 quantity_after_retry_20261027 的 new-independent-trigger、old-trigger、unknown-qualification 三個完整請求與 after-final 原結果，及既有 wrong-latest、tampered-token-history、search-limit 必要拒絕反例。原 cases/input.json 與其來源 bytes／SHA／pointer 共同確定完整輸入，materialized_input_id 再核對實際純 JSON；不新造價格、金額、觸發、期限、來源或參數。expected 及完整正常輸出直接綁舊原件，不手造另一套 oracle。

直接重用 quantity_context_20261027 的五組 contexts 及 preset flags／DefaultContext 控制。三主例在各環境的完整外層輸出及其內部 generation 身分均應與原保存結果相同；輸入與呼叫端設定保持。若舊環境引發 Overflow／Inexact 或結果差異，完整保存其實際例外／內容，不預定所有環境都會重現。

若重現，只固定外層 local Context 為原標準50位、ROUND_HALF_EVEN、Emin=-999999、Emax=999999、capitals1、clamp0、空flags 與 InvalidOperation／DivisionByZero／Overflow traps，範圍必涵蓋完整公開呼叫。implementation revision0.1.1，原 input/output schema0.1保持；不改 quantity_candidates、continuity、action_ledger 或任何數值／帳務／資格公式。舊 READ／schema／原件不重算或隱式遷移。

必要驗收：三主例的完整結果與拒絕理由不變；錯 latest、缺歷史 token、搜尋上限仍拒絕；原帳 opening／完整 fills／權利／reserve／latest／全部 tokens 保持。原資本1430與當期估值1425.100分開，當期A60/B25/C2、現金275.100與一般reserve100，不把待交／未成交狀態改成交易。獨立新觸發可競爭；舊觸發及UNKNOWN不得追加。等待交割仍條件意圖，不建單、成交或選最佳比例。

純呼叫不得新增檔案、網路、retry／回放／simulate 或 Journal.save；既有 checkpoint 證明會重用 action_ledger，不能宣稱所有帳務函式呼叫0。fresh 程序及呼叫端 preset 控制確認 DefaultContext、flags、traps 不受污染。只跑本輪必要方法，舊suite／九路徑／完整20案不重跑；前後控制與歷史PASS不累加成測試。

輸出完全相同時用固定原件 path／bytes／SHA／完整結果指紋精確引用，差異完整內容另存 objects，before／after 分版本，全部舊證據留史。保存自審、manifest、正常commit/push與GitHub固定SHA讀回沿既有里程碑授權；原唯一Codex、原工作區及原分支，無子代理。

1101期初cash_claims UNKNOWN、70／2／其中8／真實總淨合格0、正式false／主壓力null及來源0.10全部parents、action_resolution0.4、P0-3／P0-4與人工基底保持。R2/F、來源認證、信用、期初應付／外部活單等原未支援不擴張。無bootstrap／hydrate、新行情／來源、真實producer、UI／Android、樣本外、部署、交易、付費或訊息。Astra及救援原件仍未取得／未讀。本輪只證合成工程，不證策略或市場績效。
