# EVOLVE Architecture

```text
Voice / UI / Android
        │
        ▼
Wake + Perception Layer
  ├─ Wake word
  ├─ VAD
  ├─ STT
  ├─ screen/device observation
  └─ context signals
        │
        ▼
Context & Workflow Model
  ├─ current state
  ├─ user-approved memory
  ├─ workflow history
  └─ next-action prediction
        │
        ▼
AETHON Orchestrator
  ├─ intent
  ├─ planning
  ├─ model routing
  └─ task state
        │
        ├───────────────┐
        ▼               ▼
Capability Registry   Capability Factory
        │               │
        │          research/design/build
        │          test/evaluate/sandbox
        │               │
        └───────┬───────┘
                ▼
          Safety Kernel
  identity → authorization → risk → policy
                │
                ▼
         Authorized Tools
  web / files / code / browser / Android
                │
                ▼
           Observation
                │
                ▼
           Verification
                │
                ▼
        Result + Audit Log
                │
                ▼
          Workflow Memory
                │
                └──────────► learning loop
```

## Initial implementation boundaries

### Phase 1 — Voice foundation
1. Unified voice session contract.
2. Wake-state model.
3. STT/TTS abstraction.
4. Streaming assistant handoff.
5. Android voice-session transport.
6. Testable fake providers.

### Phase 2 — Workflow intelligence
1. Workflow event schema.
2. Workflow storage.
3. Sequence extraction.
4. Next-action baseline.
5. Evaluation harness.

### Phase 3 — Capability factory
1. Capability-gap schema.
2. Research planner.
3. Code-generation sandbox.
4. Test/evaluation runner.
5. Capability registration with approval gates.

### Phase 4 — Multimodal/device intelligence
1. Android screen observation.
2. Semantic UI actions.
3. Screenshot/UI-tree verification.
4. Cross-device task state.

### Phase 5 — Continual improvement
1. Personal workflow model.
2. Failure learning.
3. Capability regression tests.
4. Versioned capability marketplace/registry.

## Engineering rule

Do not replace working AETHON modules merely to rename them. Extend stable interfaces and introduce new contracts at clear boundaries.
