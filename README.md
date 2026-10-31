# Open-VINC Examples

獨立 C++／Python 入門範例：先運行一個 Module，再讓兩個 Module 傳遞計數訊息。框架固定為 **v0.1.2**，
commit `466cfa60ae12798192df0ceae8ec175c48b70a76`。本專案使用公開 SDK 與 CMake functions。

## 教學順序

| 範例 | 建置入口 | 學習目標 |
| --- | --- | --- |
| 第一個運行模組 | `first-module/CMakeLists.txt` | 一個 Plugin 的註冊、啟動與正常停止 |
| 第一個跨程序訊息 | 根目錄 `CMakeLists.txt` | 兩個 Module 的計數訊息收發 |
| 自訂訊息 | 同一個根目錄入口，新增 `custom-message/` | 定義 SensorReading 的數值與字串欄位，生成型別並收發 |
| 讓模組接收自己的指令 | 同一個根目錄入口 | `receiver status`／`receiver reset` 與錯誤指令 |
| 設定與儲存模組參數 | 同一個根目錄入口，新增 `parameters/` | 調整 `sender.step`、保存並重新啟動 |
| 第一個 RPC | 同一個根目錄入口，新增 `rpc/` | `sender count` 請求 receiver 的接收數量 |
| 使用啟動腳本 | 同一個 RPC 範例 | `-S` 與 `srun` 共用 scripts/rpc-startup.tcl |
| 讓模組輸出日誌 | 同一個根目錄入口，新增 `logging/` | 四種等級、來源過濾與 Shell 顯示過濾 |

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
所以 C++ 入口不需要 Node.js、npm 或 Python 來建置／執行／測試。
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

- 完整三平台驗證、Python 遠端 CI、指定實例名稱、安裝／可重定位封裝留待後續。
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

## Python 入門範例（2026-10-26）

`python/` 是獨立建置入口，部署 helloModule、counterPublisher、counterSubscriber、parameterPublisher、rpcPublisher、rpcSubscriber、logPublisher、logSubscriber 八個 Python Module，
共用根目錄的 CounterSample.msg。ModuleType 與實例名稱對應 C++ 教學，讓 Shell 操作保持相同。
不加入同名的 C++ Plugin，以免掃描時衝突。

在已載入 MSVC x64 環境的 PowerShell，從 repository 根目錄執行：

```powershell
git -C framework/open-vinc submodule update --init -- library/pybind11/upstream
py -3.13 -m venv .venv
cmake -S python -B build/python -G Ninja -DCMAKE_BUILD_TYPE=Release "-DPython_EXECUTABLE=$PWD/.venv/Scripts/python.exe"
cmake --build build/python
.\build\python\Vinc.exe --python .\.venv\Scripts\python.exe
```

需要 64 位元、有 GIL 的 CPython，與原生 SDK 使用的工具鏈／Runtime 相容；Windows 不使用 MinGW Python。
這不是 pip 套件：SDK 隨 Vinc 部署到建置目錄的 python/vinc。新增訊息定義須重新建置 SDK。
修改 python/modules 的 .py 後，建置會複製到 data/module；重新啟動 Vinc 後使用更新內容。
on_start 保存 Publisher／Subscriber，on_stop 明確 close；FrameworkLoop 派送訊息與指令。
Python module_interface 的 args 已移除實例名稱；推送失敗捕捉 VincError 並回傳 1，避免預期的指令失敗使 Module fault。

驗證命令（教學主文不要求讀者執行測試）：

```sh
ctest --test-dir build/python --output-on-failure
```

- Windows x64、MSVC 19.51.36257、CMake 4.3.2、Ninja、CPython 3.13.12：Debug／Release 建置成功，
  python.tutorials 各 1/1 通過。測試實際啟動中央與 Python 子程序，逐筆等待輸出，驗證 Hello 啟停、
  sequence 1／2／3、不同 PID、status、reset、錯誤命令／多餘參數不改變計數及正常 exit。
  等待有期限，失敗時只清理本次建立的程序樹。紀錄在各建置目錄 python-test.log。
- 本機原始 Python 的 VCRUNTIME140 14.42.34438 被 SDK 的 14.51.36244 最低基準拒絕。
  成功路徑使用既有隔離 CPython 副本（open-vinc/build/runtime-investigation/python），搭配 VS 提供的
  14.51.36247 Runtime；也以該副本建立的 .venv 跑通相同流程。未修改系統 Python 或固定框架。
  若遇 incompatible MSVC Runtime，依錯誤的實際 DLL 路徑修正部署；只更新系統 DLL 不一定能修正 Python 自帶舊副本。
