# Open-VINC Examples

獨立 C++ 入門範例：先運行一個 Module，再讓兩個 Module 傳遞計數訊息。框架固定為 **v0.1.2**，
commit `466cfa60ae12798192df0ceae8ec175c48b70a76`。本專案使用公開 SDK 與 CMake functions。

## 教學順序

| 範例 | 建置入口 | 學習目標 |
| --- | --- | --- |
| 第一個運行模組 | `first-module/CMakeLists.txt` | 一個 Plugin 的註冊、啟動與正常停止 |
| 第一個跨程序訊息 | 根目錄 `CMakeLists.txt` | 兩個 Module 的計數訊息收發 |
| 讓模組接收自己的指令 | 同一個根目錄入口 | `receiver status`／`receiver reset` 與錯誤指令 |

兩個入口獨立配置，使用不同建置目錄，共用 `framework/open-vinc`。原有根目錄命令仍建置計數範例。

## 取得相依

```sh
git clone https://github.com/JayTDawgzone1994/open-vinc-examples.git
cd open-vinc-examples
git submodule update --init framework/open-vinc
git -C framework/open-vinc submodule update --init -- library/tcl/upstream library/fmt/upstream library/spdlog/upstream library/tomlplusplus/upstream
```

需要 CMake 3.20 以上、Ninja，以及支援本框架所用 C++23 功能的工具鏈。
Windows 使用 MSVC 開發者環境，Tcl 需要 NMAKE。此範例停用 Runtime Web UI 與 Python SDK，
所以不需要 Node.js、npm 或 Python 來建置／執行／測試。
Linux/macOS 的相依與平台限制以框架 README 為準，這份範例的實機結果見下方。

## 第一個運行模組

從 repository 根目錄執行：

```sh
cmake -S first-module -B build/first-module-debug -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build/first-module-debug --parallel 4
ctest --test-dir build/first-module-debug --output-on-failure
```

Release 改用 `build/first-module-release` 與 `-DCMAKE_BUILD_TYPE=Release`。
此入口新增 `helloModule`，不加入計數 Module 或應用訊息；中央仍登記框架內建的 `bagRecorder` 種類，但不自動啟動它。`hello.cpp` 使用 FrameworkLoop，
`on_start`／`on_stop` 印出 `hello started`／`hello stopped`；必要的 `module_interface` 回傳 1，尚不提供應用命令。
沒有額外應用資源或使用者執行緒；正常停止由框架結束 pump 並執行清理 hook。
`FIRST_MODULE_BUILD_TESTS` 控制這個入口的測試，與計數入口的 `COUNTER_BUILD_TESTS` 分開。

從根目錄執行以下 PowerShell 命令，再在 Vinc Shell 輸入 `helloModule`。
等待 `hello started` 與 `Started hello`，以 `help` 查看實例狀態，最後用 `exit` 關閉。

```powershell
.\build\first-module-debug\Vinc.exe --shell-port 0
```

關閉前一次中央後，也可使用附帶的啟動腳本；腳本返回後仍在 Shell 輸入 `exit`：

```powershell
.\build\first-module-debug\Vinc.exe --shell-port 0 -S first-module/scripts/startup.tcl
```

`HelloModule` 是 C++ 類別，`hello_module` 是 CMake target，`helloModule` 是 ModuleType，
`hello` 是固定實例名稱。重複啟動同名實例會被拒絕，第一篇不提供 `--name`。
中央身分為 `first-module-example`，與計數入口分開；仍需維持 Host／Plugin 工具鏈、組態與 CRT 相容。
此入口也是 build-tree 專案，不是可任意搬動的安裝包。

`hello.shell` 實際執行中央與同一份啟動腳本，在 20 秒期限內驗證啟停輸出順序與中央正常退出。
測試透過 Tcl 同步建立 Module，不使用固定 sleep。它不涵蓋 Ctrl+C、強制崩潰或跨平台行為。
Windows CI 的 Debug／Release matrix 已包含兩個入口；遠端結果以 Actions 為準。

## 計數範例：建置與測試

```sh
cmake -S . -B build/debug -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build/debug --parallel 4
ctest --test-dir build/debug --output-on-failure
```

Release 使用另一個目錄 `build/release` 及 `-DCMAKE_BUILD_TYPE=Release`。
`COUNTER_BUILD_TESTS` 控制本範例測試；`BUILD_TESTING=OFF` 只關閉框架自己的內部測試。
使用 Ninja 單組態 generator，符合固定版本 Tcl 的建置契約。

