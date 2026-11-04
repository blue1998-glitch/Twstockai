# M-ORACLE-DEPLOY2｜真正條件式建機

已實作真實OCI CLI create／launch後段，不再永久拒絕。**本Codex未登入本人Oracle，尚未實際建立／驗證主機、guest健康、私人HTTPS或Android。**13項新定向測試涵蓋成功命令路徑、七類資源、無證據零寫入、竄改／過期／配額／錯區拒絕、重送零建立、未知結果不重送、事後以精確tag核對、guest固定包及盤點缺is-accessible欄位不跳過。

inspect／plan只用list/get。逐區隔實查Compute／Boot／Block，不再用缺少is-accessible=true跳過全批；任何實際讀取失敗保留未知拒絕。只選官方Ubuntu22.04映像，另查image-shape compatibility。公開固定合成ZIP沿5789d9d、345616B／0c48c1d92a94cfcfc1a88f52c22c97cda0d9f0797a05d0367a32ca1fc4a6e750，原UI不改。

## 費用證據如何成立

不是API自動保證免費，也沒有--force。plan完整私有快照綁帳戶／Home Region／全部已發現區隔／AD／實際資源／配額／影像與候選配置；服務API讀不到或範圍不完整即停。50GB新boot＋既有boot/block不得超200GB，VPUs固定10。Compute官方quota names逐一核available，另核VCN與AD block-storage服務餘量；不足或未知拒絕。只有ALWAYS_FREE或LIMITED_FREE官方候選可列計畫，LIMITED_FREE本身不認證免費。

review要求本人在控制台核對帳戶、Compute、儲存、映像、網路五類原件PNG/JPEG/PDF並明確確認，不收文字勾選假文件。來源文件與SHA／時間／原件bytes及人工觀察綁此計畫，0700/0600只留本人Cloud Shell。**這是本人視讀證據，工具不具OCR／Oracle簽章真偽認證，不能宣稱API驗證全部成本。**只有真的能核明總配置零費用才確認；看不到／不確定必須停止。帳戶Free Tier、Always Free授權、現有用量、服務quota、實體供應、試用贈額分開；不得以試用／零帳單取代。

apply驗HMAC／期限／證據原件未改、重新取得官方快照與quota、確認無其他人改資源，才呼叫非持久的ComputeCapacityReport診斷POST。這不是主機建立，單獨記為供應查詢；inspect／plan仍不發create。A1缺quota／容量才試計畫中已核的E2 Micro，沒有付費替代；全無供應就0實體資源。容量報告不保證之後launch仍可成功，競爭失敗保留未知，不盲重送。

## 成功路徑與恢復

獨立compartment→VCN→IGW→route table→自訂空入站security list→subnet→VM；所有資源綁不可混用的plan tag。VM只有公網出站HTTPS／DNS，服務只在127.0.0.1:8786，不能以公網IP看網站；未使用VCN預設security list，不得手動掛回VM。未建立NAT、LB、付費映像、Vault、額外Volume或排程。

每步STARTED先fsync，再發具有確定retry token的建立；未知結果不重發。讀回精確tag找到唯一既有資源才承接；同名無tag不借用，多個同tag拒絕。DONE逐一核身份與security空入站後重送不新增；complete不等guest健康。中斷保留進度／私有認證可續行，外來資源或配額改變即停。過期review需重新提供原件核對，plan不另開已在建立的第二組資源。status／stop不因plan過期失效；stop只對本計畫tag／帳戶相符的VM SOFTSTOP，磁碟與其他人資源保留。部分失敗／未知無法自動安全消除時明確停，不聲稱任意故障都能自動恢復。

guest以cloud-init下載並完整核原ZIP／CRC／manifest／路徑／全成員SHA後才解包，啟原owner scrypt認證服務，systemd以pilot帳戶、256M記憶體上限執行。CloudShell本人getpass設定owner與獨立VM序列登入密碼，只保存雜湊，不傳聊天或寫Git。guest健康未驗必須另外實測，RUNNING不能代網站正常。

## 私人HTTPS與實機邊界

connect會停止並要求本人先確認Tailscale Personal免費用途與同意／登入，不代接受第三方條款。按CONSOLE_GUIDE開獨立VM序列主控台，核guest健康後才做私人Serve；禁止Funnel、匿名網站、開放公網8786／443或關登入。直到實際私人TLS、未授權裝置拒絕及Android本人操作成功前，不輸出推測網址或完成旗標。

[控制台證據及最少操作](CONSOLE_GUIDE.md)。本輪沒有搬FM3、改原owner8765／原Cloud、source0.10／parents／策略／交易或重跑全市場。原13方法全是假transport／合成證據，只證工程，不是Oracle已建。完整實作來源在本目錄，固定包在deliveries/m1-oracle-deploy2-20261104；GitHub讀回另存。
