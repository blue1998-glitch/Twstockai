# M-MOB1｜可獨立驗證的私人手機研究成品；遠端入口待授權

**工程服務已實作並通過本機驗證，但使用者目前還不能由Android直接開啟。** 沒有已核的安全遠端入口，未部署、未傳送私人行情到外部。唯一最新進度仍是根CONTINUE_IN_WORK_MODE.md。本輪不重做FM3、不重抓、不重算。

## 已實作成品

`graph_core_chart.mobile_private`為獨立標準庫只讀HTTP包裝，直接服務FM3已保存的原HTML與1469分片。原搜尋、K／量／MACD、結構及事件、資料截止及拒用理由原樣重用；不重設UI、不另建引擎或庫。瀏覽器只按選股載入一股，原分片SHA仍驗證。

- 原HTML及每一個分片都需帳號／密碼，不能用難猜網址取代身分。scrypt儲存密碼雜湊，外部owner-only 0600憑證檔；不使用URL密鑰、不將憑證或測試密碼進Git。
- 僅監聽127.0.0.1。**遠端必須另有已授權的私人HTTPS終止與網路身分控管**；此服務本身不提供HTTPS，不可直接轉成公開HTTP／公開port。
- 精確白名單只含原index及1469分片；不服務Journal、raw、認證檔、目錄列表或任意路徑。拒symlink、路徑穿越、異常Host／Origin及寫入方法；GET核SHA／長度，來源改動即409，不補算修復。
- 無跨域許可、no-store、nosniff、no-referrer、禁止框架嵌入；腳本只允許原HTML的精確CSP hash，保留既有必要inline樣式。不接受代理聲稱已登入的header作驗證。
- 錯密碼有限節流。這是私人單使用者研究服務，不宣稱為公開網際網路多租戶平台或完成滲透測試。Basic憑證由瀏覽器管理，不承諾單一按鈕可清除瀏覽器驗證快取；未來由停用憑證／撤銷tailnet存取撤權。

## 實際驗證

7個新合成安全方法全PASS，重跑同方法不加總。真實原成品經登入後HEAD逐路由檢查1470檔（HTML1＋分片1469），未登入HTML／分片均401。沒有再次驗收1986歷史API原件；僅驗本服務可取用範圍、原HTML指紋及必要代表性資料。

40項Chromium手機／桌面檢查，24份下載與既存完整結果一致；代號搜尋、長短史、缺價、同步、縮放、觸控與原資格均保留，外部請求及JS錯誤0。測試使用外部一次性假帳號與隨機測試密碼，完成後停止loopback服務、刪除測試憑證與含密碼設定；沒有把測試帳號當使用者已登入。Chrome模擬不是Android實機。新服務在fresh Python程序匯入時不載入辨識引擎。

[各項狀態](summary.json)、[安全測試](tests-security.log)、[服務驗證](server-acceptance.json)、[手機驗證](browser-verification.json)、[原碼保全](preservation.json)。真實PNG、下載JSON及預覽都Git外，不附公開圖。

## 現有入口／保存實查

原Cloud capabilities空、無具名入站預覽／轉送工具，VPN=false，未有可核既存手機主機／身分；網路unrestricted只指正常對外請求。現有1040監聽埠不是已授權應用入口，未試探或當手機網址。沒有啟用VPN、修改路由或安裝新Tailscale於本executor。

原成品位置仍由 `/workspace/twstockai-local-data/fm3_20261101/runtime/fm3-continuation.json` 的 preview.path 指定。本次只暫時本機實測，**沒有留置永久服務或可點擊的手機URL**。GitHub是程式／非行情證據入口，並非執行頁。

資料目前在overlay。既有Cloud內可讀不等環境重建可恢復；未發現已核的獨立私人持久磁碟／備份服務。因此「原始資料重啟後可恢復」仍未核實，沒有為驗此項而重啟Cloud或刪除唯一副本。本輪不把同overlay的複本說成可靠備份。

## 唯一待核方案（最低新增成本）

**使用者自有、可持續開機的Linux電腦／支援Python的NAS＋Tailscale Personal私人網路＋Serve HTTPS**，沿本服務及原靜態分片。不購買VPS／網域，不開公開Funnel，不另建Web框架或資料庫。

1. 成本：本輪讀回官方Personal價格為USD0，適用個人用途；硬體、磁碟、電費及網路需既有資源，不假設免費。如沒有符合設備，此方案前提未滿足，不自行購買／租用。部署前須再次核價格／使用條件。
2. 資料保護：手機及主機以本人Tailscale身分登入，只允許本人／指定手機存取該主機HTTPS；ACL預設拒絕其他身份。Serve僅tailnet內，不用Funnel。服務另驗owner密碼；不信任URL、來源IP或代理身份header。Tailscale可能提供端對端加密中繼及控制面metadata，不是把行情存入Tailscale雲端；使用與私人資料傳輸均須明示授權。
3. 持久性：原FM3 raw、Journal、檢查點、preview以保留hardlink的加密連線複製到本人持久磁碟；啟用磁碟加密，另有本人掌控的獨立加密備份。容量須容納實際資料與備份。先做指紋核對及隔離還原，再做重啟復原驗收；此前保留原Cloud唯一副本，不能宣稱已恢復保證。
4. 需要核定：指定上述自有主機及儲存位置；允許該主機接收受限資料；允許本人Tailscale／Serve及owner驗證設定與私密HTTPS服務啟動。個人登入／MFA由本人完成，不在聊天索取密碼、token或私鑰。沒有此核定不建立tailnet、上傳資料、安裝正式服務或正式部署。
5. 核定後的Android測試：登入本人私人網路→開啟部署時產生並實核的HTTPS網址→輸入owner驗證→搜尋代號或名稱→看K／量／MACD／事件及截止日→另查一個拒用股票。最後驗未登入／未授權裝置不可讀HTML或分片，再做主機重啟恢復。**這是待部署後步驟，尚未執行。**

[官方方案／安全／Serve文件讀回](deployment-source-review.json)。本輪沒有實際部署或轉移私人行情，沒有預造假的 .ts.net 網址。

## 工程者重現（非要求使用者開終端機）

```bash
# 用另外的私人憑證檔；交互輸入不回顯，不把密碼放參數或URL
python3 -m graph_core_chart.mobile_private --credentials PRIVATE/auth.json --init-user OWNER
# 只有loopback；正式HTTPS與本人tailnet尚需核定，不可當現有手機入口
python3 -m graph_core_chart.mobile_private --preview PRIVATE/market-fm3-v02.html --credentials PRIVATE/auth.json --port 8765
```

本功能里程碑到部署授權邊界停止，交回總監核唯一方案。每日更新／排程未啟動；所有策略、來源、歷史及正式資格不變。下輪若核定，不再重做FM3或研究相同流程，直接在指定主機交付私人手機入口。
