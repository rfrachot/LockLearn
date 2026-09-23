"""Long-operation progress and cancellation tests."""

import asyncio

from custom_components.locklearn.core.operations import OperationRegistry


async def test_operation_stream_and_cancellation_cleanup() -> None:
    """Progress is observable, cancellable and detached on close."""
    registry = OperationRegistry()
    started = asyncio.Event()

    async def worker(context):
        await context.async_update("merge", 0.25)
        started.set()
        await asyncio.Event().wait()

    operation_id = registry.start("queued", worker)
    snapshots: list[dict] = []
    unsubscribe = registry.subscribe(operation_id, snapshots.append)
    await started.wait()
    assert snapshots[-1]["phase"] == "merge"
    assert snapshots[-1]["progress"] == 0.25
    assert registry.cancel(operation_id)
    await asyncio.sleep(0)
    state = registry.get(operation_id)
    assert state is not None
    assert state.status == "cancelled"
    unsubscribe()
    await registry.async_close()


async def test_operation_can_publish_terminal_result_payload() -> None:
    registry = OperationRegistry()

    async def worker(context):
        await context.async_set_result({"rebuilt_cards": 3, "applied": True})

    operation_id = registry.start("rebuild_progress", worker)
    task = registry.task(operation_id)
    assert task is not None
    await task

    state = registry.get(operation_id)
    assert state is not None
    assert state.status == "completed"
    assert state.result == {"rebuilt_cards": 3, "applied": True}
    assert state.as_dict()["result"] == {"rebuilt_cards": 3, "applied": True}
    await registry.async_close()
