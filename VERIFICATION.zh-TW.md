# 驗證紀錄

日期：2026-10-23。環境：Apple Silicon、macOS 14.8.7、CLT 16.2、Apple Clang 16.0.0、Swift 6.0.3、SDK 15.2。

## 核心行為與介面實測

- 鎖屏 Escape 已改為等實體放開，再送出虛擬 down/up；專項測試 **3 tests、944 assertions** 通過，包含短按、長按兩秒、映射成 Escape、離開 loginwindow 與裝置解除攔截時取消。
- 一般應用 Escape 保持原樣；Command+Option+Power/Eject 保留上游延遲。
- 本機替換核心後，Input Monitoring、內建／外接鍵盤接管及虛擬 HID 連線正常。使用者確認短按與長按正常，熄屏後不會再次喚醒。
- AppKit 側邊欄預覽已實際操作收合／展開；使用者確認卡頓改善、按鈕位置與頂部背景正常。移除原版左側 2 pt 補丁後，收合截圖已確認白邊消失。

## 15.9.0 整理版必要檢查（升版及移除更新器之前）

- 13 份 XcodeGen 專案規格成功生成，資源路徑有效；不等同完整 Xcode 建置。
- CLT 完整編譯及連結成功。重新展開 PKG：9 個 App 的 ad-hoc 簽名與新圖標通過；12 個執行檔均為 arm64，動態函式庫無建置目錄依賴。
- 安裝／移除腳本語法、封裝內容與原始碼一致；核心 LaunchDaemon 保留原版 label、程式路徑及 KeepAlive。
- DriverKit 6.8.0 封裝前後 22 個檔案逐一 SHA-256 相同，原版 App／dext 簽名有效。Apple 簽名驗證在沙盒外執行。
- DMG CRC 完整性驗證通過。
- 廣泛回歸在使用者要求只做必要檢查後停止；此前完成 18 組、115 tests、1315 assertions。**這不是本輪全套測試通過的聲明。** 更早的 bug 回移版本曾完成 31 組／168 tests／3604 assertions。
- Event Tap 生命週期測試曾重現原版 0 → 10 個殘留註冊；修復後 0 → 0，ASan 無錯誤。可用 `tests/integration/run-event-tap-lifecycle.sh` 重現。

## 最終 15.9.1 的範圍

上述必要檢查完成後，依使用者要求移除官方 Updater、Sparkle、更新入口、啟動更新檢查及相關 API，改為 15.9.1，再重新編譯與封裝。
**依使用者要求，此後不重跑測試或最終整包驗證。** 建置仍需完成編譯、連結與本機簽名。

外層安裝包未作 Developer ID 簽名或公證，DriverKit 原版簽名保留。
最終整包未自動安裝；目前系統仍保留已通過實測的核心。安裝後可能需重新允許 Input Monitoring／背景服務。


## EventViewer 側邊欄同步（2026-10-24）

將已用於 Settings 的 AppKit 側邊欄容器移至 `src/apps/share/swift/Views/NativeSidebarSplitView.swift`，
Settings 與 EventViewer 共用；EventViewer 保留原清單外觀和列間距，加入完整高度的背景處理，
並移除舊 NavigationSplitView 的左側 2 pt 留白補丁。版本維持 15.9.1。
本次依使用者要求只重新編譯與封裝，未執行自動或代理操作的介面測試。使用者於 2026-10-24 回報實測完全正常，據此同步 GitHub 並替換同版本 Release。
