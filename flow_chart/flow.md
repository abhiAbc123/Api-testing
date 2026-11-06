# api-test-e10 Execution Flowchart

This document is rendered using [Mermaid](https://mermaid.js.org/). Supported by VSCode, GitHub, Obsidian, Typora, and other Markdown viewers.

> For new task preflight gates, see `doc/preflight_gates_new.md`; for maintenance task preflight gates, see `doc/preflight_gates_maintenance.md`. The 5 new task creation modes are detailed in `doc/mode_capture_driven.md`, `doc/mode_reference_case.md`, `doc/mode_curl_manual.md`, `doc/mode_java_controller_source.md`, and `doc/mode_api_tpl.md`. The 4 maintenance modes are detailed in `doc/mode_maintenance_*.md`, with shared maintenance context in `doc/maintenance_prompt_context.md`. This file maintains flowcharts and decision logic.

---

## 1. Overview (Entry Flow)

```mermaid
flowchart TD
    Start([User triggers task]) --> ExceptCheck{Pure query / tool / diagnostics?}
    ExceptCheck -- Yes --> QuickAnswer[Respond directly with reminder:<br/>Formal authoring requires confirming New/Maintenance<br/>and submitting corresponding task info]
    ExceptCheck -- No --> P0[Preflight 0<br/>Run preflight_check.py]

    P0 --> P0Result{Index data<br/>available?}
    P0Result -- Date config error --> P0Fail[Echo error message<br/>Prompt user to fix config.json]
    P0Fail --> Start
    P0Result -- "Data fresh / auto-updated" --> T[Identify task type<br/>New / Maintenance]

    T --> TSig{Clear signals for<br/>New / Maintenance?}
    TSig -- Yes --> TAuto[Infer task type automatically<br/>New / Maintenance]
    TSig -- No --> TAsk[Ask user for task type<br/>Wait for confirmation of New / Maintenance]
    TAsk --> TRecv[Received user reply]

    TAuto --> Route{Task Type?}
    TRecv --> Route

    Route -- New --> ReadNew[Read and execute<br/>doc/preflight_gates_new.md]
    Route -- Maintenance --> ReadMaint[Read and execute<br/>doc/preflight_gates_maintenance.md]

    ReadNew --> NewInfo{All 5 new task items<br/>provided?}
    NewInfo -- No --> ARej[Reject: Return new task template<br/>Wait for user completion]
    ARej --> Start
    NewInfo -- Yes --> A2{"API Method File<br/>and Location<br/>both declare<br/>No new API for this case?"}

    A2 -- "Both declare No new API" --> NoNewApi["Record: No new API allowed<br/>Reuse existing APIs only"]
    A2 -- Both specify concrete values --> HasNewApi["Record: Allow adding new API<br/>at specified location"]
    A2 -- "Only one declares No new API" --> A2Rej["Reject: Both fields must declare together"]
    A2Rej --> Start

    NoNewApi --> NewMode{Creation mode determined?<br/>incl. auto-inference}
    HasNewApi --> NewMode
    NewMode -- Yes --> NewTodo[First Todo item:<br/>New + Mode N + 5 task items]
    NewMode -- No --> NewAsk[Ask creation mode per<br/>preflight_gates_new.md]
    NewAsk --> NewTodo

    ReadMaint --> MaintInfo{All 2 maintenance items<br/>provided?}
    MaintInfo -- No --> AMRej[Reject: Return maintenance template<br/>Wait for user completion]
    AMRej --> Start
    MaintInfo -- Yes --> MaintMode{Maintenance mode determined?<br/>incl. auto-inference}
    MaintMode -- Yes --> MaintTodo[First Todo item:<br/>Maintenance + Mode N + 2 task items]
    MaintMode -- No --> MaintAsk[Ask maintenance mode per<br/>preflight_gates_maintenance.md]
    MaintAsk --> MaintTodo

    NewTodo --> Dispatch{Task Type + Mode Dispatch}
    MaintTodo --> Dispatch
    Dispatch -- New-Mode 1 --> Flow1A[New Mode 1: Capture-Driven]
    Dispatch -- New-Mode 2 --> Flow2A[New Mode 2: Reference Case]
    Dispatch -- New-Mode 3 --> Flow3A[New Mode 3: Manual cURL]
    Dispatch -- New-Mode 4 --> Flow4A[New Mode 4: Controller Source]
    Dispatch -- New-Mode 5 --> Flow5A[New Mode 5: API-TPL Driven]
    Dispatch -- Maint-Mode 1 --> Flow1B[Maint Mode 1: Capture-Driven]
    Dispatch -- Maint-Mode 2 --> Flow2B[Maint Mode 2: Reference Case]
    Dispatch -- Maint-Mode 3 --> Flow3B[Maint Mode 3: Manual cURL]
    Dispatch -- Maint-Mode 4 --> Flow4B[Maint Mode 4: pytest Error-Driven]

    Flow1A --> Pytest[pytest Closed-Loop]
    Flow2A --> Pytest
    Flow3A --> Pytest
    Flow4A --> Pytest
    Flow5A --> Pytest
    Flow1B --> Pytest
    Flow2B --> Pytest
    Flow3B --> Pytest
    Flow4B --> Pytest

    Pytest --> Report[Output summary of methods & test cases<br/>+ Execution results]
    Report --> End([Completed])

    classDef reject fill:#f88,stroke:#c00,color:#000
    classDef pass fill:#8f8,stroke:#080,color:#000
    classDef wait fill:#fc8,stroke:#c80,color:#000
    class ARej,AMRej,A2Rej,P0Fail reject
    class NoNewApi,HasNewApi pass
    class TAsk,TRecv,ReadNew,ReadMaint,NewAsk,MaintAsk wait
```

---

## 2. Preflight 0 / New Preflight / Maintenance Preflight Decision Gates

```mermaid
flowchart LR
    Q1[User Request] --> G1{Is authoring task?}
    G1 -- No --> PassThru[Exempt Channel:<br/>Query / Tool / Diagnostics]
    G1 -- Yes --> G0[Run preflight_check.py]
    G0 --> G0R{Index data usable?}
    G0R -- No --> G0Fail[Echo error<br/>Wait for user fix]
    G0R -- Yes --> G1T{Task type clear?}

    G1T -- No --> AskType[Ask New / Maintenance]
    G1T -- Yes --> TypeRoute{Task Type?}
    AskType --> TypeRoute

    TypeRoute -- New --> ReadN[Read<br/>preflight_gates_new.md]
    TypeRoute -- Maintenance --> ReadM[Read<br/>preflight_gates_maintenance.md]

    ReadN --> NInfo{All 5 new items present?}
    NInfo -- No --> Ret1[Return new task template]
    NInfo -- Only one filled with no new API --> Ret2[Prompt to fill both]
    NInfo -- Yes --> NMode{Creation mode determined?}

    ReadM --> MInfo{All 2 maint items present?}
    MInfo -- No --> RetM[Return maint template]
    MInfo -- Yes --> MMode{Maint mode determined?}

    NMode -- Task has signals --> AutoN[Auto-infer creation mode]
    NMode -- No signals --> AskN[Creation mode menu]
    NMode -- User replied number --> TakeN[Adopt creation mode]

    MMode -- Task has signals --> AutoM[Auto-infer maint mode]
    MMode -- No signals --> AskM[Maint 4-option menu]
    MMode -- User replied number --> TakeM[Adopt maint mode]

    AutoN --> Go[Enter corresponding mode workflow]
    AskN --> Go
    TakeN --> Go
    AutoM --> Go
    AskM --> Go
    TakeM --> Go

    style G0Fail fill:#f88
    style Ret1 fill:#f88
    style RetM fill:#f88
    style Ret2 fill:#f88
    style AskType fill:#fc8
    style AskN fill:#fc8
    style AskM fill:#fc8
    style PassThru fill:#8cf
    style Go fill:#8f8
```

---

## 3. Overview of New Tasks (Entry to Mode Dispatch)

```mermaid
flowchart TD
    NStart([Enter New Task]) --> NeedGate{Has preflight_gates_new.md<br/>been read and executed?}
    NeedGate -- No --> ReadGate[Read new preflight gate first]
    NeedGate -- Yes --> Info
    ReadGate --> Info{All 5 new task items<br/>provided?}

    Info -- No --> AskInfo[Copy new task template<br/>Wait for user completion]
    AskInfo --> NStop([Halt])
    Info -- Yes --> ApiPair{"API Method File<br/>and Location<br/>both declare<br/>No new API for this case?"}

    ApiPair -- "Both declare No new API" --> NoNew[Record: No new API<br/>Reuse existing APIs only]
    ApiPair -- Both specify concrete values --> HasNew[Record: Allow adding new API<br/>at specified location]
    ApiPair -- "Only one declares No new API" --> RejectPair[Reject: Both fields must declare together]
    RejectPair --> NStop

    NoNew --> Mode{Creation mode determined?}
    HasNew --> Mode
    Mode -- Clear signals in task --> AutoMode[Auto-infer<br/>Modes 1-5]
    Mode -- User replied number --> TakeMode[Adopt user choice]
    Mode -- No --> AskMode[Copy creation mode menu<br/>Wait for user choice]
    AskMode --> TakeMode

    AutoMode --> ReadDocs[Read coding_style_guide.md<br/>+ corresponding mode_*.md]
    TakeMode --> ReadDocs
    ReadDocs --> Dispatch{Enter Creation Mode}
    Dispatch --> N1[New Mode 1: Capture-Driven]
    Dispatch --> N2[New Mode 2: Reference Case]
    Dispatch --> N3[New Mode 3: Manual cURL]
    Dispatch --> N4[New Mode 4: Controller Source]
    Dispatch --> N5[New Mode 5: API-TPL Driven]

    N1 --> VerifyN[pytest Closed-Loop]
    N2 --> VerifyN
    N3 --> VerifyN
    N4 --> VerifyN
    N5 --> VerifyN
    VerifyN --> NEnd([Creation Complete])

    classDef nWait fill:#fc8,stroke:#c80,color:#000
    classDef nPass fill:#8f8,stroke:#080,color:#000
    classDef nReject fill:#f88,stroke:#c00,color:#000
    class ReadGate,AskInfo,AskMode,ReadDocs nWait
    class NoNew,HasNew,N1,N2,N3,N4,N5,NEnd nPass
    class RejectPair nReject
```

### Key Principles for New Tasks

- Read `doc/preflight_gates_new.md` first and complete 5-item validation.
- `[fixture]` is optional; all other fields must contain real files, real locations, and complete descriptive case names.
- `[API Method File]` and `[API Method Location]` can both declare "No new API for this test case"; declaring only one must be rejected.
- When "No new API" is declared, only existing methods may be reused.
- Prompt with menu if mode is unconfirmed; auto-infer when signals are unambiguous.
- Read `doc/coding_style_guide.md` and the selected `doc/mode_*.md` before writing code.

---

## 4. New Creation Mode ①: Capture-Driven

```mermaid
flowchart TD
    F1Start([Mode 1 Entry]) --> NeedRestart{User mentioned<br/>restart capture service?}
    NeedRestart -->|Yes| Restart[restart.bat<br/>Stop 12138<br/>Wait 1s and restart]
    NeedRestart -->|No| Chk[check_capture_server.py]
    Restart --> ServiceInfo[Return self.baseurl<br/>self.prefixes<br/>self.jsonl_path]
    Chk -->|RUNNING exit=0| UI
    Chk -->|NOT_RUNNING exit=1| Start1[Background start<br/>start.bat]
    Start1 --> Wait1[Wait 2s]
    Wait1 --> ReChk[Re-check]
    ReChk -->|RUNNING| ServiceInfo
    ReChk -->|Still fails| Manual[Prompt user to<br/>double-click start.bat manually]
    Manual --> F1End([Terminate])
    Chk -->|PORT_OCCUPIED exit=2| Stop[Ask whether to run<br/>stop.bat to release port]
    Stop --> Chk

    ServiceInfo --> UI
    UI[Step 4: Prompt user for UI operations<br/>Browser proxy 127.0.0.1:12138<br/>Reply 'continue' when done]
    UI --> UserOp[User completes UI operations]
    UserOp --> Scan[Step 5: scan_page_api.py<br/>Incremental/full index refresh]
    Scan --> Match[Step 6: match_captures.py<br/>Generate capture_selection.md]

    Match --> Stop2[Step 7: AI pauses]
    Stop2 --> Tick[Wait for user checkboxes and reply 'checked']
    Tick --> Read[Step 8: Read capture_selection.md<br/>Review latest.jsonl]

    Read --> ConflictChk{Preflight A='No new API'<br/>but draft has new API checked?}
    ConflictChk -- Yes --> Reject1[Reject:<br/>Update Preflight A or uncheck new API]
    Reject1 --> End1([Terminate])
    ConflictChk -- No --> Landing[Step 8: Placement validation<br/>Recommend new API per pure_path<br/>Reuse implemented APIs per index<br/>Omit login/binary by default]
    Landing --> Analyze[Step 9: Analyze capture data<br/>Identify entrypoint / distinguish read vs write<br/>Trace main flow / determine dependencies]
    Analyze --> Design[Step 10: Design test cases<br/>Merge page load<br/>Isolate write actions<br/>Chain dependencies]
    Design --> Similar[Step 11: Similarity check<br/>Highly similar case exists?<br/>Ask whether to reuse/extend/parametrize]
    Similar --> Compose[Step 12: Write test cases<br/>Write methods and pytest cases per design<br/>Adhere to coding_style_guide.md]

    Compose --> Verify[Step 13: pytest Closed-Loop]
    Verify --> F1End2([Return to Overview])
```

### Mode ① Key Steps & Artifacts

| Step | Action | Artifact / Output |
|---|---|---|
| 1 | Check restart necessity | Check if user explicitly asked for capture restart |
| 2 | Handle capture service | Restart: `restart.bat`; Otherwise: inspect port and run `start.bat` as needed |
| 3 | Return service info | `self.baseurl` / `self.prefixes` / `self.jsonl_path` |
| 4 | Prompt for UI operations | Browser proxy and certificate guidance; reply "continue" when done |
| 5 | Refresh index | `tools/page_api_index.sqlite3` |
| 6 | Generate draft | `api_test_dwp_temp/capture_selection.md` |
| 7 | Wait for user selection | `[x]/[ ]` checkboxes; AI must halt |
| 8 | Read selection & validate placement | Process checked APIs only; validate new APIs vs preflight, reuse per index |
| 9 | Analyze capture data | Entry requests, read/write types, main flow, API dependencies |
| 10 | Design test cases | Merge page loads, separate write actions, chain dependencies |
| 11 | Similarity check | Suggestions for highly similar cases (reuse/extend/parametrize) |
| 12 | Write test cases | New methods to `[API Method File]`, cases to `[Test Case File]` |
| 13 | pytest closed-loop | Execution logs + pass/fail statistics |

---

## 5. New Creation Mode ②: Reference Existing Case

```mermaid
flowchart TD
    F2Start([Mode 2 Entry]) --> RefChk{User specified reference sample?}
    RefChk -- No --> AskRef[Ask:<br/>Please specify test function name or sample characteristics]
    AskRef --> RecvRef[Received reference]
    RecvRef --> Read1
    RefChk -- Yes --> Read1

    Read1[Read full reference case<br/>+ test class header]
    Read1 --> Read2[Check page_api_index.sqlite3<br/>Confirm method location of reference calls]
    Read2 --> A3Chk{Preflight A='No new API'?}

    A3Chk -- Yes --> Skip[Skip API deduplication]
    A3Chk -- No --> Diff[Determine if new URL needed<br/>from user business diffs]
    Diff -->|No new URL| Remind[Remind user to change Preflight A to<br/>'No new API for this test case']
    Remind --> End2([Halt for correction])
    Diff -->|Has new URL| Skip

    Skip --> Clone[Mimic test case<br/>Reuse step skeleton/params/assertions<br/>Retain self.xxx instance names<br/>Replace differentiating business parts]
    Clone --> Doc[Case docstring = Case Name]
    Doc --> Verify2[pytest Closed-Loop]
    Verify2 --> F2End([Return to Overview])
```

### Mode ② Key Principles (Forbidden Actions)

| Action | Allowed |
|---|---|
| Add capabilities not present in reference (e.g. grouping, sorting) | ❌ Forbidden |
| Complicate a simplified reference case | ❌ Forbidden |
| Add `@pytest.mark.skip` to new case | ❌ Unless requested as placeholder |
| Introduce API instances not in reference | ❌ Forbidden |
| Modify the reference case itself | ❌ Forbidden (unless requested) |

---

## 6. New Creation Mode ③: Manual cURL

```mermaid
flowchart TD
    F3Start([Mode 3 Entry]) --> CheckPair{Does each API have<br/>cURL + response body?}
    CheckPair -- No --> AskMiss[Ask for missing items]
    AskMiss --> Recv[Continue after completion]
    Recv --> Parse
    CheckPair -- Yes --> Parse

    Parse[Parse each cURL<br/>Method / URL / Headers / Body]
    Parse --> Strip[Strip hardcoded ETEAMSID<br/>timestamp / Referer / UA]
    Strip --> Dedup[Search index by pure_path]

    Dedup --> DedupBranch{Hit in index?}
    DedupBranch -- Yes --> Reuse[Reuse existing method]
    DedupBranch -- No --> NewApiChk{Preflight A='No new API'?}

    NewApiChk -- Yes --> Reject3[Reject:<br/>Update Preflight A or find existing substitute]
    Reject3 --> End3([Terminate])
    NewApiChk -- No --> NewApi[Add method at Preflight A location]

    Reuse --> Assemble
    NewApi --> Assemble
    Assemble[Assemble test case steps<br/>in cURL chronological order]

    Assemble --> Assert[Assert from response body<br/>code / structure / key fields / sort lists]
    Assert --> Verify3[pytest Closed-Loop]
    Verify3 --> F3End([Return to Overview])
```

### Mode ③ cURL Processing Checklist

| cURL Element | Handling |
|---|---|
| `-X GET/POST/PUT/DELETE` | Pass as method argument of API method |
| `--url "https://host/api/xxx?a=1"` | Split pure_path + query parameters |
| `-H "Cookie: ETEAMSID=xxxx"` | Remove hardcoded cookie, acquire dynamically via login fixture |
| `-H "Content-Type: application/json"` | Retain |
| `-H "Referer: ..."` / `-H "User-Agent: ..."` | Remove, do not write to method |
| `-d '{"a":1,"timestamp":...}'` | Replace `timestamp/_t` with dynamic generation at call time |
| `--data-urlencode` | Encode into payload form |

---

## 7. New Creation Mode ④: Java Controller Source Reference

```mermaid
flowchart TD
    F4Start([Mode 4 Entry]) --> Source{Controller source code<br/>or Jacoco URL provided?}
    Source -- No --> AskSource[Ask for source file / Markdown / Jacoco URL]
    AskSource --> SourceRecv[Received source info]
    Source -- Yes --> Analyze
    SourceRecv --> Analyze

    Analyze[Run analyze_java_controller.py<br/>Extract mapping & deduplicate by api_url+method]
    Analyze --> Draft[Generate java_sourceCode_analysisResult.md<br/>Uncovered APIs checked x by default<br/>Scenario groupings editable]
    Draft --> StopDraft[AI pauses<br/>Wait for user adjustment of checkboxes and groups]
    StopDraft --> Confirm[User confirms to proceed with draft]

    Confirm --> ReadDraft[Re-read adjusted draft<br/>Process retained checked endpoints and scenarios only]
    ReadDraft --> Design[Design test cases per call chain and business flow<br/>Document inference rationale]
    Design --> Ref[Find similar existing cases<br/>or read user-specified reference]
    Ref --> Landing{Is test case file _CSC.py?}
    Landing -- Yes --> UseCSC[Write directly to dedicated file]
    Landing -- No --> RemindCSC[Remind once to suggest _CSC.py<br/>Proceed with user choice if insisted]
    RemindCSC --> UseUserFile[Proceed with user-specified file]

    UseCSC --> Compose[Add/reuse API methods<br/>Write basic assertions + print full response]
    UseUserFile --> Compose
    Compose --> Run1[First pytest run<br/>Obtain actual response]
    Run1 --> Assert[Complete assertions based on actual response]
    Assert --> Retry{Debug iterations < 3?}
    Retry -- Yes --> Verify[pytest Closed-Loop]
    Verify --> Result{Passed?}
    Result -- Yes --> F4End([Return to Overview])
    Result -- No --> Retry
    Retry -- No --> Stop3[Halt further attempts<br/>Summarize failure causes (payload / variables / auth / env)]
    Stop3 --> F4End
```

### Mode ④ Key Steps & Artifacts

| Step | Action | Artifact / Output |
|---|---|---|
| 1 | Read Controller/Jacoco | Java source, line numbers, Jacoco coverage colors |
| 2 | Extract APIs & deduplicate | Combine class + method mappings, query `page_api_index.sqlite3` |
| 3 | Generate editable draft | `api_test_dwp_temp/java_sourceCode_analysisResult.md` |
| 4 | User adjusts draft | Check APIs, reorganize scenarios, add reference notes |
| 5 | Design test cases | Split by call chains; do not dump all `[x]` APIs into one monolithic case |
| 6 | Reference existing cases | AI searches or user specifies reference cases for fixtures/assertions |
| 7 | Author `_CSC.py` test cases | Remind once if not `_CSC.py`; user choice honored |
| 8 | Two-stage assertions | Basic assertions + print response first, then complete real assertions |
| 9 | pytest closed-loop | Up to 3 debug iterations; summarize causes and halt if unresolved |

---

## 8. New Creation Mode ⑤: API-TPL Driven

```mermaid
flowchart TD
    F5Start([Mode 5 Entry]) --> ReadMode[Read doc/mode_api_tpl.md<br/>+ coding_style_guide.md<br/>+ preflight_gates_new.md]
    ReadMode --> Landing{Does api-landing.md exist?}
    Landing -- No --> Export[export-report-artifacts<br/>Export landing package from ai-result]
    Export --> Landing2{Exists after export?}
    Landing2 -- No --> AskLanding[Reject: Provide run directory<br/>or complete analysis report first]
    AskLanding --> F5End0([Terminate])
    Landing2 -- Yes --> ReadLanding
    Landing -- Yes --> ReadLanding

    ReadLanding[Read api-landing.md only<br/>Forbidden to load entire ai-result.md<br/>Forbidden to use functional-cases.html]
    ReadLanding --> Checked{Are there manually checked<br/>x API-TPL entries?}
    Checked -- No --> RejectNone[Reject: Unchecked items must not be created<br/>Remain pending approval]
    RejectNone --> F5End1([Terminate])
    Checked -- Yes --> Scope[Step 0: Process x entries only<br/>Record id/method/path/params<br/>trigger_steps/related_tc]

    Scope --> MaintSkip{Is Mode 4 maintenance section<br/>completely unchecked?}
    MaintSkip -- Yes --> SkipMaint[Skip maintenance<br/>Zero changes to existing cases]
    MaintSkip -- No --> NoteMaint[Maintenance items follow Mode 4 separately<br/>Do not handle in Mode 5]
    SkipMaint --> Loop
    NoteMaint --> Loop

    Loop[Process each API-TPL-x] --> L1[Step 1: L1 Deduplication<br/>page_api_index.sqlite3<br/>api_url + method]
    L1 --> ParamMatch{Path contains param placeholder?}
    ParamMatch -- Yes --> Fuzzy[Multi-segment fuzzy match<br/>Literal segments must match]
    ParamMatch -- No --> Exact[Structural path match]
    Fuzzy --> Hit{Index hit?}
    Exact --> Hit

    Hit -- Yes --> Reuse[Reuse existing method<br/>Write real path for URL<br/>Do not recreate]
    Hit -- No --> Place[Step 2: Determine placement<br/>placement_hints / module directory]
    Place --> NewMethod[Step 3: Add page_api method<br/>coding_style_guide structure]
    NewMethod --> Trigger{docstring contains<br/>Trigger Steps?}
    Trigger -- No --> FixTrigger[Add Trigger Steps<br/>Source: TPL.trigger_steps / related_tc]
    FixTrigger --> Trigger
    Trigger -- Yes --> CaseWrite
    Reuse --> NeedTrigger{Reused method lacks<br/>Trigger Steps?}
    NeedTrigger -- Yes --> FixTrigger2[Add Trigger Steps]
    FixTrigger2 --> CaseWrite
    NeedTrigger -- No --> CaseWrite

    CaseWrite[Step 4: Author pytest test case<br/>Use established fixture add_form_data<br/>Title must have semantic note]
    CaseWrite --> TitleOk{Case docstring has<br/>semantic note?}
    TitleOk -- No --> FixTitle[Add verification description]
    FixTitle --> TitleOk
    TitleOk -- Yes --> Discipline{Fake green / skip / invented params?}
    Discipline -- Yes --> RejectBad[Reject for correction]
    RejectBad --> CaseWrite
    Discipline -- No --> Pytest[Step 5: pytest Closed-Loop<br/>test_case + PYTHONPATH=.]

    Pytest --> Pass{Passed?}
    Pass -- No --> FixReal[Fix method/assertions from real response<br/>Green before removing debug prints]
    FixReal --> Pytest
    Pass -- Yes --> Clean[Delete debug prints<br/>Recommend re-run to confirm]
    Clean --> More{More unprocessed<br/>API-TPL-x?}
    More -- Yes --> Loop
    More -- No --> ScanIdx[Step 6: Refresh page_api_index]
    ScanIdx --> Deliver[Step 7: Output summary of methods/cases<br/>pytest results / Forbidden to commit push]
    Deliver --> F5End([Return to Overview])

    classDef f5wait fill:#fc8,stroke:#c80,color:#000
    classDef f5pass fill:#8f8,stroke:#080,color:#000
    classDef f5reject fill:#f88,stroke:#c00,color:#000
    class AskLanding,RejectNone,RejectBad,FixTrigger,FixTrigger2,FixTitle,FixReal f5wait
    class F5End,Deliver,Reuse,NewMethod f5pass
    class F5End0,F5End1 f5reject
```

### Mode ⑤ Key Steps & Artifacts

| Step | Action | Artifact / Output |
|---|---|---|
| 0 | Confirm checked scope | Only process `[x]` `API-TPL-*` in `api-landing.md`; record method/path/params/`trigger_steps`/`related_tc` |
| 1 | L1 deduplication | `tools/page_api_index.sqlite3`; `{param}` **multi-segment fuzzy match** |
| 2 | Placement | `placement_hints` / module page_api; write real path when `{param}` matches |
| 3 | Author/reuse page_api | Standard structure per `coding_style_guide.md`; docstring must include **`Trigger Steps:`** |
| 4 | Author pytest cases | Established fixtures (e.g. `add_form_data`); case title **`--` semantic note**; no skip/fake green |
| 5 | pytest closed-loop | `test_case` + `PYTHONPATH=.`; fix based on real responses; clean debug prints after green |
| 6 | Refresh index | Update `page_api_index.sqlite3` |
| 7 | Stop and deliver | Methods/cases list + pytest results; **Forbidden to run git commit / push** |

### Mode ⑤ Key Principles (Forbidden Actions)

| Action | Allowed |
|---|---|
| Process unchecked `[ ]` API-TPLs | ❌ Forbidden |
| Load entire `ai-result.md` for Mode 5 | ❌ Forbidden (use `api-landing.md` only) |
| Use `functional-cases.html` to write automation | ❌ Forbidden |
| Fabricate URLs, parameter names, or irrelevant trigger steps | ❌ Forbidden |
| Method missing `Trigger Steps:` or case title lacking semantic note | ❌ Incomplete Deliverable |
| Write Mode 5 flow into Mode 4 / modify Mode 4 docs | ❌ Forbidden |
| Retain debug `print` statements after passing | ❌ Forbidden |
| Execute `git commit` / `git push` | ❌ Forbidden |

---

## 9. Overview of Maintenance Tasks (Entry to Mode Dispatch)

```mermaid
flowchart TD
    MStart([Enter Maintenance Task]) --> NeedCtx{Has maintenance_prompt_context.md<br/>been read?}
    NeedCtx -- No --> ReadCtx[Read maintenance prompt context first]
    NeedCtx -- Yes --> MT
    ReadCtx --> MT[Lock maintenance target<br/>Case / Method / Workflow]

    MT --> Scope{Is change scope clear?}
    Scope -- No --> AskScope[Ask for affected APIs<br/>reference sample / capture / cURL / diffs]
    AskScope --> MT2[Complete maintenance info]
    Scope -- Yes --> TMode{Is maint mode determined?}
    MT2 --> TMode

    TMode -- No --> AskMode[Copy 4-option menu<br/>Wait for user selection]
    TMode -- Yes --> RunMode[Enter maintenance mode dispatch]
    AskMode --> RunMode

    RunMode --> M1[Maint Mode 1: Capture-Driven]
    RunMode --> M2[Maint Mode 2: Reference Case]
    RunMode --> M3[Maint Mode 3: Manual cURL]
    RunMode --> M4[Maint Mode 4: pytest Error-Driven]

    M1 --> VerifyM[Minimal regression pytest]
    M2 --> VerifyM
    M3 --> VerifyM
    M4 --> VerifyM

    VerifyM --> MEnd([Maintenance Complete])

    classDef mWait fill:#fc8,stroke:#c80,color:#000
    classDef mPass fill:#8f8,stroke:#080,color:#000
    class AskScope,AskMode,ReadCtx mWait
    class RunMode,M1,M2,M3,M4,MEnd mPass
```

### Key Principles for Maintenance Tasks

- Search existing implementations first; do not assume new creation.
- Distinguish "case only" vs "method + case updates".
- Prioritize capture backtracking for broad changes, and reference samples or cURL for targeted changes.
- For pytest error-driven maintenance, default to `/test-fixing` first, using `/Debugging` only when stack or API context is unclear.
- Adding methods during maintenance is a fix mechanism, not the task objective.
- Run minimal regression on affected test cases; do not execute full test suite by default.

---

## 10. Maintenance Mode ①: Capture-Driven

```mermaid
flowchart TD
    M1Start([Maint Mode 1 Entry]) --> ScopeChk{Affected scope clear?}
    ScopeChk -- No --> AskScope[Ask for affected APIs / cases / flow / diffs]
    AskScope --> ScopeRecv[Received maintenance scope]
    ScopeChk -- Yes --> ServiceChk{Is capture service running?}
    ScopeRecv --> ServiceChk

    ServiceChk -- No --> Boot[Check / Start / Restart capture service]
    Boot --> UI[Retrace latest flow and complete UI actions]
    ServiceChk -- Yes --> UI

    UI --> Capture[Read latest.jsonl<br/>Refresh index and draft if needed]
    Capture --> Compare[Compare with existing implementation<br/>Index reuse / patch modification]
    Compare --> Point[Pinpoint changes<br/>Asserts only / params only / method+case / replacement method]
    Point --> Scenario[Patch existing cases by business scenario]
    Scenario --> Verify[Minimal regression pytest]
    Verify --> M1End([Maintenance Complete])

    classDef m1wait fill:#fc8,stroke:#c80,color:#000
    classDef m1pass fill:#8f8,stroke:#080,color:#000
    class AskScope,ScopeRecv,ServiceChk,Boot,UI,Capture,Compare,Point m1wait
```

### Maintenance Mode ① Key Steps & Artifacts

| Step | Action | Artifact / Output |
|---|---|---|
| 1 | Lock scope | Affected APIs, cases, workflows, diffs |
| 2 | Check capture service | Start / restart / verify active service |
| 3 | Acquire latest flow | `latest.jsonl`, index and draft if needed |
| 4 | Compare with implementation | Reusable methods, patchable methods, affected cases |
| 5 | Pinpoint changes | Assertions / parameters / fixtures / calls / replacement methods |
| 6 | Patch by business scenario | Minimal localized repairs to existing cases |
| 7 | Minimal regression | Execute pytest on affected test cases |

---

## 11. Maintenance Mode ②: Reference Existing Case

```mermaid
flowchart TD
    M2Start([Maint Mode 2 Entry]) --> RefChk{Reference sample provided?}
    RefChk -- No --> AskRef[Ask for reference sample function name / path]
    AskRef --> RefRecv[Received reference sample]
    RefChk -- Yes --> RefRead[Read full reference case<br/>+ test class header]
    RefRecv --> RefRead

    RefRead --> IndexChk[Check page_api_index.sqlite3<br/>Confirm methods called by reference]
    IndexChk --> DiffChk{Affects test case only?}
    DiffChk -- No --> MethodChk[Compare existing methods with index<br/>Determine if method should be modified]
    DiffChk -- Yes --> Patch[Minimal patch maintenance<br/>Assertions / params / fixture / calls]
    MethodChk --> Patch

    Patch --> Keep[Retain shared skeleton and self.xxx instances]
    Keep --> Verify[Minimal regression pytest]
    Verify --> M2End([Maintenance Complete])

    classDef m2wait fill:#fc8,stroke:#c80,color:#000
    classDef m2pass fill:#8f8,stroke:#080,color:#000
    class AskRef,RefRecv,RefRead,IndexChk,DiffChk,MethodChk m2wait
```

### Maintenance Mode ② Key Principles (Forbidden Actions)

| Action | Allowed |
|---|---|
| Add capabilities not in reference (e.g. grouping, sorting) | ❌ Forbidden |
| Turn local fixes into complex refactors | ❌ Forbidden |
| Attach `@pytest.mark.skip` to maintained cases | ❌ Unless requested as placeholder |
| Introduce API instances not in reference | ❌ Forbidden |
| Modify the reference case itself | ❌ Forbidden (unless requested) |

---

## 12. Maintenance Mode ③: Manual cURL

```mermaid
flowchart TD
    M3Start([Maint Mode 3 Entry]) --> Pair{Does each API have<br/>cURL + response body?}
    Pair -- No --> AskPair[Ask for missing cURL or response body]
    AskPair --> PairRecv[Continue after completion]
    PairRecv --> Parse
    Pair -- Yes --> Parse

    Parse[Parse each cURL<br/>Method / URL / Headers / Body]
    Parse --> SmallChk{Clear changes in 1-2 APIs only?}
    SmallChk -- No --> Redirect[Suggest switching to capture-driven<br/>or reference case]
    SmallChk -- Yes --> Compare[Compare with existing methods<br/>Identify reuse / patch / substitute]

    Compare --> Patch[Targeted patching of cases / asserts / params / calls]
    Patch --> Assert[Rewrite assertions against real responses]
    Assert --> Verify[Minimal regression pytest]
    Verify --> M3End([Maintenance Complete])

    classDef m3wait fill:#fc8,stroke:#c80,color:#000
    classDef m3pass fill:#8f8,stroke:#080,color:#000
    class AskPair,PairRecv,Redirect m3wait
```

### Maintenance Mode ③ cURL Processing Checklist

| cURL Element | Handling |
|---|---|
| `-X GET/POST/PUT/DELETE` | Pass as method argument of API method |
| `--url "https://host/api/xxx?a=1"` | Split pure_path + query parameters |
| `-H "Cookie: ETEAMSID=xxxx"` | Remove hardcoded cookie, acquire dynamically via login fixture |
| `-H "Content-Type: application/json"` | Retain |
| `-H "Referer: ..."` / `-H "User-Agent: ..."` | Remove, do not write to method |
| `-d '{"a":1,"timestamp":...}'` | Replace `timestamp/_t` with dynamic generation at call time |
| `--data-urlencode` | Encode into payload form |

---

## 13. Maintenance Mode ④: pytest Error-Driven

```mermaid
flowchart TD
    M4Start([Maint Mode 4 Entry]) --> Target{Case file + target case<br/>provided?}
    Target -- No --> AskTarget[Return maintenance 2-item template]
    Target -- Yes --> ReadTarget[Read full target case<br/>+ test class header / fixture / imports]

    ReadTarget --> BuildCmd[Assemble minimal pytest command<br/>File + function / -k keyword]
    BuildCmd --> RunPytest[Run pytest]
    RunPytest --> Result{Result?}
    Result -- PASS --> M4End([No fix needed or passed])
    Result -- FAIL --> LastErr[Extract final pytest interruption error only<br/>traceback / assertion diff / exception]
    LastErr --> Analyze[Thorough analysis of final error<br/>import / fixture / assert / response / return layer]
    Analyze --> Classify{Classification?}

    Classify -- Functional BUG --> Bug[Stop modifying case<br/>Return failing API / request info / response summary<br/>Report to dev]
    Classify -- Ambiguous --> Unknown[Do not modify case<br/>Compile UI reproduction steps & verification items<br/>Wait for user confirmation]
    Classify -- Test Case Needs Maint --> TestFix[Prefer /test-fixing<br/>Apply minimal patch by error category]

    TestFix --> NeedDebug{Maintenance difficult<br/>or call stack ambiguous?}
    NeedDebug -- No --> Patch[Minimal patch to target case<br/>and API method if necessary]
    NeedDebug -- Yes --> Debug[Switch to /Debugging<br/>Set breakpoint at failure or critical call<br/>Inspect stack / locals / payload / response]
    Debug --> Patch
    Patch --> RunPytest

    classDef m4wait fill:#fc8,stroke:#c80,color:#000
    classDef m4pass fill:#8f8,stroke:#080,color:#000
    classDef m4reject fill:#f88,stroke:#c00,color:#000
    class AskTarget,ReadTarget,BuildCmd,RunPytest,LastErr,Analyze,Classify,TestFix,NeedDebug,Debug m4wait
    class M4End,Patch m4pass
    class Bug,Unknown m4reject
```

### Maintenance Mode ④ Execution Checklist

| Step | Action | Artifact / Output |
|---|---|---|
| 1 | Lock target | `[Test Case File]` + `[Test Case Location]` |
| 2 | Read context | Target case, class header, fixture, imports, instances |
| 3 | Run pytest | Minimal scope command, execution directory, PYTHONPATH |
| 4 | Extract final error | Final pytest traceback, assertion diff, or exception |
| 5 | Categorize | Functional BUG: stop and report; Ambiguous: return reproduction steps; Maintenance: proceed to fix |
| 6 | Prefer `/test-fixing` | Apply minimal patch following test repair process |
| 7 | Fallback `/Debugging` | Breakpoint inspection when context/stack is unclear |
| 8 | Loop verification | Re-run same minimal pytest until passing or reclassified |

---

## 14. pytest Closed-Loop (Shared across All Modes)

```mermaid
flowchart TD
    V0([Authoring / Maint Complete]) --> Enc[UTF-8 Validation + py_compile]
    Enc --> Cwd[Change working directory<br/>paths.pytest_workdir]
    Cwd --> Env[Set PYTHONPATH<br/>pytest.pythonpath]
    Env --> Run[Execute pytest]

    Run --> Result{Result?}
    Result -- PASS --> Rep[Output summary of methods & cases<br/>+ pass statistics]
    Result -- FAIL --> Diag[Failure Diagnosis Priority]

    Diag --> D1{ModuleNotFoundError?}
    D1 -- Yes --> FixImport[Fix sys.path / PYTHONPATH]
    FixImport --> Run
    D1 -- No --> D2{Mojibake / Encoding?}
    D2 -- Yes --> FixEnc[Rewrite in UTF-8]
    FixEnc --> Run
    D2 -- No --> D3{fixture / decorator?}
    D3 -- Yes --> FixFix[Adjust fixture or skip]
    FixFix --> Run
    D3 -- No --> D4{Auth / token?}
    D4 -- Yes --> FixAuth[Re-authenticate login fixture]
    FixAuth --> Run
    D4 -- No --> D5{Assertion mismatch?}
    D5 -- Yes --> FixAsr[Rewrite assertions from real response]
    FixAsr --> Run
    D5 -- No --> D6{payload structure?}
    D6 -- Yes --> FixPl[Fix payload]
    FixPl --> Run
    D6 -- No --> D7[Environment / Network Issue<br/>Report to user]
    D7 --> Rep

    Rep --> End([Finished])
```

---

## 15. Mode Comparison Matrix

| Dimension | Mode 1 Capture | Mode 2 Reference | Mode 3 cURL | Mode 4 Controller Source | Mode 5 API-TPL |
|---|---|---|---|---|---|
| Typical Scenario | Multiple new APIs / complex workflow | Batch authoring similar cases / params | Capture unavailable / excessive data | Backend defined APIs without test coverage | git-diff-analyse gaps / checked templates |
| Preparation Cost | Low (UI operation only) | Medium (specify reference) | High (collect cURL + response) | Medium (provide Controller/Jacoco) | Medium (run analysis + check api-landing) |
| New API Capability | ✅ Index-driven deduplication | ⚠️ No new API by default; create if needed | ✅ Create per cURL | ✅ Extract from source & deduplicate | ✅ Deduplicate per TPL & create/reuse |
| AI Judgment | Low (index + draft) | Medium (understand reference) | Medium (understand cURL semantics) | Medium-High (design call chains & scenarios) | Low (template-driven) |
| Most Common Failure | Auth / browser proxy | Incorrect reference sample | Incomplete cURL / missing response | Payload/variables not determined from source | Creating unchecked items / missing trigger steps |
| Closed-Loop Strictness | Strong (pause on draft) | Strong (read reference) | Strong (cURL+response paired) | Strong (pause on draft, up to 3 debug runs) | Strong (checked only, real green, no commit) |

### Maintenance Mode Matrix

| Dimension | Maint Mode 1 Capture | Maint Mode 2 Reference | Maint Mode 3 cURL | Maint Mode 4 pytest |
|---|---|---|---|---|
| Typical Scenario | Multi-API / multi-case workflow change | Localized patch to single/similar cases | Targeted fix for 1-2 APIs | Direct fix based on failed test errors |
| Preparation Cost | Medium (latest flow) | Low (reference sample) | Medium (cURL + response) | Low (target test case) |
| Flow Tracing | Strong (trace latest flow) | Medium (reference-dependent) | Weak (best for explicit diffs) | Medium (inferred from error) |
| Granularity | Workflow level | Test case level | Endpoint / local level | Failure point level |
| Most Common Failure | Incomplete capture scope | Incorrect reference sample | Incomplete response/diffs | Non-code issues (env/auth), or ambiguous stack |
| Closed-Loop Strictness | Strong (minimal regression) | Strong (target case regression) | Strong (affected case regression) | Strong (same target pytest loop) |

---

## 16. Mapping between Flowchart and SKILL.md

| Flowchart Section | SKILL.md Section |
|---|---|
| 1. Overview | 🚨 Preflight Gates (New / Maintenance Dispatch) |
| 2. Decision Gates | Preflight 0 + `preflight_gates_new.md` / `preflight_gates_maintenance.md` |
| 3. Overview of New Tasks | `doc/preflight_gates_new.md` + new mode documents |
| 4. New Mode ① | `doc/mode_capture_driven.md` |
| 5. New Mode ② | `doc/mode_reference_case.md` |
| 6. New Mode ③ | `doc/mode_curl_manual.md` |
| 7. New Mode ④ | `doc/mode_java_controller_source.md` |
| 8. New Mode ⑤ | `doc/mode_api_tpl.md` |
| 9. Overview of Maintenance Tasks | `doc/maintenance_prompt_context.md` + maintenance mode documents |
| 10. Maintenance Mode ① | `doc/mode_maintenance_capture_driven.md` |
| 11. Maintenance Mode ② | `doc/mode_maintenance_reference_case.md` |
| 12. Maintenance Mode ③ | `doc/mode_maintenance_curl_manual.md` |
| 13. Maintenance Mode ④ | `doc/mode_maintenance_pytest_driven.md` |
| 14. pytest Closed-Loop | Core Principles → 5. Tests Must Form a Closed Loop |
| 15. Comparison Matrix | Shared specifications across all modes |
| Appendix A. Hook Sequence | 🚨 Preflight 0 (hook auto-execution) + `.claude/settings.json` `hooks.PreToolUse` |

---

## 17. Maintenance Notes

- This document maintains **two-way consistency** with `SKILL.md`: update both sides synchronously when workflows change.
- Mermaid syntax prioritizes compatibility with GitHub and VSCode Mermaid extensions.
- To export diagrams as images, use [Mermaid Live Editor](https://mermaid.live/).

---

## Appendix A: PreToolUse Hook Sequence Diagram

Describes how Claude Code intercepts `Skill({skill: "api-test-e10"})`, spawns `preflight_hook.py`, and injects `preflight_check.py` output into the AI context.

> Implementation: `hooks/preflight_hook.py` + project `.claude/settings.json` `hooks.PreToolUse.matcher="Skill"`.

```mermaid
sequenceDiagram
    autonumber
    participant AI as AI (Claude)
    participant CC as Claude Code Harness
    participant HK as preflight_hook.py
    participant PF as preflight_check.py
    participant FS as config.json / sqlite index

    Note over AI,CC: User triggers task -> AI decides to invoke Skill tool

    AI->>CC: Skill({skill: "api-test-e10"})
    Note over CC: Intercept tool call<br/>Check settings.json<br/>Match matcher: "Skill"

    CC->>HK: Spawn subprocess<br/>cwd=Session CWD<br/>stdin=JSON{tool_name, tool_input.skill, cwd, ...}
    activate HK

    HK->>HK: Read stdin and parse tool_input.skill

    alt skill != "api-test-e10"
        HK-->>CC: exit 0 (no stdout output)
        Note over CC: Pass-through<br/>Does not affect other skills
    else skill == "api-test-e10"
        HK->>PF: subprocess.run(preflight_check.py)<br/>PYTHONIOENCODING=utf-8<br/>timeout=120s
        activate PF
        PF->>FS: Read config.json.apiDataUpdateDate
        FS-->>PF: Date string

        alt delta <= 7 days
            PF-->>HK: stdout: "Database API data is up to date within one week..."<br/>exit 0
        else delta > 7 days
            PF->>FS: Call scan_page_api.py incremental scan
            FS-->>PF: New API list
            PF-->>HK: stdout: [scan_page_api] recent_new_methods<br/>exit 0
        else Invalid date / future date
            PF-->>HK: stdout: Error notice<br/>exit 1
        end
        deactivate PF

        HK->>HK: Construct JSON: {hookSpecificOutput:<br/> {hookEventName, additionalContext}}
        HK-->>CC: stdout outputs JSON<br/>exit 0 (even if PF fails, do not block)
    end
    deactivate HK

    Note over CC: Parse hookSpecificOutput<br/>Inject additionalContext into<br/>AI next context turn

    CC->>CC: Actually execute Skill tool<br/>Load SKILL.md etc.

    CC-->>AI: Skill tool result + preflight additionalContext

    Note over AI: AI sees simultaneously:<br/>1. SKILL.md content<br/>2. preflight result<br/>No need to manually run preflight
```

### Key Timing Constraints

| Step | Sync / Async | Failure Handling |
|---|---|---|
| ②→③ Harness calls hook | **Synchronous blocking** | Skill tool does not execute until hook exits |
| ④ Hook parses stdin | Synchronous | JSON parse fail → exit 0 immediately |
| ⑤ Skill name filter | Synchronous | Mismatch → exit 0 immediately without running PF |
| ⑥→⑩ Spawn preflight | Synchronous blocking | timeout=120s; on timeout → inject diagnostics, exit 0 |
| ⑪ JSON output | Synchronous | Always exit 0 (PF failure does not block Skill) |
| ⑫ Inject additionalContext | Handled by harness | Injected into AI context as system message |

### Key Design Trade-offs

- **Never Block**: Even if preflight itself crashes, hook exits 0; it is better for AI to see diagnostic info than for the entire skill to become unavailable.
- **Secondary Filtering in Script**: `matcher: "Skill"` matches on tool name alone; filtering on `skill_name == "api-test-e10"` inside the script is required to avoid intercepting other skills.
- **CWD Inherits payload.cwd**: The preflight subprocess runs in the user session CWD (the consumer project), not the hook script directory.
