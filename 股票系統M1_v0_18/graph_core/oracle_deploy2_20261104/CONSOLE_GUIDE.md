# 本人Cloud Shell／獨立Oracle VM操作

第一段固定指令會安裝已驗工具並唯讀plan；若無API權限、容量資料缺失、服務限額或來源不明就停止，不建資源。不要回傳私有JSON、OCID、IP或憑證。

## review：API不能直接證明的必要項目

在CloudShell私有目錄console-review-private.json核對實際plan。它含帳戶／候選AD／image OCID等私人資料，只能本人看，不貼聊天。檔案上傳用CloudShell Upload，檔名可自行取，無須輸入OCID。

1. 帳戶：控制台Billing & Cost Management→Upgrade and Manage Payment，截Plan Type=Free Tier；若仍Trial，還需證明本配置不使用贈額，不升級。
2. Compute→Create instance先只看建立頁，不按Create：依私有計畫找同一AD、A1 1CPU6GB或E2 Micro預設，確認Always Free eligible、實際免費CPU／記憶體／主機數剩餘量。A1月CPU／RAM使用量也要覆蓋，不以服務quota或本月0帳單替代。兩候選都可能用時，原件必須涵蓋兩者；不能證明就停。
3. Storage→Block Storage→Boot Volumes／Block Volumes，確認整個Home Region各區隔總量、剩餘Always Free至少50GB與10VPU配置不另計費；不是只看一區隔或未掛載磁碟。
4. 建立頁Image核實私有計畫選定官方Canonical Ubuntu22.04同image ID，無Marketplace／授權費。只是名稱Ubuntu不夠。
5. Networking→VCN／Public IP及官方價格資料，核本計畫VCN、IGW、路由、安全清單、子網、短期IPv4與網路流量均零費用；沒有NAT／LB。任何不確定不確認，不能用難猜URL或試用抵扣取代。

把真正頁面PNG/JPEG/PDF原件上傳CloudShell HOME，review逐項讀檔名與本人確認，資料留私有。工具只核原件bytes與本人觀察綁定，不自動判讀圖片語義；不能上傳合成或無關圖片。這些是必要授權證據，不是解除檢查的--force。

apply只在全部檢查成功後才建；會請本人安全輸入owner密碼及新VM序列主控台pilot密碼，各至少16字。都不要貼聊天。CloudShell只管理，不是股票主機。

## guest與Tailscale本人邊界

建立後控制台Compute→Instances，選本計畫twstockai-pilot-instance開頭主機，Resources→Console connection→Launch Cloud Shell connection。這是獨立VM序列主控台，不是原Cloud。用pilot及剛設定的主控台密碼登入。

先在該VM檢查：

```sh
sudo systemctl status twstockai-pilot --no-pager
curl --max-time 10 -I http://127.0.0.1:8786/
```

應為active且未登入回401。若不是，停止，不開公網埠、不關認證；查本VMcloud-init及systemd紀錄，紀錄勿公開。

只有本人同意Tailscale Personal條款、已核本用途免費並親自登入後，才按官方Ubuntu22.04 HTTPS apt簽章方式安裝Tailscale。此工具不代註冊或安裝；不要curl|bash。官方入口 https://tailscale.com/download/linux 。安裝需要的依賴與外連仍須免費／安全，不能為解決apt HTTP失敗放開入站或停TLS。

在獨立VM執行sudo tailscale up，親自開它給的登入連結；連結／token不貼聊天。於Tailscale管理台只允許本人Android裝置到此VM443，不保留default allow-all、不可Funnel或分享其他人。Android安裝Tailscale並登入同一已授權網路。

取得此VM真正DNSName後，將它寫入 /opt/twstockai-pilot/private-host（完整host.ts.net，不能猜網址），sudo systemctl restart twstockai-pilot，然後sudo tailscale serve --bg http://127.0.0.1:8786 。實際讀Serve狀態後在Android開真實HTTPS網址，輸入owner／剛設定的owner密碼；確認合成標記、搜尋／圖形／日期／比較。未經授權的裝置須拒絕，公網不得可直接開網頁。

停止私人存取：在此VM sudo tailscale serve reset，Tailscale管理台撤銷此裝置或Android授權；停止主機則用工具stop，僅SOFTSTOP自己VM且保留磁碟。原Cloud與FM3服務不可停止。未做任何一步，就保留未完成／未知。
