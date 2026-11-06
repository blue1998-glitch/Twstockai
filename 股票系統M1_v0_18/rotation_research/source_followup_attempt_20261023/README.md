# 三份新來源取得嘗試：全部受阻，未建立0.7

本輪接續 `2d2dbf1aeedcc6238a2cfc064170bdbdcc3a7040`，實際遠端頭相同，祖先核對成功。指定完整交接／0.6來源／驗收／回讀已讀；重新bootstrap成功，0補缺、7個差異保留。只有本既有唯一Codex工作處理，沒有另一工作、worktree或子代理。

使用者提供的三個精確新URL各GET一次；本環境均在代理CONNECT階段失敗，錯誤皆為 `URLError: <urlopen error Tunnel connection failed: 403 Forbidden>`。沒有原站HTTP回應、原始PDF／HTML bytes或可用來源SHA；Work所給SHA／大小／內容只是比對線索，不能當本環境原件已取得或已驗。

| 新來源 | 本環境要求時間UTC | 結果 |
| --- | --- | --- |
| 期交所玉山DN復牌公文 | 2026-10-23T07:59:32.733029+00:00 | CONNECT403，無原件 |
| 玉山官方併購完成新聞 | 2026-10-23T07:59:32.733869+00:00 | CONNECT403，無原件 |
| 台泥115年第2季合併財報 | 2026-10-23T07:59:32.735050+00:00 | CONNECT403，無原件 |

精確URL、要求／完成時點、完整錯誤及Work對照值都在 [captures/source-manifest.json](captures/source-manifest.json) 與各meta。三筆captured_at／readback_at為null，沒有把要求時點當捕捉成功；未生造.response／空PDF／HTML。未重試、未跟隨重新導向、未改主機或路徑、未改代理／TLS，也未請求任何先前禁止端點。

## 本輪實際完成

- 最新遠端、祖先、交接閱讀、完整checkout重新bootstrap，以及原追蹤檔雜湊保存核對。
- 3個精確新URL的單次擷取與具體失敗保存；[verification.json](verification.json)明示0可用原件、0新產品測試／資格／每日帳／六方案。
- 透過支援的環境設定工具，只追加www.taifex.com.tw、www.esunfhc.com、media.taiwancement.com三個確切網域至草稿，保留原七custom domains及presets。saved但requires_publish=true，**未套用／未發布／未再請求**。見[network-draft.json](network-draft.json)。這不表示網域已可連線，更不解除本輪拒絕後停止的限制。
- 本接收失敗與交接checkpoint保存同分支，固定提交逐檔GitHub回讀見根 `deliveries/m1-source-followup-attempt-20261023/`。

## 未完成及保留

沒有取得或視讀這三份原件，沒有核Work的三份SHA／頁碼／語義；沒有建立0.7、catalog、來源parser、新成品ZIP或新產品測試。未把摘要寫入正式來源診斷。既有91項與0.6的70拒算／2不足／8換股影響未支援／真正總淨報酬0及daily／journal空，全部只是前輪證據，本輪未重跑。

原0.6及全部parent、原策略引擎、庫、Raw null、舊UNKNOWN、缺價拒算、歷史、頁與舊成品保存；execution_qualified=false、imputed_close／valuation null、historical_signal_eligible=false、primary_pressure_id=null、policy_authorized=false保持。完整行動減資、7/25後權息、2884證交所直接復牌／2025可交易日／未圓整實配／畸零／既有股東換股影響、台泥最後調整及細項、淨分配與九研究起日期初權利仍缺。無新UI／Android，不把一般法律或公司發放當個人淨額。

## 下一輪必要前提

先透過環境設定的支援流程檢閱、儲存並發布草稿，讓必要網路設定真正生效；Codex本輪不自行發布環境。即使設定改變，也需下一輪對本次已拒三URL有新的明確授權才可作新的觀察，不能在本輪自動重試或換路徑。原有禁止端點與三個舊403網域仍照原限制，不因草稿而可重試。不得要求使用者手機下載／上傳這三份來源。

原件真正可取得後才依[待接入的已確認界線](PENDING_SOURCE_BOUNDARIES.md)與最新完整交接作獨立0.7／精確parent0.6、定向實測及交付。這是待辦界線，**不是已核原件、已實作契約或測試通過**。完整[Work唯讀續接](WORK_HANDOFF.md)；不要把原三URL無前提重送當阻礙已解決。