- Python SDK 的 CI 尚未配置相容環境，Linux／macOS 未驗證。

## 運行中修改參數（2026-10-26）

新增獨立種類 `parameterPublisher`，實例仍叫 `sender`，搭配原有 `counterSubscriber`／`receiver`。
原本的 counterPublisher 不加入參數 API，維持前幾篇的入門程式。C++ 原始碼在 parameters/publisher.cpp，
由根目錄 add_subdirectory(parameters) 建置；Python 在 python/modules/parameterPublisher/。
兩種入口沿用現有建置目錄與 CounterSample 訊息，不變更固定框架。

先啟動 counterSubscriber，再啟動 parameterPublisher；等待 Started sender 與 step=1，逐筆操作：

```text
param get sender.step
sender send
param set sender.step 5
param get sender.step
sender send
sender send
exit
```

每次 send 等到實際接收輸出再繼續。set 之後先等 step=5，表示 Module 已更新本地設定。
預期 sequence 為 1、6、11。參數為 UInt64，預設 FrameworkOnly；on_change 轉交具名函式，
用 update 讀取快取。最後送出的 sequence 初始 0，成功 push 後才記錄新值；加法超出 UInt64 範圍時
回傳 1，不發送也不推進序號。step=0 允許重複目前序號；本篇只示範 1 與 5，不擴充參數驗證機制。
參數中央提交與 Module 套用並非同一事件，不以 param get 代替 Module 的 step 確認輸出。

本機實測：Windows x64、MSVC 19.51.36257、CMake 4.3.2、Ninja、相容 CPython 3.13.12：

- C++ Debug／Release 建置與既有 CTest 各 2/2 通過；另以真實中央 Shell 各執行一次參數流程：
  `.venv/Scripts/python.exe python/tests/smoke.py build/debug/Vinc.exe - build/debug/parameters-test.log parameters`，
  Release 改用 build/release。Python 在此僅為標準函式庫測試驅動器，C++ 建置與模組不需 Python SDK。
- Python Debug／Release 建置與 python.tutorials 各 1/1 通過，現涵蓋 hello、counter、parameters 三個情境。
- 兩種語言、兩種組態皆驗證序號 1／6／11、錯誤型別不改變 live value、UInt64 溢位拒絕發送、
  改回步進 1 後繼續發送，以及參數更新前後 sender PID 相同。所有等待有期限，最後正常 exit 並回收本次程序。
- 各建置目錄保留 parameters-test.log 或 python-test.log。不同組態的 Python 測試須依序執行，
  避免相同 VINC_NAME 的中央同時啟動；不修改框架的單實例防護。
- C++ Windows CI 增加參數 Shell 流程，測試驅動器使用 setup-python 3.13；遠端尚未執行。
  Python SDK 的遠端 CI、Linux／macOS 仍待驗證。參數保存與重啟的新增驗證見下方紀錄。

## 第一個 RPC（2026-10-26）

新增 `rpcPublisher`／`rpcSubscriber`，實例分別為 sender／receiver。C++ 位於 rpc/，由根目錄建置；
Python 位於 python/modules 的同名目錄。原有 counterPublisher、counterSubscriber 與 parameterPublisher
維持原樣。兩個 RPC Module 都使用 FrameworkLoop，Bus callback、RPC handler 與 completion 由框架派送，
沒有額外使用者執行緒或同步等待回覆的迴圈。

新增 messages/GetCountRequest.msg（無資料欄位）與 GetCountResponse.msg（uint64 received），
沿用原有 add_message_dir。Python 必須重新建置 SDK，才能使用新生成型別。
接收端在 on_start 登記 get_count 服務，由具名函式填入目前計數並回傳 RpcStatus.success()。
發送端的 sender count 非同步呼叫 receiver/get_count；本地接受不等於遠端成功，完成時才印出 RPC received=N。
登記失敗視為啟動失敗；本地呼叫失敗、completion 框架錯誤與應用非零狀態均有檢查，預期呼叫失敗不使 sender fault。
服務隨 Module 停止，不提供顯式取消註冊；on_stop 關閉 Publisher／Subscriber。

