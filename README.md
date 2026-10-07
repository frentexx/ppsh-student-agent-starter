# 屏北高中 學生 Agent 起步技能包

> 給屏北高中學生用的 AI Agent 技能（Skills），專門做兩件事：
> **① 領取上課用的 AI 點數（Token）　② 把專案準備好，讓 AI 每次都知道東西該放哪、上次做到哪。**
>
> 每個技能都是一份純文字說明書，AI 讀了就照著做——**不是程式，不需要會寫程式。**
> ✅ 適用：**Codex Desktop**、**Claude Code**
>
> 搭配教學網頁：👉 **[學生 Agent 入門簡報](https://frentexx.github.io/ppsh-student-agent-intro/)**

---

## 技能清單

| 技能 | 你怎麼叫它 | 用途 | 它會動到什麼 |
|---|---|---|---|
| `ppsh-stu-token` | 「領點數」「切換點數池」「換回個人設定」 | **引導你領取 NMKING 課程點數**、套用設定、確認真的接到專案點數池，下課後切回個人設定或換到另一個點數池 | 只引導，**不替你輸入密碼、不替你執行設定檔** |
| `ppsh-stu-init` | 「初始化專案」 | 為專案資料夾建立藍圖（`AGENTS.md`）、交接檔（`handoff.md`）、**`作業成果`資料夾**，並**檢查電腦環境**：有沒有 ComfyUI、有沒有生圖模型、能不能讀 PDF、能不能寫 Word | 建 3 個檔案＋資料夾；缺套件時**問你同意才安裝**；不下載模型 |
| `ppsh-stu-startup` | 「開工」 | 讀藍圖與交接檔，30 秒內告訴你上次做到哪、下一步是什麼、作業成果有幾個檔案 | 只讀，不改任何檔案 |
| `ppsh-stu-shutdown` | 「收工」 | 把今天做的事寫進交接檔，並提醒你生成的檔案是不是都放在 `作業成果` | 改寫 `handoff.md`；不搬動你的檔案 |
| `ppsh-stu-report` | 「寫學習歷程報告」 | 把 `作業成果` 的圖片、影片與對話歷程，整理成**符合高中學習歷程（課程學習成果）的 Word 報告**。你只要說幾句省思，AI 幫你寫成文章，**你同意了才寫進去** | 產生一份 .docx；對話紀錄會自動遮蔽金鑰與密碼 |

**所有技能都不碰 git、不上傳任何東西。**

### 一個專案的完整流程

```
領點數（ppsh-stu-token）→ 初始化專案（ppsh-stu-init）→ 開工 → 做作業 → 收工
                                                      ↑___________↓（每次上課重複）
全部做完 → 寫學習歷程報告（ppsh-stu-report）
```

---

## 學生看這裡

### 1. 領取點數（一句話版）

老師會給你一個**領取連結**，並**口頭告訴你班級密碼**。你在網頁上選「免登入領取」，依老師約定的格式填「識別名稱」（例如座號，**不要填姓名**），輸入班級密碼，下載**自己的**設定檔，套用後重新開啟 Codex、建立新任務就能用。

> 完整一步一步的帶領，請對 AI 說「**領點數**」，由 `ppsh-stu-token` 陪你做。

### 2. 三條安全規則

- **Token、設定檔、班級密碼不要貼到群組或給別人**，截圖要遮住 Token。
- **每個人用自己的設定，不交換。**
- 免登入領取**沒有復原碼**：不要換瀏覽器、不要清除瀏覽器資料。

### 3. 作業成果放哪

**你用 AI 做出來的圖片、影片、文件，一律放在專案資料夾的 `作業成果` 裡**（圖片、影片、文件各一個子資料夾）。專案初始化時，這條規則會寫進 `AGENTS.md`，AI 每次都會照做。

---

## 安裝：一段話交給 AI Agent

**不用打任何指令。** 打開 **Codex Desktop**，把下面這段話**整段複製、貼上、送出**，AI 要動到電腦時按「同意」即可。裝完請把 Codex **整個關掉再打開**。

```text
請讀取 https://github.com/frentexx/ppsh-student-agent-starter 的 README.md，
照其中「給 AI Agent 的安裝步驟」，幫我把這 5 個學生技能裝好。
我不熟指令：請你自己判斷、自己執行，需要我同意的地方跳出確認就好，不要叫我自己打指令。
全部做完後，用一張簡單的表告訴我結果，以及我接下來要做什麼。
```

**怎麼確認裝好了**：重開後問它「**你有哪些 ppsh-stu 開頭的技能？**」，列得出 5 個就成功了。

**裝到一半失敗**：不用自己修，把 AI 最後給你的結果表**截圖給老師**（截圖不要有 Token）。

---

## 給 AI Agent 的安裝步驟（學生不用看這段）

> 你正在幫一位**不熟指令**的高中生安裝技能。規則：
> - **所有指令由你執行**，不要叫學生自己打指令。
> - 會改動電腦的步驟（寫入技能資料夾）照你所在 Agent 的權限確認機制取得同意；只讀的檢查直接跑。
> - **不要讀取、索取或顯示任何金鑰或 Token**；這 5 個技能都不需要金鑰。
> - 某一步失敗就停在那一步，用白話說明卡在哪；**不要換成本文件以外的方法硬裝**。
> - 可重複執行：已經裝好的就跳過。

### 要裝的技能（5 個）

`ppsh-stu-token`、`ppsh-stu-init`、`ppsh-stu-startup`、`ppsh-stu-shutdown`、`ppsh-stu-report`

### 步驟 1：判斷你是哪個 Agent

| 你是 | 技能資料夾（Windows） | npx 的 `-a` |
|---|---|---|
| Codex Desktop | `%USERPROFILE%\.agents\skills\` | `codex` |
| Claude Code | `%USERPROFILE%\.claude\skills\` | `claude-code` |

Codex **不要用內建的 `$skill-installer`**（會裝到 `.codex\skills\`，不是個人技能資料夾）。只裝到**你自己**的資料夾。

### 步驟 2：安裝技能

**路線 A（`node --version` 有版本號時優先用）：**

```powershell
npx skills add frentexx/ppsh-student-agent-starter -s ppsh-stu-token ppsh-stu-init ppsh-stu-startup ppsh-stu-shutdown ppsh-stu-report -a <codex 或 claude-code> -g -y --copy
```

PowerShell 回「因為這個系統上已停用指令碼執行」→ 把 `npx` 改成 `npx.cmd` 重跑。

**路線 B（沒有 Node.js，或路線 A 失敗）：下載 ZIP 後複製**

```powershell
$tmp = Join-Path $env:TEMP "ppsh-student-agent-starter"
Invoke-WebRequest "https://github.com/frentexx/ppsh-student-agent-starter/archive/refs/heads/main.zip" -OutFile "$tmp.zip"
Expand-Archive "$tmp.zip" -DestinationPath $tmp -Force
$dst = "$env:USERPROFILE\.agents\skills"   # Claude Code 改成 "$env:USERPROFILE\.claude\skills"
New-Item -ItemType Directory -Force $dst | Out-Null
foreach ($s in 'ppsh-stu-token','ppsh-stu-init','ppsh-stu-startup','ppsh-stu-shutdown','ppsh-stu-report') {
  Copy-Item "$tmp\ppsh-student-agent-starter-main\skills\$s" $dst -Recurse -Force
}
```

### 步驟 3：確認檔案到位（只讀）

```powershell
$dir = "$env:USERPROFILE\.agents\skills"   # Claude Code 改成 "$env:USERPROFILE\.claude\skills"
foreach ($s in 'ppsh-stu-token','ppsh-stu-init','ppsh-stu-startup','ppsh-stu-shutdown','ppsh-stu-report') {
  "{0,-20} {1}" -f $s, (Test-Path "$dir\$s\SKILL.md")
}
foreach ($f in 'ppsh-stu-init\scripts\check_env.py','ppsh-stu-report\scripts\extract_history.py','ppsh-stu-report\scripts\build_report.py') {
  "{0,-46} {1}" -f $f, (Test-Path "$dir\$f")
}
```

8 行都要是 `True`。

### 步驟 4：不需要補任何環境

安裝本身**不需要** Python 套件。`ppsh-stu-init` 與 `ppsh-stu-report` 用到時才會檢查 Python 與 `python-docx`，缺的**那時再問學生同意**，這裡不要先裝。

### 步驟 5：回報

用一張表（技能名稱、成功／失敗）回報，最後用一句白話說：「請把 Codex 整個關掉再打開，然後問我『你有哪些 ppsh-stu 開頭的技能？』」。

---

## 尚待實機驗證

| 項目 | 狀態 |
|---|---|
| 技能在 Codex Desktop 的安裝與觸發 | 🟡 待實測 |
| Codex 會話紀錄（`~/.codex/sessions`）的欄位與位置，供 `ppsh-stu-report` 讀取 | 🟡 依公開資料撰寫，待實測；失敗時改由學生貼上對話 |
| 套用 NMKING 設定後，Codex 端確認提供者與點數池的畫面位置 | 🟡 待實測 |
| ComfyUI 連線位址（學校主機）與模型位置 | 🟡 待老師提供；可用環境變數 `COMFYUI_URL`、`COMFYUI_PATH` 指定 |

## 授權與來源

MIT 授權（見 `LICENSE`）。`ppsh-stu-init`、`ppsh-stu-startup`、`ppsh-stu-shutdown` 改作自同作者的
[ppsh-agent-skills](https://github.com/frentexx/ppsh-agent-skills)（教師版），改為學生用語並加入作業成果與環境檢查。
領取點數的步驟依 NMKING AI Gateway 分享者操作手冊 v2.6 整理，畫面以平台當下為準。
