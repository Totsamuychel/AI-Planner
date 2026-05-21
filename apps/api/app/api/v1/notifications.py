import asyncio
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.api.deps import SessionDep
from app.models.reminder import Reminder
from app.schemas.notification import NotificationTestRequest, ReminderOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


# Simple in-memory queue for SSE. In production, use Redis Pub/Sub.
clients: set[asyncio.Queue] = set()


async def sse_generator(request: Request, queue: asyncio.Queue) -> AsyncGenerator[str, None]:
    try:
        while True:
            if await request.is_disconnected():
                break
            data = await queue.get()
            yield f"data: {data}\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        clients.remove(queue)


@router.get("/sse")
async def sse_notifications(request: Request) -> StreamingResponse:
    queue: asyncio.Queue = asyncio.Queue()
    clients.add(queue)
    return StreamingResponse(sse_generator(request, queue), media_type="text/event-stream")


@router.post("/test")
async def send_test_notification(req: NotificationTestRequest) -> dict[str, Any]:
    # Push to SSE clients if channel is desktop
    if req.channel == "desktop":
        for queue in clients:
            await queue.put(f"Test notification: {req.message}")
    
    return {"status": "ok", "message": "Test notification dispatched."}


@router.get("/history", response_model=list[ReminderOut])
async def get_notification_history(
    db: SessionDep,
    limit: int = 50,
) -> Any:
    result = await db.execute(
        select(Reminder)
        .order_by(Reminder.created_at.desc())
        .limit(limit)
    )
    reminders = result.scalars().all()
    return reminders