教學操作：先 rpcSubscriber，等 Started receiver，再 rpcPublisher，等 Started sender。
sender count 得到 RPC received=0；sender send 後等待實際接收 sequence=1，再 count 得到 1；
第二筆等待 sequence=2 再 count 得到 2。最後 exit。先等待 Bus 接收輸出，避免把尚未處理的訊息算入預期。

Windows x64、MSVC 19.51.36257、CMake 4.3.2、Ninja、相容 CPython 3.13.12 實測：

- C++ Debug／Release 建置成功，既有 CTest 各 2/2 通過；標準函式庫 Shell 驅動器各通過 parameters、rpc 情境：
  `.venv/Scripts/python.exe python/tests/smoke.py build/debug/Vinc.exe - build/debug/native-tutorials.log parameters rpc`，
  Release 改 build/release。驅動器不引入 C++ 建置或執行時的 Python SDK 相依。
- Python Debug／Release 建置成功，python.tutorials 各 1/1 通過，包含 hello、counter、parameters、rpc 四個情境。
- RPC 核對 0／1／2、重複查詢不改值、reset 後 0、下一筆後 1；目標尚未啟動時回報 NotFound，
  啟動目標後可再呼叫成功。額外參數／未知指令回傳 1；sender PID 在失敗與成功後保持相同，receiver 為不同 PID。
  各次查詢等候新完成輸出，所有等待有期限；最後檢查停止輸出與中央退出碼 0。
- C++ CI 的 Shell 步驟加入 RPC，遠端尚未執行。Python SDK 遠端 CI、Linux／macOS 和 C++↔Python 混合配對
  未在本輪驗證；本輪不修改框架、協定、工具鏈或系統 Python。

## 參數保存與重啟（2026-10-26）

參數教學在同一篇完成調整、param save、退出中央、重新啟動中央與兩個 Module、讀回設定的流程。
不另開保存教學，Module 原始碼與 SDK 用法無需更動。

- parameters 情境在測試開始時將 live step 設成 1，讓已存在其他保存值時仍可重跑；不改原始碼預設值。
  測試結束前設成 5，等 Module 回報 step=5，再執行 param save 並等 Parameters saved。
- 確認第一個中央正常退出後，建立第二個中央與全新 Module，使用同一建置目錄和 VINC_NAME。
  等 step=5，再用 param get 核對保存值，逐筆收到 sequence 5／10；接收計數重新從 0 累積至 2。
- 測試驅動器從 CMakeCache 的 VINC_NAME 定位本次建置的參數檔，保留原始檔案 bytes，
  等測試程序結束後原樣還原；原先不存在的檔案則只移除測試建立的該檔。無遞迴清理，不覆寫使用者原有設定。
- Windows x64／MSVC 19.51／CPython 3.13.12：C++ Debug／Release 的真實 Shell 驅動器各通過 parameters、rpc；
  Python Debug／Release 的 python.tutorials 各 1/1 通過，仍包含四情境，parameters 現在涵蓋兩次中央啟動。
  本輪只修改測試與文件，沿用已建置的相同執行檔；沒有重新編譯 Module 或 SDK。
- 各建置目錄的 native-tutorials.log／python-test.log 含 Parameters saved、RESTART AFTER PARAM SAVE、sequence 5／10。
  本機確認測試後原參數檔的 saved value 維持 1。遠端 CI、Linux／macOS 未驗證。

## 啟動腳本（2026-10-26）

新增 scripts/rpc-startup.tcl，依序執行 rpcSubscriber、rpcPublisher。兩種語言共用同一份 Tcl，
不修改任何 Module 或框架原始碼。每個啟動命令等 Ready；腳本完成後模組持續運行，最後由 Shell exit 正常關閉。
範例已部署 Tcl Runtime，修改這份腳本不需重新編譯。

從 repository 根目錄的 PowerShell 啟動：

```powershell
.\build\debug\Vinc.exe -S scripts/rpc-startup.tcl
.\build\python\Vinc.exe --python .\.venv\Scripts\python.exe -S scripts/rpc-startup.tcl
```

兩行為不同語言的替代操作；每次先結束前一個中央。所有中央 CLI 選項放在 -S 前面，後方是 Tcl 的 argv。
路徑相對工作目錄。也可先開沒有 -S 的中央，再於 Shell 輸入 srun scripts/rpc-startup.tcl。
等 Script completed: scripts/rpc-startup.tcl 後才輸入一般 Shell 命令，避免前景腳本期間輸入被忽略。