## 實際操作

從專案根目錄執行；Windows：

```powershell
.\build\debug\Vinc.exe --shell-port 0 -S scripts/startup.tcl
```

POSIX 對應執行檔是 `./build/debug/Vinc`。本專案明確將中央輸出到建置根目錄。
`--shell-port 0` 避免占用固定的 5500 port；所有中央選項須放在 `-S` 之前。
這是 build-tree 範例；Plugin catalog 含絕對路徑，不是可任意搬動的安裝包。

在 **Vinc Shell** 輸入以下命令；每次等待看見接收輸出後再送下一筆：

```text
sender send
sender send
receiver status
exit
```

預期依序看見 `received sequence=1 publisher=sender`、`received sequence=2 publisher=sender`、
`received=2`。`exit` 正常停止兩個 Module 並等待程序退出。

接續的模組指令教學沿用同一個 Receiver。`receiver reset` 印出 `counter reset` 並清除接收數量，
再用 `receiver status` 可看到 `received=0`；它不重設 Sender 的訊息序號。
未知指令或多餘參數會印出 `Usage: receiver [status|reset]` 並回傳 1，Module 保持運行；
正常指令回傳 0，單獨輸入 `receiver` 仍等同 `receiver status`。

## 閱讀順序與契約

1. `messages/CounterSample.msg`：只定義 sequence，時間與發布者由框架填入。
2. `modules/publisher.cpp`：advertise、本地 make_message、push 與可恢復的 Shell 命令失敗。
3. `modules/subscriber.cpp`：保存 handle，lambda 只轉交本地 unique_ptr 給 `on_message`，由具名成員函式計數與輸出；on_stop 釋放訂閱。
4. `scripts/startup.tcl`：先啟動 Receiver，再啟動 Publisher，返回後框架繼續運作。
5. `CMakeLists.txt`：add_message_dir、add_module 與外部框架組裝。

ModuleType 為 `counterPublisher`／`counterSubscriber`，固定實例名稱為 `sender`／`receiver`；
第一篇不提供 --name，重複啟動同名實例會被拒絕。兩個 Module 都使用 FrameworkLoop，
callback 與 Shell hook 由同一個 pump 執行緒派送，不增加使用者執行緒。
Publisher 省略容量選項，使用 v0.1.2 預設的 2 個 slot、每筆完整訊息映像上限 1 MiB。
Subscriber 也省略選項，預設從 OldestRetained 接收，max_message_bytes=0 不另設接收大小上限；Publisher 的容量限制仍然存在。
讀者過慢時仍可能被覆蓋，這不是每筆必達保證。
OldestRetained 允許讀取 Publisher 加入時仍保留的資料；不能補回已覆蓋內容。
Receiver callback 取得已複製且驗證的本地訊息，應用程式不持有共享讀取保護。

## 測試與驗證

- `counter.lifecycle`：透過公開 Manager／OutputHub，實際啟動兩個 ModuleHost，核對不同 PID、
  訊息 1／2／3 與 publisher metadata、status／reset、錯誤命令與額外參數不改變計數、
  reset 後繼續接收、OS 確認正常退出及輸出回收；
  完整流程執行兩輪。依實際 callback 輸出等待，有明確期限，不用固定 sleep 猜資料送達。
- `counter.shell`：實際執行 Vinc、範例啟動腳本、發送命令、reset、錯誤命令與 exit，檢查正常退出。
  訊息內容與程序回收由 lifecycle 測試精確驗證，不以停止訊息取代 OS 退出證據。

## 待處理事項

- 完整三平台驗證、Python 對照範例、指定實例名稱、安裝／可重定位封裝留待後續。
- Ctrl+C 的行為沿用框架；本範例新增的測試驗證 exit／Manager 正常停止，不宣稱新增訊號測試。

## 單一 Module 實機紀錄（2026-10-25）

Windows x64、MSVC 19.51.36257、CMake 4.3.2、Ninja：

- `first-module/` 從獨立目錄完成 Debug／Release 建置，`hello.shell` 各 **1/1** 通過。
- 測試實際載入 Hello Plugin，核對啟動、停止順序與中央退出碼 0；輸出記錄於
  `build/first-module-debug/hello-test/output.log` 與對應 Release 目錄。
