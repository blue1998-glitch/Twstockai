# Twstockai｜Oracle Cloud Shell安全查核

**[直接複製Cloud Shell指令](CLOUD_SHELL_COMMAND.md)** · [工具包](Twstockai_ORACLE_SHELL1.pyz?raw=true) · [固定校驗](release.json)

本版已交付可執行inspect／plan／status／stop及apply安全拒絕，**成功建機與私人HTTPS後段未實作，整個里程碑為部分交付**。不是只差使用者按apply。

使用者只需登入自己的Oracle控制台→開Cloud Shell→貼上固定指令。全套來源／長度／SHA／CRC／manifest通過才執行；自動使用官方OCI CLI登入，不用填OCID、程式路徑、SHA或憑證。完整帳戶回應只在私有0700/0600目錄，公開摘要不露識別／IP／token。

固定工具工程：`485d8745dc52545675746502a3516e9ea8b9cbaf`；11543 bytes；SHA256 `d9aca0a8f198f4e7f8bcafc3810f0ac8f1cc1dea77e7ca4a14dcd6c1191f08e7`。原pilot ZIP仍345616 bytes／原SHA，不改產品UI。

[工程／已完成與未完成](../../股票系統M1_v0_18/graph_core/oracle_shell1_20261104/README.md) · [bootstrap實測](../../股票系統M1_v0_18/graph_core/oracle_shell1_20261104/bootstrap-verification.json) · [完整接續](../../股票系統M1_v0_18/graph_core/oracle_shell1_20261104/WORK_HANDOFF.md)

已在原Cloud實際下載固定GitHub工具、校驗後啟動；缺Oracle登入時安全停止。重送在禁止下載spy下重用已驗工具，竄改快取在執行前拒絕。這不是本人Cloud Shell真實帳戶資格核對，沒有建立Oracle／HTTPS，也未測Android實機。