- startup 測試從 repository 根目錄使用相對路徑，真正透過 CLI -S 執行同一份檔案。
  完成後驗證 RPC received=0、發送 sequence=1、RPC received=1，以及不同 Module PID。
- 在已啟動的模組上重複 srun，驗證同名實例導致 Script error in ... (line 2)，原有 Module 仍可回覆數量 1。
  正常 exit 後再啟動新中央，以互動 srun 執行腳本，核對新數量 0、收訊後 1 與正常停止。
- Windows x64／MSVC 19.51／相容 CPython 3.13.12：C++ Debug／Release 的 parameters、rpc、startup 情境各通過；
  Python Debug／Release 的 python.tutorials 各 1/1 通過，包含 hello、counter、parameters、rpc、startup 五情境。
  本輪沿用既有二進位，不重建未修改的 Module／SDK。等待有期限，失敗只清理本次程序樹。
- native-tutorials.log／python-test.log 記錄 -S、重複執行錯誤與 INTERACTIVE SRUN。
  C++ CI 已納入 startup 情境；遠端 CI、Linux／macOS、內嵌腳本、取消及 Tcl 控制流程未在本輪驗證。

## 模組日誌（2026-10-26）

新增 logging/ 的 logPublisher／logSubscriber 與 python/modules 的同名版本，固定實例仍為 sender／receiver。
沿用 CounterSample、get_count RPC 與 FrameworkLoop；不更動原有 counter、parameters、rpc 範例或固定框架。
根目錄 CMake 建置兩個原生 Module；Python 建置照既有方式複製 .py 檔。
on_start 記錄 Info，接收 callback 記錄 Info，發送準備與 trace 記錄 Debug，未知 sender 命令記錄 Warn，
RPC 本地拒絕／完成失敗／應用非零狀態記錄 Error。Error 等級本身不使 Module fault。

兩個模組的具名 write_log helper 檢查 C++ Result／捕捉 Python VincError；寫入拒絕改用普通輸出提示，
不遞迴寫 Log、不把日誌失敗回傳成 hook 失敗。原有 ready／received／RPC／stopped 輸出保留，
與帶有來源與等級的結構化紀錄區分。成功寫入只代表本地接受，不宣稱必達或斷電保存。
on_stop 釋放 Publisher／Subscriber 並記錄停止，沒有額外使用者執行緒或檔案 handle。

操作：開啟全新中央後 log show on，依序 logSubscriber、logPublisher，等待各自 Started。
sender send、sender count 延續先前語意；sender trace 寫入 Debug 並印出 debug_enabled=0／1，
用來確認非同步的 log level sender debug 已套用。sender count missingReceiver 可示範預期 RPC 失敗，
之後 sender count 仍能取得真正 receiver 的回覆。log show warn 只顯示 Warn／Error；log show off 只關閉顯示。

Windows x64／MSVC 19.51.36257／CMake 4.3.2／Ninja／相容 CPython 3.13.12 實測：

- C++ Debug／Release 完成增量建置，既有 CTest 各 2/2 通過；真實 Shell 驅動器各通過
  parameters、rpc、startup、logging 四情境。記錄位於 build/debug/native-tutorials.log 與 Release 對應檔。
- Python Debug／Release 建置完成，python.tutorials 各 1/1 通過，包含 hello、counter、parameters、rpc、startup、logging 六情境。
- logging 核對初始 Info、單獨 log show debug 不產生來源已略過的 Debug、來源改 Debug 後的 trace／send，
  以及 Shell 改 Info／Warn 時隱藏較詳細等級。來源改 Warn 後，即使 Shell 顯示 Debug，來源 Info／Debug 仍略過。
  來源等級透過 enabled 輸出確認套用，不使用固定 sleep；同來源的後續可見紀錄作為顯示過濾檢查的等待依據。
- RPC 失敗有 Error，無效命令有 Warn，之後正常查詢仍成功。log show off 後仍可收訊、查詢與正常退出，
  且新的中央日誌檔包含關閉顯示後的 sequence=3、四個等級與 sender stopped。
  只讀取本次中央新增的日誌檔，不改寫或刪除既有日誌；所有程序等待有期限並清理本次程序樹。
