# Open-VINC Examples

第一個獨立 C++ 範例：兩個 Module 傳遞計數訊息。框架固定為 **v0.1.2**，
commit `466cfa60ae12798192df0ceae8ec175c48b70a76`。本專案使用公開 SDK 與 CMake functions。

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

## 建置與測試

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

## 閱讀順序與契約

1. `messages/CounterSample.msg`：只定義 sequence，時間與發布者由框架填入。
2. `modules/publisher.cpp`：advertise、本地 make_message、push 與可恢復的 Shell 命令失敗。
3. `modules/subscriber.cpp`：保存 handle、接收本地 unique_ptr、on_stop 釋放訂閱。
4. `scripts/startup.tcl`：先啟動 Receiver，再啟動 Publisher，返回後框架繼續運作。
5. `CMakeLists.txt`：add_message_dir、add_module 與外部框架組裝。

ModuleType 為 `counterPublisher`／`counterSubscriber`，固定實例名稱為 `sender`／`receiver`；
第一篇不提供 --name，重複啟動同名實例會被拒絕。兩個 Module 都使用 FrameworkLoop，
callback 與 Shell hook 由同一個 pump 執行緒派送，不增加使用者執行緒。
Publisher 保留 4 筆、每筆 4096 bytes。讀者過慢時仍可能被覆蓋，這不是每筆必達保證。
OldestRetained 允許讀取 Publisher 加入時仍保留的資料；不能補回已覆蓋內容。
Receiver callback 取得已複製且驗證的本地訊息，應用程式不持有共享讀取保護。

## 測試與驗證

- `counter.lifecycle`：透過公開 Manager／OutputHub，實際啟動兩個 ModuleHost，核對不同 PID、
  訊息 1／2 與 publisher metadata、錯誤命令不終止 Module、OS 確認正常退出及輸出回收；
  完整流程執行兩輪。依實際 callback 輸出等待，有明確期限，不用固定 sleep 猜資料送達。
- `counter.shell`：實際執行 Vinc、範例啟動腳本、發送命令、錯誤命令與 exit，檢查正常退出。
  訊息內容與程序回收由 lifecycle 測試精確驗證，不以停止訊息取代 OS 退出證據。

## 待處理事項

- 完整三平台驗證、Python 對照範例、指定實例名稱、安裝／可重定位封裝留待後續。
- Ctrl+C 的行為沿用框架；本範例新增的測試驗證 exit／Manager 正常停止，不宣稱新增訊號測試。

## 實機紀錄（2026-10-25）

Windows x64、MSVC 19.51.36257、CMake 4.3.2、Ninja：

- Debug 與 Release 分別完成建置，兩組態 CTest 各 2/2 通過。
- 每組態的 lifecycle 測試完整建立／收發／停止兩輪；Shell 測試另外執行真正的 Vinc 與 Tcl。
- 測試紀錄位於本機 build/debug/Testing/Temporary/LastTest.log 與對應 Release 目錄；不提交生成檔。
- 未執行 Linux/macOS 實機驗證。GitHub Actions 已提供 Windows Debug/Release 工作流程，遠端執行結果仍須以 Actions 為準。
