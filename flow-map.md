# Flow map — from the verify request to the verdict

The runtime flow of the `verify` skill, from the invocation (A) to the report and the re-check loop after `FIX REQUIRED` (B). This is the single home of the runtime flow diagram; the rules behind each step live in `.agents/skills/verify/SKILL.md` and `references/`.

Renders on GitHub and claude.ai; VS Code needs a Mermaid extension.

> **Status:** draft — not reviewed (no fresh reviewer was available; every box was checked against the sources by the author only). Everything shown exists in the skill's text. Nothing is missing. The skill is a set of instructions run by the host's agent, so "exists" means the step is specified in the skill files; the flow is not code.
> Lines: solid = exists · red dashed or red band = missing · dotted = optional or read-only · "no code yet" (or "not described") box = missing stage · grey = outside the target · light grey dashed box = side path

## 1. What happens

```mermaid
%%{init: {"theme":"base","themeVariables":{"fontFamily":"system-ui, -apple-system, Segoe UI, sans-serif","fontSize":"15px","primaryTextColor":"#1b221e","lineColor":"#8a968f","clusterBkg":"transparent","clusterBorder":"#b7c0ba","titleColor":"#5d6962","edgeLabelBackground":"#ffffff"},"flowchart":{"curve":"basis","nodeSpacing":22,"rankSpacing":30,"padding":14,"htmlLabels":true,"subGraphTitleMargin":{"top":6,"bottom":14}}}}%%
flowchart TD
    A["<b>verify invoked</b><br/>mode, target, --contract"]
    Z["<b>Author fixes</b><br/>the skill never repairs"]

    subgraph F1["Phase 1 · Target and contract"]
        B["<b>Target resolved</b><br/>branch-aware default, or as named"]
        B2["<b>Base resolved</b><br/>invocation, origin/HEAD, main/master"]
        B3["<b>Artifact target</b><br/>truth is the request it answers"]
        E["<b>Empty target</b><br/>no base and clean tree"]
        C["<b>Verification Contract</b><br/>built first, never edited"]
    end

    subgraph F2["Phase 2 · Panel"]
        D["<b>Mode baseline</b><br/>quick, panel or release roles"]
        D2["<b>Triggers and bound</b><br/>security kept at the bound"]
        D3["<b>Mode escalated</b><br/>quick to panel, panel to release"]
    end

    subgraph F3["Phase 3 · Review and report"]
        F["<b>Capability check</b><br/>unknown means no commands"]
        G["<b>Fresh reviewers</b><br/>one context per role, depth one"]
        H["<b>Adjudication</b><br/>lead gates every claim"]
        I["<b>Report</b><br/>fixed header, one of 4 verdicts"]
    end

    subgraph F4["Phase 4 · Re-check"]
        R1["<b>Eligibility</b><br/>same contract hash, else full run"]
        R2["<b>Re-check target</b><br/>delta plus open-finding files"]
        R3["<b>Stop rule</b><br/>no-ship until a re-check passes"]
    end

    A -->|"invoke"| B
    B --> B2
    B2 -->|"base"| C
    %% 3: optional
    B -.->|"plan or doc"| B3
    %% 4: optional
    B3 -.-> C
    %% 5: optional
    B2 -.->|"none"| E
    %% 6: optional
    E -.->|"empty panel"| I
    C --> D
    D --> D2
    D2 --> F
    %% 10: optional
    D2 -.->|"security or high"| D3
    %% 11: optional
    D3 -.-> F
    F --> G
    G --> H
    H --> I
    I -->|"FIX REQUIRED"| Z
    Z -->|"fixed"| R1
    R1 -->|"eligible"| R2
    R2 -->|"re-run roles"| G
    I -->|"no open blocker"| R3

    classDef ext fill:#e7eae8,stroke:#8a968f,color:#1b221e
    classDef p1 fill:#dbe8f6,stroke:#4a7fb5,color:#1b221e
    classDef p2 fill:#fbefd2,stroke:#c3962c,color:#1b221e
    classDef p3 fill:#d8eee2,stroke:#3f8f68,color:#1b221e
    classDef p4 fill:#e7def4,stroke:#7a5aa6,color:#1b221e
    classDef side fill:#f5f6f5,stroke:#a9b4ad,color:#5d6962,stroke-dasharray:4 3
    class A,Z ext
    class B,B2,C p1
    class D,D2 p2
    class F,G,H,I p3
    class R1,R2,R3 p4
    class B3,E,D3 side
    linkStyle 3,4,5,6,10,11 stroke:#8a968f,stroke-width:1.5px,stroke-dasharray:2 3
```

| Phase | In one line |
|---|---|
| Target and contract | The default target is the branch against its merge base plus the working tree, or the working-tree diff; the base comes from the invocation, then `origin/HEAD`, then local `main` or `master`, else the working tree only (and an empty target reviews nothing, `PASS WITH NOTES`). A plan or design document is an artifact target whose truth is the request it answers. The Verification Contract is built before any reviewer and is never edited or reinterpreted. |
| Panel | The mode baseline plus roles added only by concrete surface trigger, up to the mode maximum. A triggered security role is never the one omitted; `quick` escalates to `panel` on a security trigger or a high or critical surface, and `panel` to `release` on a critical one. |
| Review and report | The lead checks whether reviewers can run commands (if not, it runs the narrow read-only commands itself), dispatches fresh reviewers, gates every claim, and returns one of `PASS`, `PASS WITH NOTES`, `FIX REQUIRED`, `INCONCLUSIVE` under the fixed header. Without fresh contexts the roles run in sequence and the report says `degraded independence`. |
| Re-check | After `FIX REQUIRED` and a fix, a re-check is eligible only for the same contract with an unchanged source (compared by hash); otherwise a full run follows. It re-runs the baseline roles, every role with an open finding and any newly triggered role, over the delta (commits since the verified state, working-tree status, paths whose hash changed) plus the files of open `BLOCKER` and `SHOULD_FIX` findings. It stops at the first round with no new or unresolved blocking finding and no `MISSING` gap; `OPTIONAL` findings never open another round. |

