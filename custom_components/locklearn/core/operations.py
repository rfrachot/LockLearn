"""Observable, cancellable long-operation primitives."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass
from typing import Any
from uuid import uuid4

OperationListener = Callable[[dict[str, Any]], None]
OperationWorker = Callable[["OperationContext"], Awaitable[None]]


@dataclass(slots=True)
class OperationState:
    """Public progress state for a long operation."""

    operation_id: str
    phase: str
    progress: float
    cancellable: bool
    status: str
    error: str | None = None
    result: dict[str, Any] | None = None
    owner_user_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        """Return a WebSocket-safe snapshot."""
        result = asdict(self)
        result.pop("owner_user_id")
        return result


class OperationContext:
    """Allow a worker to publish bounded progress and observe cancellation."""

    def __init__(self, registry: OperationRegistry, operation_id: str) -> None:
        self._registry = registry
        self.operation_id = operation_id

    async def async_update(self, phase: str, progress: float) -> None:
        """Publish progress and yield so cancellation/backpressure can run."""
        await self._registry.async_update(self.operation_id, phase, progress)
        await asyncio.sleep(0)

    async def async_set_result(self, result: dict[str, Any]) -> None:
        """Publish the terminal/result payload produced by a long operation."""
        await self._registry.async_set_result(self.operation_id, result)
        await asyncio.sleep(0)

    def raise_if_cancelled(self) -> None:
        """Raise CancelledError if the operation was cancelled."""
        task = self._registry.task(self.operation_id)
        if task is not None and task.cancelling():
            raise asyncio.CancelledError


class OperationRegistry:
    """Track long operations and their subscription lifecycle."""

    def __init__(self) -> None:
        self._states: dict[str, OperationState] = {}
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._listeners: dict[str, set[OperationListener]] = {}
        self._closed = False

    def task(self, operation_id: str) -> asyncio.Task[None] | None:
        """Return the active task for cancellation checks."""
        return self._tasks.get(operation_id)

    @property
    def subscriber_count(self) -> int:
        """Return the active subscriber count for lifecycle diagnostics."""
        return sum(len(listeners) for listeners in self._listeners.values())

    def get(self, operation_id: str) -> OperationState | None:
        """Return an operation snapshot."""
        return self._states.get(operation_id)

    def start(
        self,
        phase: str,
        worker: OperationWorker,
        *,
        cancellable: bool = True,
        owner_user_id: str | None = None,
    ) -> str:
        """Start a supervised operation."""
        if self._closed:
            raise RuntimeError("Operation registry is closed")
        operation_id = uuid4().hex
        self._states[operation_id] = OperationState(
            operation_id=operation_id,
            phase=phase,
            progress=0.0,
            cancellable=cancellable,
            status="running",
            owner_user_id=owner_user_id,
        )
        task = asyncio.create_task(
            self._async_run(operation_id, worker), name=f"locklearn-operation-{operation_id}"
        )
        self._tasks[operation_id] = task
        return operation_id

    async def _async_run(self, operation_id: str, worker: OperationWorker) -> None:
        try:
            await worker(OperationContext(self, operation_id))
        except asyncio.CancelledError:
            state = self._states[operation_id]
            state.status = "cancelled"
            self._publish(operation_id)
            raise
        except Exception as err:
            state = self._states[operation_id]
            state.status = "failed"
            state.error = type(err).__name__
            self._publish(operation_id)
        else:
            state = self._states[operation_id]
            state.progress = 1.0
            state.status = "completed"
            self._publish(operation_id)
        finally:
            self._tasks.pop(operation_id, None)

    async def async_update(self, operation_id: str, phase: str, progress: float) -> None:
        """Update an active operation with a normalized progress value."""
        state = self._states[operation_id]
        if state.status != "running":
            return
        state.phase = phase
        state.progress = min(1.0, max(0.0, progress))
        self._publish(operation_id)

    async def async_set_result(self, operation_id: str, result: dict[str, Any]) -> None:
        """Attach a WebSocket-safe result payload to an active operation."""
        state = self._states[operation_id]
        if state.status != "running":
            return
        state.result = dict(result)
        self._publish(operation_id)

    def cancel(self, operation_id: str) -> bool:
        """Cancel an operation if it exists and is cancellable."""
        state = self._states.get(operation_id)
        task = self._tasks.get(operation_id)
        if state is None or task is None or not state.cancellable:
            return False
        task.cancel()
        return True

    def subscribe(self, operation_id: str, listener: OperationListener) -> Callable[[], None]:
        """Subscribe and return an idempotent detach callback."""
        if operation_id not in self._states:
            raise KeyError(operation_id)
        listeners = self._listeners.setdefault(operation_id, set())
        listeners.add(listener)

        def unsubscribe() -> None:
            listeners.discard(listener)
            if not listeners:
                self._listeners.pop(operation_id, None)

        return unsubscribe

    def _publish(self, operation_id: str) -> None:
        snapshot = self._states[operation_id].as_dict()
        for listener in tuple(self._listeners.get(operation_id, ())):
            listener(snapshot)

    async def async_close(self) -> None:
        """Cancel active work and detach every subscriber."""
        self._closed = True
        tasks = tuple(self._tasks.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._listeners.clear()
