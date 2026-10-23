# 離線橋接包接收檢查：BLOCKED_MISSING_ORIGINAL_BRIDGE_ZIP

本輪為接收阻礙紀錄，沒有建立來源0.6或接入新原件。基準遠端／本地皆為 `7ae4e80ca0fe7e67bc23ff6caaaa6ec129dd45d0`，指定節點及正式0.4 dae1f6e祖先核對成功；全部後續保留。只有本既有Codex工作，未啟動另一寫入工作或子代理。

預期附件 `TWstockai_Offline_Source_Bridge_20261023.zip`，使用者提供的預期SHA256為 `ecc413ca28fce87085666b87b3c3a6d1bf784ef553b32d2198b8bb72bebeedce`。這是預期值，**沒有取得封包bytes、沒有完成實際SHA或成員驗收**。

## 本環境實際可見內容

`/tmp/codex-remote-attachments`及`/mnt/data`皆不存在。以rg --files --hidden --no-ignore查/workspace與/tmp的ZIP檔名，可見91個ZIP，沒有指定檔名。另對可見3MiB以下或名稱含Bridge／bridge者計SHA，沒有匹配；沒有聲稱將全部大型ZIP計SHA。這91個ZIP檔名是本環境搜尋結果，**不是Work所報原研究包91項manifest的核對**。完整路徑、長度、部分SHA及搜尋錯誤見[attachment-scan.json](attachment-scan.json)。

檔案庫 `/workspace/library-files` 只有：

- M1_v0_17_cloud_20261017_01.zip
- M1_v0_17_cloud_20261017_02.zip
- M1_v0_17_cloud_20261017_03.zip
- M1_v0_17_cloud_verified_20261017.zip及其.sha256
- M1_v0_17_handoff_update_20261017.zip

搜尋另遇 `/tmp/codex-daemon-1000: Permission denied (os error 13)`，保留錯誤；未改權限、繞過或宣稱能讀該目錄。這不是橋接包已取得的證據。

## 已做與未做

已讀最新根交接、完整source_diagnostics_20261023指定文件／catalog／metadata／診斷與既有GitHub回讀。重新執行 `python3 codex/bootstrap_m1.py --hydrate-missing` 成功，0補缺、7差異保留，baseline_verified=true；完整log保留。讀完現有catalog及其parent並核對所有既有追蹤檔雜湊保持，未呼叫來源producer改寫輸出。

橋接包的CODEX_HANDOFF、REPORT、bridge-facts、prior_archive_readback、MANIFEST和PDF／API／頁面／script／query meta皆**尚未取得或讀取**。使用者摘要、預期SHA及Work自述91項相符不能取代原始bytes；沒有編造真API回應或以合成資料接入。沒有執行新產品測試、資格窗、每日帳或六方案；舊61項與70拒算／2不足／8換股不支援／合格0只屬既有證據，不是本輪重跑。

沒有官方網路請求，所有禁止入口及三網域403未重試；未套用／發布網路草稿。原0.5、正式0.4／0.3、策略、引擎、庫、Raw null、UNKNOWN歷史、舊頁／成品／證據及main保持；只追加本接收紀錄及入口前綴。保留historical_signal_eligible=false、primary_pressure_id=null、policy_authorized=false；無新UI／Android。

## 必要下一步

將ZIP本體提供到**同一既有Codex對話可讀位置**，並附實際附件路徑或檔案識別資訊。收到後先核整包預期SHA，再離線讀完整CODEX_HANDOFF及MANIFEST、逐件SHA／長度／meta／URL／HTTP／原觀察時點；成功才依完整指令建立精確parent0.5的新來源版本。新讀回時間與原捕捉時間分存，announced_at不倒填。若仍缺附件，不新增空版本或憑摘要接來源。

完整[Work唯讀續接指令](WORK_HANDOFF.md)。本輪GitHub固定回讀見根 `deliveries/m1-offline-bridge-intake-20261023/`。這是阻礙checkpoint，**不是新來源工程或測試交付成功**。
