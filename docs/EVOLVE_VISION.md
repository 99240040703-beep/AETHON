# EVOLVE — Self-Evolving Voice AI

## Product direction

EVOLVE is the next research/product layer built on the AETHON foundation.

**Goal:** build an AI system that can understand a user's goal, use authorized capabilities, and—when a required capability does not exist—research, design, implement, test, and safely register a new capability.

EVOLVE is not a claim of a new foundation model. Its research contribution is the system architecture and measurable methods for capability discovery, capability construction, workflow learning, and safe execution.

## Core loop

`Wake/Observe → Understand → Reason → Plan → Act → Verify → Learn → Evolve`

## Voice-first interaction

Primary interaction:

`Wake word → Voice activity detection → Speech-to-text → Intent/context → Planning → Tool/device execution → Verification → Text-to-speech`

The first-class wake phrase is configurable. The initial product phrase is **"Hey Evolve"**.

Voice must support:
- foreground conversational use
- Android background wake-word operation where platform permissions and OS restrictions allow it
- interruption/barge-in
- silence/end-of-turn detection
- language/locale selection
- streaming recognition and response where available
- explicit confirmation for consequential actions

## Capability evolution

When the planner detects a missing capability:

`Goal → Capability gap → Research → Design → Implement → Test → Evaluate → Sandbox → Register`

Generated capabilities remain disabled until they pass policy checks and evaluation gates.

## Safety invariant

The model never receives unrestricted authority.

Every side-effecting capability passes through:
- identity
- authorization
- risk classification
- policy evaluation
- approval when required
- bounded execution
- observation
- verification
- audit logging

## Research measurements

Track:
- intent accuracy
- workflow recognition accuracy
- next-action prediction accuracy
- task success rate
- capability-generation success rate
- generated-code test pass rate
- verification accuracy
- human intervention rate
- unsafe-action rejection rate
- latency and cost
- improvement after workflow learning

## Relationship to AETHON

AETHON remains the execution and agent foundation.

EVOLVE adds:
- voice/wake-word orchestration
- workflow intelligence
- capability-gap detection
- capability factory
- capability evaluation
- continual workflow learning

ASTRA can remain the user-facing assistant experience where appropriate; EVOLVE is the deeper research/runtime direction.
