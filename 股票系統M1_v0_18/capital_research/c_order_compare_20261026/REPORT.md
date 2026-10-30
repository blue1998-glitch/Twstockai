# C原單保存結果唯讀並列：完成報告

基線`63a81306b0d181dd47339b3bca01fd6347b94881`。開工實核遠端／本地同此SHA、原分支、tracked／index／untracked皆0。原唯一Codex／原工作區；依本輪功能里程碑授權有限實作、必要驗證、自審及正常保存讀回，不開其他代理、分支或worktree。

## 交付能力

現在可直接讀[合格重評對資格未知等待](actual/reviewed-versus-unknown-wait/readable.txt)，核對同原C單的核准量、成交、待交割、活單、預留及原帳，並看見重評結果差異。沿既有`lifecycle_compare`／`lifecycle_compare_read`，比較與摘要核心一個byte也沒改；沒有新數值模組、會計、策略或schema遷移。

共七份已保存原件組成六個範例，先存契約、精確input引用／SHA、expected及14份核心／READ source指紋於`intake.json`，再只執行READ投影。新helper只載入指紋匹配的原件，`build.py`只向新的不存在目錄寫入比較actual和文字，不能覆蓋已存在證據。原件、行情、oracle及歷史log完全不改。

## 實際保存結果

| 範例 | 保存結果 |
| --- | --- |
| reviewed-versus-unknown-wait | COMPARABLE。原C帳1430、期初A100/B5/C2、現金100、一般reserve100、cash80/A10權利、完整市場與1/9截止一致。合格重評：原B單20成交、待交割20、應付401.400；當期資格UNKNOWN：0成交、活單20、應付0。兩欄現金皆596.500，沒有重開本金。 |
| unknown-future-revocation-prefix | COMPARABLE。完整來源／execution ID不同，當期opening／window／environment／market identity相同。兩欄原B單皆成交20；只證這對前綴控制，不泛稱所有未來metadata都可忽略。 |
| capacity-mismatch | REFUSED、columns=[]；`/market/tape/5/capacity_shares`的20／7不同。 |
| market-state-mismatch | REFUSED、columns=[]；`/market/tape/5/market_state`的OPEN／LIMIT_UP_NO_BUY不同。 |
| cutoff-mismatch | REFUSED、columns=[]；`/window/observed_until`為1/9／1/12，另列市場範圍／容量等差異。不是只有截止不同的單因素反例，不補行情或截短。 |
| opening-account-mismatch | REFUSED、columns=[]；`/opening/initial_capital`為1430／1330、`/opening/account/holdings/B/shares`為5／0，另列token差異。舊E原件只作另一合成帳的拒比控制，不冒稱同一C單或單因素帳戶案例。 |

保存結果在`actual/*/actual.json`及同資料夾`readable.txt`，索引`actual/summary.json`。COMPARABLE表示原閘門所列的初始共同條件一致，後續資格review可以不同；這不是同完整資訊下的策略競爭，沒有勝負、績效或政策因果結論。

## 必要驗證與自審

本輪只執行4個唯一unittest方法、4次方法執行，全部通過：六案符合事前expected／文字投影、原帳／原單scope／remaining／權利／reserve／latest／全部token原樣連結、API成功及拒比輸入不變、fresh-process CLI成功／拒比兩路徑。CLI檢查阻擋所有數值引擎import、檔案寫入、子程序與網路，仍得到與保存actual完全相同的comparison，exit分別0與2。兩個子程序與六個範例不另加成測試方法數；歷史13／11及更早PASS均不累加。

沒有失敗／改oracle。`source-versions-before-read.json`固定本輪READ輔助程式，`self-review.json`核來源／expected／保護source指紋、僅有新範例及既有三個入口狀態變更、敏感內容與測試計數；`CHANGE_MANIFEST.json`涵蓋本輪相關檔案而不含自身。根AGENTS／CONTINUE及capital README只加最新有效入口，舊內文bytes完整保留，不建立平行規則。

重要帳／成交／未來資訊複核只核本輪READ投影與來源完整性；沒有重跑原C數值案例，不能把本輪4方法說成重新驗過原全部帳務。原job→execution來源認證與完整分叉等證明界線未擴張。新input仍指向固定基線原件；不要求當前source或summary等於舊版producer結果。

## 保留限制與下一步

沒有保存同C原市場下「完全未重評且完整觀察至1/9」的另一新actual；本輪等待控制明確是UNKNOWN遭拒後仍等待，不補造無重評控制。同時不同市場、窗口或期初帳的原件只拒比，不能從各自期末結果排策略名次。六個範例不是六個獨立市場樣本。

未跑舊suite、九路徑、真實producer、資格重算、UI／Android、樣本外；不抓新來源、不收私人文件、不bootstrap、部署、交易、付費或發訊息。1101期初cash_claims UNKNOWN／拒算、70／2／其中8／真實總淨合格0、全部正式false、主壓力null與正式來源／圖形／人工契約保持。多活單、外部既有單、期初應付、R2/F、來源認證等原未支援不擴張。Astra及第一工作區救援原件仍未取得未讀；不冒Work獨立原件驗收。

本輪無需人工操作。下一項可留在原Codex：若使用者指定，再補「C原單遭拒重評後，當期資格恢復時的受控再次重評入口」，仍須同一原單／剩餘量／完整歷史，不能變新批或繞過帳務限制。這是待指定的有限能力，本輪不實作、不新增策略條件。