- C++ CI 已加入 logging 情境；遠端 CI、Python SDK 遠端 CI、Linux／macOS、過載或磁碟故障未在本輪驗證。

## 入門函式註解（2026-10-27）

- C++／Python 的 Hello、Counter、Parameter、RPC、Log 共 16 份模組來源，補齊命名、啟動、指令與正常停止的註解。
  各 hook 開頭說明框架何時呼叫、應放入哪些工作，以及 {}／None 或 0／1 的回傳意義。
  訂閱、參數與 RPC 的函式另標示為 callback／handler，指出資料何時送達或如何填回覆；普通輔助函式也簡述責任。
- C++ 建構子說明固定實例名稱，REGISTER_MODULE 說明建立模組時使用的種類名稱。
  Python 明確說明 on_name 只負責命名，發布／訂閱放在 on_start；指令 args 不含實例名稱。
- 註解放在函式內第一行，讓網站擷取單一函式時一併帶入說明；維持具名處理函式，lambda 仍只轉交。
  後續新增教學函式，優先解釋呼叫時機、用途與回傳意義，避免逐行重述語法。
- 逐行對照原 commit：16 份來源只增加獨立註解行，所有非註解行原樣保留；8 份 Python 的 AST 完全一致。
  固定框架、訊息格式、API 與執行行為均未修改。網站的中英文對照由網站 repository 維護。
- Windows x64：C++ Debug／Release 增量建置成功，counter.lifecycle／counter.shell 各 2/2 通過；
  原生 Shell 的 parameters、rpc、startup、logging 四情境各通過。Hello 獨立入口 Debug／Release 建置及 hello.shell 各 1/1 通過。
- Python Debug／Release 建置與部署完成，python.tutorials 各 1/1 通過，包含六個教學情境。
  中文註解由網站顯示層套用，範例保留英文註解；未驗證 Linux／macOS、遠端 CI 或新增任何 Runtime 行為。

## 自訂訊息（2026-10-31）

- `messages/SensorReading.msg` 定義 `double temperature` 與 `string sensor`，供兩種語言共用。
  C++ 使用 `<vinc_messages/SensorReading.hpp>`／`vinc::SensorReading`，Python 使用 `vinc.messages.SensorReading`。
  `.msg` 不宣告欄位預設值；`T name = value` 是類別常數。生成結果不手動編輯。
- C++ 模組位於 `custom-message/`，根目錄 CMake 加入此子目錄。Python 新增 sensorPublisher／sensorSubscriber，
  沿用同一個 Python 入口、訊息目錄與部署規則。原計數、參數、RPC、日誌範例行為不變，框架仍固定 v0.1.2。
- 發送端以 `make_message` 建立本機訊息；數值直接賦值，字串透過 `assign("room")`，確認成功才 push。
  C++ 檢查 Result，Python 捕捉 VincError；錯誤指令回傳 1，不停止模組。
  接收端在具名 `on_message` 中讀取數值與文字（C++ `.get()`／`.str()`，Python 數值屬性／`.decode()`）。
  Publisher／Subscriber 都存成成員並於 on_stop 釋放，沒有使用者背景執行緒。
- 從專案根目錄重新建置 C++ 或 Python 入口。新增／修改訊息後 Python 也必須重建 SDK。
  先關閉上一個中央，再啟動對應 Vinc Shell；先執行 `sensorSubscriber` 等待 Started receiver，
  再執行 `sensorPublisher` 等待 Started sender。輸入 `sender send`，預期收到
  `received sensor=room temperature=23.5 publisher=sender`；再次 send 仍是相同讀值，最後 exit 正常停止。
- Windows x64／MSVC 19.51／CMake 4.3.2／Ninja：C++ Debug、Release 建置及既有 CTest 各 2/2 通過；
  `python/tests/smoke.py` 以原生 Shell 驅動 custom_message 情境，兩組態均通過。
  Python Debug、Release SDK 建置及 python.tutorials 各 1/1 通過，包含新增情境在內共七個情境。
  使用既有 CPython 3.13.12 環境；本輪未更動 Python 或 CRT 安裝。
- custom_message 情境檢查錯誤指令、兩次完整數值／字串接收、正常停止與中央退出。
  沿用每個等待最多 10 秒與 finally 清理程序的驅動器。C++ CI 增加此情境；遠端 CI、Linux／macOS 未於本輪驗證。
  本次範例先做本機 commit 供網站讀取不可變片段，尚未 push。
