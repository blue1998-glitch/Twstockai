# M-PORT1 實際驗收報告

## 真實資料

本原 Cloud 檔案系統實際可讀 Git 外 FM3 根。安全 fast-forward 至基準 `062b542399ab58b70a492b8aeb9b83967ccfc899`，保留 COMP1 等後續成果及歷史「另一檔案系統缺根」紀錄。未啟任何背景 worker、排程或私人服務。原續跑已完成，沒有重新下載或重算股票。必要 bootstrap 成功，restored=0，7 個歷史差異保留，見 `bootstrap.log`。

完整唯讀 SHA 與保存物件核對用時 447.192 秒；觀察時點見 `real-source-verification.json`（UTC 原樣保存，非來源公告時點）。19,596 個檔案路徑、15,147 不同 inode、8,924 Journal；原件 1,986 份。終態：1,439 多日、30 歷史不足、514 品質拒用、3 缺行情；上市參照1,089／上櫃897。1,469 組 result／history／K／完整 core／MA／MACD／chart 指紋與保存內容相符；其餘517保留拒用或無圖。

同輪已雜湊清單再確認完整檔案集合／size／mtime／inode 未變後，補核 20,305 Journal 引用與8,668預覽／capture引用。不是又一次全 SHA 或第二次全數市場驗證。完整逐檔／逐股清單只留 Git 外；公開文件只統計與單一盤點指紋。來源授權、完整歷史日曆、公司行動、當時可得性或辨識品質不因此升格。

實際原 FM3 根的 DU2 sidecar 數為0；本輪不把其他實驗資料根當成正式 FM3。DU2完整依存的恢復能力由9個合成邏輯成品測試，包括讀取不需卻未來接續需要的 anchor 缺失拒絕。

## 工程與演練

新增 `rotation_research/private_portability.py`，重用 Journal、codec 與 interned JSON 純讀取；既有核心、指標、來源、預覽及私人服務原碼不變。程式指紋對照見 `protected-source-verification.json`。新增 CLI inspect／restore／verify 及合成演練入口，沒有外部傳輸或新資料庫。

16個唯一新 unittest 方法最終通過（`tests.log`），涵蓋原件／blob／anchor缺失、損壞、來源改動、版號、錯誤 binding、symlink／Git／穿越、容量、來源鎖、中斷續跑／壞部分檔保留、舊checkpoint／預覽依存、異常hardlink合併、來源完全不可存取時驗證。沒有累計中間批或歷史測試。

保存一次中間失敗：新增 reader SHA 後，容量測試的 mock 過廣，連小型讀者程式的 SHA 都禁止，尚未進到容量拒絕；修正 mock 只禁止昂貴來源資料雜湊，仍要求容量不足時無資料複製／來源雜湊／目的建立。oracle與容量保護未放寬，最終通過。原FAIL見 `tests-intermediate-failure.log`。證據生成腳本首次將 market_preview.py 寫成錯誤目錄，已更正真實路徑再比對；不是產品測試或產品缺陷。

一次合成獨立 CLI 演練3步均exit0：原目錄→新隔離目錄→恢復讀回，23檔／9DU2；全部原bytes與SHA、內部硬連結分組相同，目的inode獨立於來源。單元測試還讓舊合成來源完全不可stat／lstat，恢復讀取仍成功；既有M-MOB1 batch_index可讀新的獨立路徑配方。沒有啟動Web、重算核心或改寫來源；合成69根K／結果只重用已公開合成示範。這些不代表真實市場樣本或 Android 通過。

## 容量與未驗證

原集合邏輯31,157,700,168 bytes，實際allocated20,508,598,272 bytes（約19.10GiB）。保留hardlink後，本機完整隔離副本最低檔案配置＋reserve為20,575,571,968 bytes（約19.16GiB）；當下可用約2.43GiB，詳見容量時點。故未嘗試真實完整複製，沒有刪除／重壓／搬走原件。

**E 真實獨立備份未建立／未驗證；未知是否另有不可見備份。真實新環境、重啟／斷電／遠端FS恢復未測。** 合成本地副本不能替代持久備份。overlay永久性未知，源目錄目前一致只代表本次觀察，不保證未來仍在。

未來 Oracle／私人主機至少需：明確移轉授權、合法私人存取、持久磁碟容量大於完整副本19.16GiB並預留後續DU2增量與獨立備份空間、支援hardlink／POSIX鎖／fsync／atomic rename的檔案系統、固定相容程式版本、私人manifest與完整共享片段、認證／加密／ACL及備份驗證。尚未核實Oracle免費quota與磁碟，不能認定免費容量必然足夠。原件保留至真正隔離復原與備份驗收完成；不得刪唯一副本。工具只提供本機動作，不自行傳出資料。

## 結案狀態

已完成A／B唯讀完整性、C／D工程能力；E及F的外部授權／持久復原未完成。未取得：獨立真實備份或新私人持久磁碟；未讀：不存在於本輪授權可見範圍的備份；未實作：外部傳輸／部署／排程（不在範圍）；未執行：真實19GiB拷貝與股票核心重跑；未測：真實跨環境／重啟／Android；GitHub未讀回狀態以另存固定SHA收據為準。

全部來源缺口、原false／null／UNKNOWN、正式0.10及parent、策略與舊資料不變。不新抓行情、不回算資金績效。不另開Codex／代理、不公開私人資料、無Oracle／VPN／部署／付費／交易。里程碑保存後停止，等總監於Oracle帳戶完成時核定下一步，不自行開新研究。
