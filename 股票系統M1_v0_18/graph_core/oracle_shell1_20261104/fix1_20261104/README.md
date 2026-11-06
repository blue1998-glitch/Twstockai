# Cloud Shell compartments參數補正

使用者本人回報登入及Home Region已核，失敗查詢為compartments；原始CLI stderr未取得，不能聲稱排除其他原因。核官方CLI文件：--compartment-id-in-subtree為[boolean]、需帶true／false；原版缺值，因共用argv序列化把所有True當開關。以CLI參數解析替身在舊版重現OCI_READ_FAILED；新版傳明示小寫值，--all仍是無值旗標。舊Mock只回成功、未檢驗CLI語法，這是原測試缺口。

新22唯一方法＝2新增＋20必要工具回歸；未跑原合成產品16或瀏覽器15。新增CLI_ARGUMENT_ERROR安全分類與固定操作名診斷，不回顯stderr、帳戶識別或token。新0.2獨立交付包，原0.1、pilot／FM3／main保留。未在本人帳戶重跑，未宣稱真實查詢已恢復；仍只唯讀，建機及HTTPS後段未完成。
