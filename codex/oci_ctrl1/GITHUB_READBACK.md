# M-OCI-CTRL1 固定部署逐檔原bytes讀回

公開工程ddc1e119cf77bfcfe3d8dceaae10ce566e61f909，12檔固定GET／長度／SHA全部一致。私庫固定commit 13e58a19787e9fb4ec55762a08ad10c930b34358，四部署檔原bytes已核；handler與workflow再次從固定提交讀回一致。workflow .github/workflows/ctrl1.yml active，blob c229a46d562058530afd23109957110018dee9ff。收據另存正常提交避免自指，後續收據讀回存原Cloud Git外。

18唯一新本地fixture方法通過，初批15／中間18不累加；未重跑舊probe／舊測試，未代總監發任何留言。只更新Issue描述作可操作入口，並非PING或成功收據。控制器native runs0、原零費probe仍disabled，私庫run總數仍只有舊probe1。

工程狀態ENABLED_AWAITING_DIRECTOR_PING，不是GPT_TO_GITHUB_RUNNER_CONNECTED。需總監本對話工具親自向private #1發 {"schema":"oci-ctrl/0.1","operation":"ping"}，讀回相符comment/run/固定版本PING_OK及native success後才接受。原生installation／API／身分缺失皆fail-closed，mock不能取代真實驗收。Oracle仍NOT_CONNECTED／0calls，沒有Secrets、Oracle憑證、外部套件／checkout／新主機／費用變更。

原Cloud／工程鎖／dev／512MiB、FM3 metadata90377／owner原碼／公開main／880未追蹤檔完整保留；交總監首測後不擴張其他工作。
