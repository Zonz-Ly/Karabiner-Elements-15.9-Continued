# Karabiner-Elements 15.9.0 修復回移

這個分支以官方 **v15.9.0**（`a35a45692a8fdc811312050b404cb14602f55c74`）為基底，保留原有 IOHID 鍵盤捕捉路徑、local_datagram 通訊、應用拆分及虛擬 HID 驅動。

檢查日期：2026-10-23。逐項比對 v16.0.0、v16.1.0、v16.2.0、v16.3.0 的 release notes 與相關提交；另外檢查目前上游 v16.99.2（`05043031913c2dbbafb80308b9c93aa6a4823c80`）的 Beta 修復，未引入新版鍵盤捕捉或應用架構。可獨立回移的 Beta 選擇器顯示修復也包含在內。

## 已回移的修復

| 問題 | 來源與處理 |
| --- | --- |
| Complex Modifications／Profiles 拖動時捲動會失效或跳位 | [5e130254a](https://github.com/pqrs-org/Karabiner-Elements/commit/5e130254a801ca577c6a0fa909ea5eaa66cc33ae)、[0c4e29596](https://github.com/pqrs-org/Karabiner-Elements/commit/0c4e295962e9190841e140d864a03539d384b883)。拖動期間不因滑鼠離開把手就停用移動，排序後保留 SwiftUI 清單項目身分與捲動狀態。 |
| unset 後表達式仍讀到舊變數值 | [c13574f90](https://github.com/pqrs-org/Karabiner-Elements/commit/c13574f9057e077ad99acd7c06eb1a69ef97a4de)、[b27c5a378](https://github.com/pqrs-org/Karabiner-Elements/commit/b27c5a378ae8fae20236ea0a41ccd19c96540430)。同步清除編譯後表達式的數字／字串儲存值；再次 set 時取消清除標記。 |
| RunLoop 無法啟動時產生不必要的 crash report | [7254647bc](https://github.com/pqrs-org/Karabiner-Elements/commit/7254647bc810ae972a6eb7fde7e0dccdb505a3f3)。只回移必要的 failure_policy 支援。正式程式以 exit 結束；測試仍預設 abort。 |
| ac_zoom_in／ac_zoom_out 的 HID usage 顛倒 | [315972554](https://github.com/pqrs-org/Karabiner-Elements/commit/3159725547b1f471405886c31e51009cf9e25791)。只修正兩個常數：Zoom In = 0x22d，Zoom Out = 0x22e。 |
| 舊格式系統預設設定使 Settings 在登入時意外開啟 | [e95bbaf9c](https://github.com/pqrs-org/Karabiner-Elements/commit/e95bbaf9c62efb206fa2b7b642734e365470fbad)。追蹤設定來源，暫用系統設定時不因鍵盤類型欄位缺失開啟 Settings。使用者設定的原有提醒保留。 |
| Event Tap 洩漏與銷毀時的回呼競爭 | [cd95ed8f8](https://github.com/pqrs-org/Karabiner-Elements/commit/cd95ed8f829816c8018beb30763ff60c67febcc4)、[229c00b18](https://github.com/pqrs-org/Karabiner-Elements/commit/229c00b187f1a9f2d1e17e6ffbeee8f4d3e16c69)。明確 invalidate Mach port；建立 RunLoop source 失敗時也釋放。清理在 Event Tap 自身 RunLoop 執行，完成後才銷毀實例。這個監視器在 15.9 已存在，沒有加入鍵盤 key-down／key-up 捕捉。 |
| macOS 27 上 Simple Modifications 選擇器未顯示選取標記 | [a0ef4a258](https://github.com/pqrs-org/Karabiner-Elements/commit/a0ef4a2586f135c5bb3a21c90afd60938e7ff9fb)。15.9 使用相同的選單圖片方式，因此改用文字內的單色 Unicode 選取符號；沒有引入新版的在地化或 Settings 架構。 |
| 鎖屏 Escape／睡眠快捷鍵的 key-up 立即喚醒電腦 | [5e6952040](https://github.com/pqrs-org/Karabiner-Elements/commit/5e6952040083948e55a0571613f02e0d1f03cd7f)、[618ad4054](https://github.com/pqrs-org/Karabiner-Elements/commit/618ad4054084739885175a292d64172f717d2627)。睡眠快捷鍵保留上游延遲；鎖屏 Escape 另外改為等待實體放開，再送出成對事件。 |

## Escape 修復的行為

當前景應用為 `com.apple.loginwindow`，Escape key-down 暫不送出；實體放開時才依序送出虛擬 key-down、key-up。沿用輸出佇列的至少 5 ms 間隔，沒有固定 500 ms 等待。映射後的 Escape（如 Caps Lock → Escape）也適用。

例如輸入 down = 100 ms、up = 160 ms，輸出為 160／165 ms。按住兩秒也等到放開才觸發熄屏。一般應用的 Escape、鎖屏上的其他按鍵保持原樣。

待送 Escape 以裝置區分；裝置解除攔截、斷線或按鍵狀態清理時取消。若放開時已離開 loginwindow，也不送出待送的按下事件。這項行為在本機內建／外接鍵盤環境中由使用者確認短按、長按及熄屏後不再喚醒均正常；不據此保證所有硬體與睡眠情境。

Command + Option + Power／Eject 仍採上游預設 500 ms 延遲，避免在等待放開期間遺失快捷鍵所需的修飾鍵狀態。`global.delay_milliseconds_before_sleep_shortcut`（0–10000 ms）只控制這組快捷鍵，0 表示關閉該延遲；不控制鎖屏 Escape。

15.9 的 Core Service 以 root 權限透過 IOHID 獨佔鍵盤，再由虛擬 HID 裝置送出事件。它本來就需要在登入／密碼畫面支援重映射，不能以「鎖屏會阻止所有軟體接觸所有按鍵」推論 Escape 特別漏過保護。這次修復針對的是虛擬 HID 事件時序；沒有停用 macOS 的安全輸入保護，也沒有新增密碼或原始按鍵內容的記錄。相關架構說明：[官方 Security 文件](https://karabiner-elements.pqrs.org/docs/help/advanced-topics/security/)。

## 已核對但未回移

| Release note／相關問題 | 不適用於本分支的理由 |
| --- | --- |
| 16.0：擷取遺漏事件後 modifier 卡住；16.3：左右 Command／Shift 同時按下時卡住 | 相關修復依賴新版 CGEventTap 鍵盤 fallback、keyboard_suppression 與實體 modifier 對帳路徑。依本次範圍不移植這些路徑。 |
| 16.2：Core Service agent 退出時偶爾 abort | 15.9 的 agent 僅請求／等待 Input Monitoring 權限後返回，沒有後續版本加入的 AppKit／Accessibility 元件生命週期。舊版已存在的 RunLoop 失敗與 Event Tap 清理問題則已另外處理。 |
| 16.2：喚醒後數秒不工作；16.3：快速睡眠／喚醒後 30 秒不工作 | 後續版替換了 IPC（unix_domain_stream）及虛擬 HID service 通訊。相關修復更新該新通訊實作；15.9 保留 local_datagram 與 VirtualHIDDevice 6.8.0，不移植整套新 IPC／驅動。 |
| 16.3：每次喚醒都檢查更新 | 15.9 原本沒有該週期排程問題；本 fork 最終移除了整個官方更新功能。 |
| Beta：Caps Lock 被重複映射、ISO 鍵錯配 | 都針對新版 CGEventTap fallback；排除。 |
| 其他 Beta 新 Settings／ConsoleUserServer 介面、JavaScript 規則與新打包／簽名流程修復 | 涉及 15.9 沒有的功能或其後重構。不為回移這些修復引入新功能或新應用結構。 |
| Menu Bar 位置保存、Settings 新狀態結構與「For export」文字錯誤 | 對應的新 ConsoleUserServer `MenuBarExtra.isInserted` 條件、新狀態欄位及文案都未存在於 15.9。 |
| 非打包 GUI app 偵測、notes、更多按鍵／滑鼠支援、通知樣式、CLI 選項等 | 屬新增支援或功能增強，不屬此次 bug 回移。 |

虛擬 HID 驅動子模組仍鎖定 **6.8.0**（`c946e1458e8c1692a39511e62b8c0408928a0aa8`），CPM lock 子模組也維持原版。此 fork 的發布版本為 **15.9.1**；移除了官方更新器、啟動時更新檢查、選單／設定入口及相關 API。vendor 中只有 RunLoop failure policy 與 Zoom usage 的小範圍修正，未整批更新依賴。

## 驗證與建置

詳細測試結果見同目錄 `VERIFICATION.zh-TW.md`。新增回歸案例涵蓋鎖屏 Escape、映射後 Escape、一般應用 Escape、其他按鍵、裝置斷線／前景切換取消、長按、睡眠快捷鍵延遲，以及數字／字串 unset 後重新求值與 HID usage 雙向轉換。

核心測試：

```sh
make -C tests
```

WindowServer Event Tap 實機測試是獨立的可選測試，不會記錄輸入內容：

```sh
bash tests/integration/run-event-tap-lifecycle.sh
```

若測試程式無法建立 Event Tap，會回傳 77 並標示 SKIP；這種結果不代表洩漏測試已通過。檔案監視測試需要正常的 FSEvents 存取，受限沙盒可能使它失敗。

後續已將原有建置流程的基準調整為 **macOS 14.5+／Xcode 16.2**，並修正相依套件與 Swift 6.0 相容性；詳見 `BUILDING-SONOMA.zh-TW.md`。另已新增純 CLT 建置流程，沿用本機 15.9.0 資源並實際產出 arm64 PKG／DMG，詳見 `BUILDING-CLT.zh-TW.md`。已在本機替換核心服務並確認鎖屏短按與長按 Escape 正常。

安裝修補版後的實機驗收：

1. 先在一般應用確認 Escape、Caps Lock 映射、左右修飾鍵及輸入法正常。
2. 用 Control + Command + Q 鎖屏，短按並放開 Escape；等待至少 5 秒，螢幕應保持熄滅。
3. 以其他按鍵或正常方式喚醒，確認密碼可輸入、沒有卡住的 Escape／修飾鍵。
4. 對內建鍵盤、外接鍵盤、Caps Lock → Escape 分別重複；再檢查 Option + Command + Power／Eject。
5. 另測長按 Escape、快速重複按與快速睡眠／喚醒；記錄硬體與行為，避免把短按成功推論成所有睡眠情境均已修復。
