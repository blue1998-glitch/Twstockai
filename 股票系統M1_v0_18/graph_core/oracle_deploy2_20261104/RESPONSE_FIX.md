# OCI_RESPONSE_INVALID補正

使用者原CloudShell回報固定包已驗但OCI_RESPONSE_INVALID；未取得原回應，根因未知，不能推定權限或空清單。原工具漏保存解析失敗操作與原件，已補精確操作名＋EMPTY_STDOUT／NON_JSON／MISSING_DATA／UNEXPECTED_DATA_TYPE；完整stdout/stderr只存本人私有狀態。空輸出不當零資源，未知仍拒絕。

本輪4唯一方法＝2新＋2直接相關回歸通過，未重跑17全套或合成產品。舊包不改，固定新包見release-response-fix.json；只先plan，不review/apply，不新增Oracle資源。帳戶根因、guest、HTTPS、Android未驗。
