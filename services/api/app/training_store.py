from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from uuid import uuid4

import psycopg


@dataclass(frozen=True)
class TrainingExample:
    example_id: str
    owner_id: str
    session_id: str | None
    request_id: str | None
    user_text: str
    assistant_text: str
    capability: str | None
    tool: str | None
    mode: str | None
    language: str
    verified: bool
    success: bool
    feedback: str | None
    score: float | None
    metadata: dict


class TrainingStore:
    """Owner-scoped dataset store for ASTRA training and evaluation.

    PostgreSQL is used when AETHON_DATABASE_URL is configured. The bounded
    in-memory store keeps local development and tests deterministic.
    """

    _memory: list[TrainingExample] = []
    _memory_limit = 5000

    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = (
            os.getenv("AETHON_DATABASE_URL", "") if database_url is None else database_url
        )

    @property
    def enabled(self) -> bool:
        return self.database_url.startswith(("postgres://", "postgresql://"))

    def _ensure_table(self, conn) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS astra_training_examples (
                example_id UUID PRIMARY KEY,
                owner_id TEXT NOT NULL,
                session_id UUID NULL,
                request_id UUID NULL,
                user_text TEXT NOT NULL,
                assistant_text TEXT NOT NULL,
                capability TEXT NULL,
                tool TEXT NULL,
                mode TEXT NULL,
                language TEXT NOT NULL,
                verified BOOLEAN NOT NULL DEFAULT FALSE,
                success BOOLEAN NOT NULL DEFAULT FALSE,
                feedback TEXT NULL,
                score DOUBLE PRECISION NULL,
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        conn.commit()

    def record(
        self,
        *,
        owner_id: str,
        user_text: str,
        assistant_text: str,
        session_id: str | None = None,
        request_id: str | None = None,
        capability: str | None = None,
        tool: str | None = None,
        mode: str | None = None,
        language: str = "en-US",
        verified: bool = False,
        success: bool = True,
        metadata: dict | None = None,
    ) -> TrainingExample:
        item = TrainingExample(
            example_id=str(uuid4()),
            owner_id=owner_id,
            session_id=session_id,
            request_id=request_id,
            user_text=user_text[:12000],
            assistant_text=assistant_text[:20000],
            capability=capability,
            tool=tool,
            mode=mode,
            language=language,
            verified=bool(verified),
            success=bool(success),
            feedback=None,
            score=None,
            metadata=metadata or {},
        )
        if not self.enabled:
            self._memory.append(item)
            if len(self._memory) > self._memory_limit:
                del self._memory[:-self._memory_limit]
            return item

        with psycopg.connect(self.database_url) as conn:
            self._ensure_table(conn)
            conn.execute(
                """
                INSERT INTO astra_training_examples
                (example_id, owner_id, session_id, request_id, user_text,
                 assistant_text, capability, tool, mode, language,
                 verified, success, metadata)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
                """,
                (
                    item.example_id,
                    owner_id,
                    session_id,
                    request_id,
                    item.user_text,
                    item.assistant_text,
                    capability,
                    tool,
                    mode,
                    language,
                    item.verified,
                    item.success,
                    json.dumps(item.metadata),
                ),
            )
            conn.commit()
        return item

    def feedback(self, example_id: str, owner_id: str, feedback: str, score: float | None) -> bool:
        feedback = feedback.strip().lower()
        if feedback not in {"good", "bad", "correct", "incorrect", "useful", "not_useful"}:
            raise ValueError("feedback must be good, bad, correct, incorrect, useful, or not_useful")
        if score is not None and not 0 <= score <= 1:
            raise ValueError("score must be between 0 and 1")

        if not self.enabled:
            for index, item in enumerate(self._memory):
                if item.example_id == example_id and item.owner_id == owner_id:
                    self._memory[index] = TrainingExample(**{
                        **asdict(item), "feedback": feedback,
                        "score": score if score is not None else (
                            1.0 if feedback in {"good", "correct", "useful"} else 0.0
                        )
                    })
                    return True
            return False

        with psycopg.connect(self.database_url) as conn:
            self._ensure_table(conn)
            result = conn.execute(
                """
                UPDATE astra_training_examples
                SET feedback=%s, score=%s, updated_at=NOW()
                WHERE example_id=%s AND owner_id=%s
                """,
                (
                    feedback,
                    score if score is not None else (
                        1.0 if feedback in {"good", "correct", "useful"} else 0.0
                    ),
                    example_id,
                    owner_id,
                ),
            )
            conn.commit()
            return result.rowcount == 1

    def list(self, owner_id: str, limit: int = 100, only_labeled: bool = False) -> list[TrainingExample]:
        limit = max(1, min(limit, 1000))
        if not self.enabled:
            rows = [x for x in self._memory if x.owner_id == owner_id]
            if only_labeled:
                rows = [x for x in rows if x.feedback is not None]
            return rows[-limit:][::-1]

        with psycopg.connect(self.database_url) as conn:
            self._ensure_table(conn)
            where = "owner_id=%s"
            params: list[object] = [owner_id]
            if only_labeled:
                where += " AND feedback IS NOT NULL"
            params.append(limit)
            rows = conn.execute(
                f"""
                SELECT example_id, owner_id, session_id, request_id, user_text,
                       assistant_text, capability, tool, mode, language,
                       verified, success, feedback, score, metadata
                FROM astra_training_examples
                WHERE {where}
                ORDER BY created_at DESC
                LIMIT %s
                """,
                params,
            ).fetchall()

        return [
            TrainingExample(
                example_id=str(row[0]),
                owner_id=row[1],
                session_id=str(row[2]) if row[2] else None,
                request_id=str(row[3]) if row[3] else None,
                user_text=row[4],
                assistant_text=row[5],
                capability=row[6],
                tool=row[7],
                mode=row[8],
                language=row[9],
                verified=row[10],
                success=row[11],
                feedback=row[12],
                score=row[13],
                metadata=row[14] or {},
            )
            for row in rows
        ]

    def stats(self, owner_id: str) -> dict:
        rows = self.list(owner_id, limit=1000)
        labeled = [x for x in rows if x.score is not None]
        return {
            "examples": len(rows),
            "labeled": len(labeled),
            "success_rate": round(sum(x.success for x in rows) / len(rows), 4) if rows else 0.0,
            "verification_rate": round(sum(x.verified for x in rows) / len(rows), 4) if rows else 0.0,
            "feedback_score": round(sum(x.score for x in labeled) / len(labeled), 4) if labeled else None,
            "capabilities": sorted({x.capability for x in rows if x.capability}),
            "tools": sorted({x.tool for x in rows if x.tool}),
            "languages": sorted({x.language for x in rows if x.language}),
        }

    def export_jsonl(self, owner_id: str, only_labeled: bool = True) -> str:
        rows = self.list(owner_id, limit=1000, only_labeled=only_labeled)
        output: list[str] = []
        for item in rows:
            # Training-ready instruction format; hidden reasoning is never collected.
            record = {
                "messages": [
                    {"role": "user", "content": item.user_text},
                    {"role": "assistant", "content": item.assistant_text},
                ],
                "metadata": {
                    "capability": item.capability,
                    "tool": item.tool,
                    "mode": item.mode,
                    "language": item.language,
                    "verified": item.verified,
                    "success": item.success,
                    "feedback": item.feedback,
                    "score": item.score,
                },
            }
            output.append(json.dumps(record, ensure_ascii=False))
        return "\n".join(output)
