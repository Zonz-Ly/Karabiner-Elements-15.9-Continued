# 只使用 Command Line Tools 建置

這條流程為本機使用的 15.9.0 修復版而設：以 CLT 重新編譯全部程式碼，
使用已安裝的官方 15.9.0 App 內的 Resources，並封入倉庫原有的
Karabiner-DriverKit-VirtualHIDDevice 6.8.0 安裝包。
不會呼叫 `xcodebuild`、`xcodegen`、`actool` 或 SwiftPM 建置系統。

## 環境與來源

- macOS 14.5 或更新版本、CLT 16.2（Swift 6.0.3、macOS SDK 15.2）。
- Python 3、Ruby、Git，以及 macOS 內建的簽名與封裝工具。
- 此倉庫的 15.9.0 修復分支及原有 submodules。
- 本機完整安裝的官方 Karabiner-Elements 15.9.0（含輔助 App）。
  建置會逐一檢查 `CFBundleShortVersionString`，並記錄複製資源的 SHA-256。
  也接受已安裝、版本與本次建置相同且帶有 `KELocalBuild` 標記的本 fork 資源。
  `--resource-root` 也可以指定另一個包含 `Applications` 與 `Library` 的目錄。

程式只複製各 App 的 `Contents/Resources`，不使用原版執行檔。
App 的 Info.plist、LaunchAgents 與 LaunchDaemons 從本分支產生。
本機圖標位於 `files/icons/`，建置時直接套用 `.icns` 並寫入 Info.plist，
不需要 actool。其餘圖片沿用原資源；修改 `.xcassets` 仍須先重新編譯資源。

## 建置

在倉庫根目錄執行：

```sh
make package-clt
```

預設為目前電腦的架構。Apple Silicon 會產出 `arm64`，Intel 會產出 `x86_64`。
這是單一架構的安裝包；跨架構建置可以指定 `--arch`，但須另行驗證。

```sh
make package-clt CLT_BUILD_ARGS='--arch arm64'
```

首次執行會從上游 GitHub 取得五個固定版本的套件：Collections 1.1.4、
AsyncAlgorithms 1.0.4、Highlightr 2.1.2、CodeEditor 1.2.6、SettingsAccess 2.1.0。
腳本同時核對確切 Git commit 與追蹤檔案是否有修改。
可用 `--dependencies` 指定已下載的套件目錄。

```sh
python3 scripts/build_with_clt.py --dependencies /path/to/dependencies --package --dmg
```

`build-clt/logs` 保留個別命令與錯誤，`build-clt/build-manifest.json` 記錄工具鏈、
資源雜湊、套件版本與驅動雜湊。重新執行可使用編譯快取。
部分 CLT 16.2 安裝含重複的 SwiftBridging module map；腳本會在建置目錄
產生 VFS overlay 隱藏重複宣告，不修改 `/Library/Developer/CommandLineTools`。

App 會在系統暫存目錄組裝與簽名，避免「文件」目錄的檔案同步服務自動加入
Finder metadata、使簽名失敗。可用 `--staging-dir` 指定另一個本機暫存目錄。
PKG、DMG 與紀錄仍保留在 `build-clt`。不要將 staging 目錄放在同步磁碟內。

## 產物與簽名

- `build-clt/release/Karabiner-Elements-15.9.1-backports-arm64.pkg`
- `build-clt/Karabiner-Elements-15.9.1-backports-arm64.dmg`
- `build-clt/release/build-manifest.json`

Intel 的檔名使用 `x86_64`。

重編譯的 App 使用 ad-hoc 本機簽名；外層安裝包沒有 Developer ID 簽名或公證。
原版驅動安裝包保持原有簽名與內容。這與官方發布包的信任身分不同，安裝後
可能需要重新允許輸入監控或背景服務。建置腳本不安裝或啟動系統服務；安裝 PKG 才會註冊服務。

15.9.1 已移除官方 Updater、Sparkle、啟動更新檢查與手動更新入口，
不會由官方自動更新覆蓋此 fork。

## 圖標與本機服務

三個新 `.icns` 位於原版 `files/icons/`，Xcode 專案與 CLT 共用同一份來源。
主程式與輔助 App 使用 KarabinerElements；EventViewer 與 MultitouchExtension 各用自己的圖標。
不再建置 AppIconSwitcher，也沒有圖標選擇介面；不再寫入 Finder 自訂圖標。
原有 asset catalog 的其他圖片仍沿用已安裝 15.9.0 資源；簽名驗證過的 DriverKit 安裝包不更動。

CLT 的 ad-hoc 核心服務由安裝包安裝至標準 `/Library/LaunchDaemons/`，
沿用原版 plist 和 label。安裝時清理舊的核心 SMAppService 註冊，避免官方簽名的舊父程式限制阻止本機程式啟動。
驅動 daemon 與使用者 agents 仍沿用原版服務管理；沒有修改 SIP、AMFI 或 TCC 資料庫。
升級前與解除安裝時會卸載並移除這個核心 plist。完整 Xcode 簽名建置仍使用原版 SMAppService 路徑。

## 驗證邊界

建置成功與簽名驗證通過，不代表已在鎖定畫面驗證 Esc 的行為。
目前核心已通過本機短按與長按 Esc 實測；最終完整安裝包仍須在目標電腦安裝後重新驗收。
完整測試結果與本機驗證紀錄見 `VERIFICATION.zh-TW.md`。
