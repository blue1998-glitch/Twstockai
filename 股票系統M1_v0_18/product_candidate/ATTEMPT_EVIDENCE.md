# 101／106 嘗試與量先價：獨立核心候選 0.1

依 2026-10-17 21:39 使用者圖形裁決實作。`attempt_evidence.py` 是新增、明確呼叫的純 Python 核心，不會被舊 build／viewer／資料庫自動啟用。不是正式選股器，也不是全市場、生命階段或交易績效驗收。

## 已落地的部分

- 呼叫端明確選定近期高點與更左側交易區：示例 101、104～106。越過 101 與越過 106 分開記錄嘗試的**價格條件**，不要求先過 106 才保留 101 的依據。
- 左側區域的最高量取指定來源日的**最大股數量**；不取平均、不換成近期高點的量。缺指定來源日直接拒絕；來源量有 null 則最高量未知，不以可得部分假裝完整最高量。
- 當下累計量／完成日量嚴格大於左側最高量，且已提供前綴中價格尚未越過上緣，才保存 `VOLUME_LEAD_OBSERVED`。沒有量先價也不否定 101 的價格條件。
- 若同一完成日同時有高價過 106、總量過最高量，卻沒有能證明順序的觀察，保存 `VOLUME_EXCESS_ORDER_UNKNOWN`。不從 OHLC 猜量、價先後。
- 盤中越過、完成日收盤越過及後來收盤跌回分別記錄。日後跌回不刪掉先前嘗試／突破；101 和 106 各自呈現，不自動互相取代。
- 等於參照不是嚴格超越，也不是嚴格跌破。使用原精度 Decimal 比較，沒有兩位小數截斷或自行加入連續兩日門檻。
- 每筆 frame／事件有可重現指紋、原觀察及前一 frame 連結；輸出保留原歷史與參照來源。逐前綴重播不改較早 frame／事件 ID。

「量先價可提高往後成功機率」保存為使用者的方向性判讀，並由量先價事件提供證據。**沒有可校準勝率**，`probability_estimate=null`。超越左側區上緣另記實際價格進展，不將量能當作已成功。趨勢延續可形成趨勢強勢股的概念保留；本版尚無正式延續／生命階段分類器。

## 輸入與資訊邊界

API：`evaluate(payload) -> dict`。完整可執行假想例在 `fixtures/attempt_evidence_v01.json`。

| 欄位 | 用途／限制 |
|---|---|
| `schema_version` | 明確為 `attempt-evidence-input/0.1` |
| `context` | series／source ID、Raw 或 Adjusted、共同價格基底 ID、股數單位；Adjusted 還需錨定日 |
| `history` | 第一個觀察前已知的歷史 OHLC、量、日期及 `known_at`；日期唯一遞增 |
| `references` | 明選的參照集合 ID、`known_at`、近期高點來源日、左側範圍及其來源日清單 |
| `observations` | 已有的實際／假想前綴；日期、含時區時間、`is_close`、當日開高低現價、累計股數、價格基底 ID |

近期高點必須符合所指來源日的最高價。左區來源日是呼叫者明選，價格區域必須與這些 K 線交集；此處**沒有自動辨識交易密集區**、量價分布、套牢持有人或壓力強度。

`is_close` 必須明示，不從 13:30 等鐘點推論收盤。盤中資料同日開盤價不變，高點／累計量不倒退、低點不反向收窄；跨日至少需前日完成觀察。資料修正應成為新輸入版本，不能在同一次重播偷偷改舊紀錄。

只接受 `SHARES_REPORTED`，不自動乘一千。不同基底的列、晚於第一個觀察日的 Adjusted 錨定拒絕比較；共同基底、Adjusted 錨定與公司行動完整性仍是**呼叫者宣告**，本模組沒有外部認證／還原工具，不能把宣告升格成已核實。原專案的 Raw 公司行動與 Adjusted 同錨定限制仍有效；將來接入真實資料時必須先經既有來源對齊與公司行動驗證。

歷史可能不是完整市場時間序列，官方日曆、完整歷史覆蓋與真實盤中可得性均未認證。量先價僅指**已提供資料窗口內看見的證據**，不能推論漏掉的日期從未過上緣。若歷史本來就曾過上緣、或先前觀察已見過，後來放量不會被改稱為新量先價。

所有事件 `occurred_at=null`，因快照只證明首次看到，不知道兩次更新間精確穿越時刻。`first_observed_at` 用輸入觀察時間；完成日價格／量的 `confirmed_at` 也是首次看到完成資料的時間。不能回填盤中精確成交時刻。

## 輸出與不可外推的部分

- `attempt_levels[].price_attempt_condition=MET`：只代表已選日線結構中該價格子條件成立，**不是所有必要條件都通過的買入指令**。
- `latest_completed_close_relation`：與當下盤中關係分開，避免盤中已過就寫成收盤已過。
- `volume_lead_evidence_ids`：歷史曾看見的量先價證據。後來價格失敗仍保留，不表示該支持永久有效。
- `CLOSE_RETURNED_BELOW`：價格跌回參照的事實；本模組不自動上移防守、不新增減碼／賣出處置，也不把 106 以下都寫成原 101 失敗。
- `classification_quality=NOT_VALIDATED`、`action_qualification=NOT_EVALUATED`、`trend_strength=NOT_CLASSIFIED`。固定未評估標示不是否認使用者的例圖判讀，而是防止將子條件錯當完整市場交易資格。

未完成：自動選取日線結構／關鍵高點／左區、正式三種整理及生命階段、延續強勢的分類條件、持倉處置與資金比較、即時資料供應、全市場辨識、候選畫面整合、Android 實機、分類及交易價值驗證。

## 重現

在 `股票系統M1_v0_18` 執行，無額外套件、API key 或網頁需求：

```bash
python3 -m unittest discover -s tests -p test_attempt_evidence.py -v
python3 -m unittest discover -s tests -p test_product_candidate.py -v
python3 -m product_candidate.attempt_evidence product_candidate/fixtures/attempt_evidence_v01.json
```

最後一行只把新 JSON 印至標準輸出，不寫入歷史庫。`evaluate` 不讀寫檔案、沒有 Streamlit 或資料庫依賴；命令入口只讀指定輸入。已執行結果與限制見 `validation_attempts_20261017/驗收報告.md`。
