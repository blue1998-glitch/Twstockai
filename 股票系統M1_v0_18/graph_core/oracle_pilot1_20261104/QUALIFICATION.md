# 免費與私人存取資格

狀態：**STOPPED_ACCOUNT_ACCESS_MISSING**。本輪新建Compute／Boot／Block／VCN／IP／VPN／Tailscale帳戶全部0；Oracle帳戶原有資源、帳單與額度UNKNOWN，不宣稱帳戶整體費用為0。

## 已取得的官方公開說明

[Oracle Always Free](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm) HTTP200；[Tailscale Personal](https://tailscale.com/docs/account/manage-plans/free-plans-discounts)與[Serve](https://tailscale.com/docs/features/tailscale-serve) canonical各HTTP200。原kb入口308只記Location，再讀官方canonical，不是受拒繞路；沒有重試任何被禁行情入口。URL／時點／SHA／長度見public-docs兩份JSON；原bytes留Git外。

本次Oracle說明列：Always Free Compute須在Home Region；E2.1.Micro最多兩台，A1首1500 OCPU-hours／9000GB-hours每月（文內2 OCPU總量），Boot＋Block合計200GB。文件同時有47GB／50GB最低開機磁碟的不同段落，實際建立頁須核，不自行選較低值。不沿用舊4 OCPU／24GB傳聞。文件亦有閒置資源回收風險，不能當持久性保證。

1 OCPU／6GB／約50GB只列為待核提案，**不是本帳戶免費資格或容量可用證據**。公開文件不證既有用量、免費餘額、映像、磁碟效能、IP／流量與所有網路組件均免費。任何未知都不得以試用點數、預算警報或允許付費來補足；不得Upgrade／PAYG。

Tailscale公開Personal說明列6免費使用者，Serve限tailnet，Funnel公網。只證一般產品能力，不證本帳戶方案／用途／免費資格／裝置授權或ACL。未登入，無tailnet、無Serve、無實際HTTPS網址。若需新免費帳戶仍須使用者明確同意並親自登入，不代為接受付費條款。

## 取得正式管理存取後才可依序做

1. 先唯讀登入身分、實際Home Region、帳戶型態、現有Compute／Boot／Block／網路及剩餘Always Free額度；保存遮蔽憑證的原始管理回應／畫面與時點。
2. 獨立測試compartment；核建立頁最終整套清單均符合Always Free。最小A1缺容量才評估E2 Micro，不自動試付費機型、不依賴30天贈額；IP、映像、磁碟及網路任何費用不明就停止。
3. 免費資格確證後才建立，不複製原Cloud檔案；只傳固定SHA的公開合成ZIP。獨立資料根、獨立owner憑證、獨立服務；在Oracle驗manifest與單檔SHA後啟原owner服務，綁127.0.0.1:8786。禁止任意document root或直接公網HTTP。
4. 取得既有或使用者同意新建的免費Personal登入；只把Oracle測試機／該Android置入授權tailnet，ACL／grants只給指定owner裝置與443，無廣泛分享、Funnel或入站網站埠。新Oracle上依官方方式裝Tailscale，不在原Codex裝VPN。
5. 用Serve私人HTTPS反向代理至loopback，將實際完整.ts.net主機名加到owner精確Host白名單；保留owner認證。核計畫及免費資格，禁止Funnel。不得將金鑰／登入URL token寫Git／報告。
6. 實際測試TLS、登入、未授權裝置拒絕、無公網匿名工作台、搜尋／圖／日期／比較、資源與重整；成功才公布實際已測私人URL。安全允許才測獨立Oracle重啟，不重啟原Cloud。
7. 使用者本人Android登入該tailnet，開已驗URL、登入owner，回報結果；工程手機尺寸不替代實機。

停止方式：停止**獨立Oracle pilot服務**；於該Oracle停Serve、在tailnet撤銷該測試裝置／權限。Android可Disconnect／登出Tailscale。原Cloud／FM3／8765服務不在停止範圍。目前沒有已建立的Oracle／Tailscale服務要停。

需保存最終資源／免費配額餘量／安全與持久性證據；原真實資料獨立備份及環境重啟能力仍UNKNOWN。本文件是部署接續條件，未執行的項目不得標成已建、免費或安全通過。