## 2. Who talks to whom

The caller invokes the lead, which reads the repository and the contract file and briefs host subagents; reviewers read the repository and may run existing project commands. Colors here only tell who is who.

```mermaid
%%{init: {"theme":"base","themeVariables":{"fontFamily":"system-ui, -apple-system, Segoe UI, sans-serif","fontSize":"15px","primaryTextColor":"#1b221e","lineColor":"#8a968f","edgeLabelBackground":"#ffffff"},"flowchart":{"curve":"basis","nodeSpacing":36,"rankSpacing":44,"padding":14,"htmlLabels":true}}}%%
flowchart TD
    USER["<b>Caller</b><br/>person or host agent"]
    LEAD["<b>verify lead</b><br/>SKILL.md and references"]
    REV["<b>Host subagents</b><br/>one fresh reviewer per role"]
    REPO[("<b>Repository</b><br/>git history and files")]
    CON[("<b>Contract file</b><br/>optional --contract")]
    CMD["<b>Project commands</b><br/>existing tests and analysis"]

    USER -->|"invokes"| LEAD
    LEAD -->|"report"| USER
    %% 2: optional
    LEAD -.->|"reads"| REPO
    %% 3: optional
    LEAD -.->|"reads"| CON
    LEAD <-->|"briefs, findings"| REV
    %% 5: optional
    REV -.->|"reads"| REPO
    %% 6: optional
    LEAD -.->|"runs if reviewers can't"| CMD
    %% 7: optional
    REV -.->|"may run"| CMD

    classDef ext fill:#e7eae8,stroke:#8a968f,color:#1b221e
    classDef front fill:#ffffff,stroke:#3d4a43,color:#1b221e,stroke-width:1.5px
    classDef ours fill:#ffffff,stroke:#1b221e,color:#1b221e,stroke-width:2px
    classDef db fill:#ffffff,stroke:#8a968f,color:#1b221e
    class REV,CMD ext
    class USER front
    class LEAD ours
    class REPO,CON db
    linkStyle 2,3,5,6,7 stroke:#8a968f,stroke-width:1.5px,stroke-dasharray:2 3
```

## 3. The life of one verification

```mermaid
%%{init: {"theme":"base","themeVariables":{"fontFamily":"system-ui, -apple-system, Segoe UI, sans-serif","fontSize":"15px","actorBkg":"#e7eae8","actorBorder":"#8a968f","actorTextColor":"#1b221e","actorLineColor":"#c3cbc6","signalColor":"#5d6962","signalTextColor":"#1b221e","sequenceNumberColor":"#ffffff","noteBkgColor":"#f1f3f1","noteBorderColor":"#b7c0ba","noteTextColor":"#1b221e"},"sequence":{"mirrorActors":false,"messageMargin":24,"boxMargin":8,"actorMargin":40,"messageFontSize":15,"actorFontSize":15,"noteFontSize":14}}}%%
sequenceDiagram
    autonumber
    participant CA as Caller
    participant LE as verify lead
    participant RE as Reviewers
    participant RP as Repository
    CA->>LE: verify, mode, target, --contract
    LE->>RP: resolves base and target, read-only
    LE->>LE: builds the Verification Contract
    LE->>LE: selects the panel, checks reviewer capability
    LE->>RE: contract, target, role files, finding schema
    RE->>RP: read, cite file and line
    RE-->>LE: findings or NO FINDINGS
    LE->>LE: gates every claim, assigns severity
    LE-->>CA: report, FIX REQUIRED, must not ship
    CA->>CA: author fixes the change
    CA->>LE: verify again
    LE->>LE: eligible if contract hash matches
    LE->>RE: fresh reviewers, open findings as claim and location
    RE-->>LE: findings
    LE->>LE: re-confirms each prior finding, adds the delta
    LE-->>CA: report, loop stops when nothing blocking is open
```

## Where it lives

| Phase | Path |
|---|---|
| Target and contract | `.agents/skills/verify/SKILL.md` (steps 1–2), `.agents/skills/verify/references/verification-contract.md` |
| Panel | `.agents/skills/verify/references/panel.md` |
| Review and report | `.agents/skills/verify/SKILL.md` (steps 4–6), `.agents/skills/verify/references/reviewers/`, `.agents/skills/verify/references/adjudication.md`, `.agents/skills/verify/references/json-report.md` |
| Re-check | `.agents/skills/verify/SKILL.md` (step 7), `.agents/skills/verify/references/adjudication.md#re-check`, `.agents/skills/verify/references/panel.md#re-check-panel` |

When the flow changes, the map changes in the same PR. To update, see what changed since the commit below.

Updated 2026-11-11 · agent-verification release/v0.5.0 2d6c68e
