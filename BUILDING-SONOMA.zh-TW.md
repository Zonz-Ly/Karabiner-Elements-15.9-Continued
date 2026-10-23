# 在 macOS Sonoma 建置修補版

此分支的建置基準已調整為 **macOS 14.5+、完整 Xcode 16.2、Swift 6.0、macOS 15.2 SDK**，涵蓋本機 macOS 14.8.7。程式的最低執行版本仍是 **macOS 13.0**；IOHID 捕捉方式、VirtualHIDDevice 6.8.0 與先前的 Escape／bug 回移修補保持不變。

Apple 官方確認 Xcode 16.2 支援 macOS Sonoma 14.5 以上：[Xcode 系統需求](https://developer.apple.com/xcode/system-requirements/)、[16.2 release notes](https://developer.apple.com/documentation/xcode-release-notes/xcode-16_2-release-notes)。

## 需要的工具

1. 從 [Apple Developer Downloads](https://developer.apple.com/download/all/?q=Xcode%2016.2) 下載完整 **Xcode 16.2**，解壓後放在 Applications。下載可能需要登入 Apple 帳號。請指定 16.2；App Store 提供的新版不一定支援 Sonoma。
2. 開啟 Xcode 一次，完成初始設定，然後在終端選用它。以下假設名稱為 `Xcode.app`；若保留為 `Xcode_16.2.app`，請相應修改路徑：

   ```sh
   sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer
   sudo xcodebuild -runFirstLaunch
   xcodebuild -version
   ```

3. 安裝 XcodeGen 2.42.0 以上、CMake 3.24 以上與 xz。若 Homebrew 的目前版本可在本機安裝：

   ```sh
   brew install xcodegen cmake xz
   ```

   若新版 XcodeGen 的安裝要求過高，可使用已驗證可在本機執行的 [XcodeGen 2.42.0 官方版本](https://github.com/yonaskolb/XcodeGen/releases/tag/2.42.0)，將其中 `bin/xcodegen` 所在目錄加到 PATH。

本頁說明原有的 Xcode 建置流程。若僅有 Command Line Tools，可改用已實際產出安裝包的 [`BUILDING-CLT.zh-TW.md`](BUILDING-CLT.zh-TW.md) 流程，沿用本機 15.9.0 圖片並直接封入新的 `.icns` 圖標。

## 建置

在本倉庫根目錄執行：

```sh
git submodule update --init --recursive
make check-build-environment
make package
```

安裝包輸出為 `Karabiner-Elements-15.9.1.dmg`。這些指令建置安裝包，不會自動安裝或替換正在執行的服務。

只建置程式可用 `make build`；C++ 測試為 `make -C tests`。

`make check-compiler-environment` 僅核對 macOS／Swift／SDK 版本，不代表完整 Xcode 已安裝或程式已建置。`make build` 和 `make package` 會先執行完整環境檢查，缺少 Xcode 時在清除既有輸出前停止並提供處理方式。

## 真正修改的相容性障礙

- AsyncAlgorithms 1.1.1 的 `Package.swift` 要求 Swift 6.2，改為 Swift 5.8 工具鏈以上可用的 **1.0.4**。Karabiner 使用的 debounce、AsyncTimerSequence 等 API 在此版本可用。
- 固定 **Collections 1.1.4**、**CodeEditor 1.2.6**、**Highlightr 2.1.2**、**SettingsAccess 2.1.0**。避免日後套件解析選到提高 Swift／系統需求的版本。
- 所有專案規格指定 Xcode 16.2 基準與 XcodeGen 2.42.0 最低版本。
- 移除六處 Swift 6.0 不接受的函式參數／呼叫結尾逗號。
- MultitouchExtension 的四個睡眠／喚醒通知序列將未使用的 `Notification` 內容映射成 `Void`，再回到 MainActor。這保留通知與取消行為，解決舊 Foundation SDK 的非 Sendable 通知跨 actor 錯誤；沒有把 Swift 語言版本改成 5，也沒有停用併發檢查。

請保留專案檔的 `exactVersion`，不要重新改回開放式的 `from` 範圍。

## 本機驗證結果

- macOS 14.8.7／Swift 6.0.3／SDK 15.2 的版本檢查通過。
- XcodeGen **2.42.0** 實際生成全部 **15 份**專案規格，包括 Updater 有／無簽名兩種組態；生成的專案確認包含固定套件版本。
- Collections 的三個相依模組、AsyncAlgorithms 1.0.4、Highlightr、CodeEditor、SettingsAccess，共 **7 個相依模組實際編譯通過**。
- **14 個目標的 Swift 原始碼型別檢查通過**，使用 `-warnings-as-errors`、SDK 15.2、deployment target 13.0；原本的 Swift 6 目標維持 Swift 6。上述為移除 Updater 前的檢查；15.9.1 已不包含 Updater 或 Sparkle。
- 先前 C++ 完整測試結果仍為 31 組、168 個測試、3604 個 assertions 通過；此次沒有改動 C++ 核心。

本機 Command Line Tools 有重複 SwiftBridging module map，SwiftPM manifest 也出現 PackageDescription 連結不一致。上述原始碼檢查使用工作目錄內的 VFS overlay、指定 SDK 和直接模組編譯繞過，**沒有更動系統工具鏈檔案**。後續新增的 CLT 建置腳本已將這些處理納入，直接編譯固定版本套件，不呼叫 SwiftPM 建置系統。安裝完整 Xcode 16.2 後仍可使用標準 `make package`。

**後續已用 CLT 產出 arm64 PKG／DMG**，並通過完整程式連結、App 簽名、資源載入、CLI 與封裝內容檢查。原有 Xcode 流程仍未實際執行；核心已安裝並通過鎖屏短按／長按 Escape 實測，AppKit 側邊欄預覽也已由使用者確認改善。詳見 `VERIFICATION.zh-TW.md`。