- Debug 另依教學手動操作本機 Shell：`helloModule` → `help` → `exit`，確認
  `Started hello`、`hello Running MID=1 PID=...`、`hello stopped` 及全部 Module 程序退出訊息。
- 首次受限環境的 MSVC 編譯器探測曾失敗（C1902）；同一工具鏈在可使用 PDB 服務的環境重新配置與建置成功，沒有修改框架或上游相依。
- 未執行 Linux／macOS、Ctrl+C 或強制崩潰測試；新增 CI matrix 尚未在遠端執行。

## 實機紀錄（2026-10-25）

Windows x64、MSVC 19.51.36257、CMake 4.3.2、Ninja：

- Debug 與 Release 分別完成建置，兩組態 CTest 各 2/2 通過。
- 每組態的 lifecycle 測試完整建立／收發／停止兩輪；Shell 測試另外執行真正的 Vinc 與 Tcl。
- 測試紀錄位於本機 build/debug/Testing/Temporary/LastTest.log 與對應 Release 目錄；不提交生成檔。
- 未執行 Linux/macOS 實機驗證。GitHub Actions 已提供 Windows Debug/Release 工作流程，遠端執行結果仍須以 Actions 為準。

## 接收函式可讀性調整（2026-10-26）

- Subscriber 的 lambda 只呼叫 `on_message(std::move(message))`，計數與輸出移到具名成員函式。
  保留原有訊息所有權、callback 執行緒與輸出內容，不增加執行緒。
- Windows x64／MSVC 19.51 的 Debug／Release 增量建置成功，`counter.lifecycle`、`counter.shell` 各 **2/2** 通過。
- 本輪未驗證 Linux／macOS 或遠端 CI；不修改固定框架與上游相依。

## Publisher 預設容量（2026-10-26）

- 入門 Publisher 省略 `PublisherOptions` 與容量常數，使用 v0.1.2 預設的 2 個 slot、每筆 1 MiB。
- Windows x64／MSVC 19.51 的 Debug／Release 增量建置成功，計數範例 Runtime 測試各 2/2 通過。
- 保留逐筆等待接收輸出的教學操作；不把有限緩衝區視為每筆必達保證。本輪未驗證其他平台或遠端 CI。

## Subscriber 預設選項（2026-10-26）

- 入門 Subscriber 只傳 topic 與轉交 `on_message()` 的 lambda，移除選項區塊與容量常數。
- Windows x64／MSVC 19.51 的 Debug／Release 增量建置成功，計數範例 Runtime 測試各 2/2 通過。
- 採用預設接收起點，不另設接收大小上限；本輪未驗證其他平台或遠端 CI。

## 入門 CMake 精簡（2026-10-26）

- 兩個入口移除重複的 C++23／MSVC Runtime 設定，以及與框架預設相同的 Apps／Python 開關。
  保留應用名稱、功能裁剪、UTF-8、Module／訊息組裝與穩定輸出路徑。
- 自動化測試各自移到 `tests/CMakeLists.txt`，由主檔最後一行 include；既有測試開關與預設值不變。
  獨立 lifecycle 測試 target 明確要求 C++23、關閉 extensions 並維持相容 CRT。
- Windows Debug／Release 的兩個入口重新配置、建置與測試通過：計數各 2/2、單一 Module 各 1/1。
- 另從兩個全新目錄配置，確認 Apps 預設 ON、Python 預設 OFF，且測試可正確註冊；未從這兩個探測目錄完整重建。
- 未修改固定框架或相依。Linux／macOS 與遠端 CI 未在本輪驗證。

## Module 指令教學（2026-10-26）

- Receiver 新增 `reset`，保留 `status` 與無子指令時查詢的既有行為。重置只改動接收計數，
  不重建訂閱、不重設 Publisher 的 sequence；所有操作仍由 FrameworkLoop 派送。
- Runtime 測試消耗已匹配的輸出片段，讓重複的 `received=2`／`received=0` 驗證必須等待新輸出。
  依實際收訊等待後，驗證無效命令／多餘參數不改動計數、reset 到 0、再收 sequence 3 後計數為 1。
- Windows x64／MSVC 19.51 的 Debug／Release 建置成功，計數範例各 2/2 測試通過。
- Debug 另按教學手動操作預設 Shell port：status 1 → reset → status 0 → unknown 回傳 1，
  再查詢仍為 0，發送下一筆 sequence 2 後計數為 1，最後確認兩個程序正常退出。
- Linux／macOS、遠端 CI 與其他故障情境未在本輪驗證。
