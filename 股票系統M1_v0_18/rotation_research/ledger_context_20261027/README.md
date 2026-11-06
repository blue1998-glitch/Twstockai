# 獨立公司行動資金帳RUN：數值環境隔離0.1.1

保存的同一份合成帳，在窄指數環境修前Overflow；嵌入式CLI RUN在既有preset修前Clamped。已只固定公開replay的完整標準50位Context，包含資格檢查；帳務公式、來源、資格、CLI/Journal及schema保持。

- [實際結果與限制](REPORT.md)
- [事先凍結的驗收契約](CONTRACT.md)、[input及既有完整oracle](input.json)、[expected](expected.json)、[控制及其來源](controls.json)
- [修前summary](before/summary.json)、[修後summary](after/summary.json)、[原碼差異](source-diff-from-0_1.patch)
- [本輪6個唯一方法log](tests-final.log)、[單次共享連續帳回歸](after/shared-consumer/actual.json)
- [初始準備診斷](diagnostics/intake-failure.json)、[原件保全](preservation.json)、[逐檔manifest](CHANGE_MANIFEST.json)

修後原現金分配五控制、配股/減資/兩UNKNOWN變體各兩控制共13份API actual符合凍結預期；另外兩份獨立RUN符合原結果，三份READ守衛保留修前正常及修後record。各控制/子程序不當作額外測試方法；6個方法首次全過，不累加歷史PASS。預備階段路徑錯誤留史，該兩次失敗尚未呼叫replay。

這是數值確定性修復。所有資料為明示合成，scenario_net_return不是真實合格總淨績效。1101帳戶權利UNKNOWN與70/2/其中8/真實合格0保持；無人工操作、不必轉Work例行驗收。

本目錄before/after為不可覆寫診斷，不在原路徑重新執行以增加PASS。若有新變更或疑點，另存版本。沒有新缺口就停止同類helper擴張；下一個能力須依有效優先順序確認，未定策略交Work/使用者。
