from enum import StrEnum


class TaskStatus(StrEnum):
    INBOX = "inbox"
    PLANNED = "planned"
    ACTIVE = "active"
    DONE = "done"
    ARCHIVED = "archived"
    SNOOZED = "snoozed"


class PriorityBucket(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class EnergyType(StrEnum):
    DEEP = "deep"
    SHALLOW = "shallow"
    ERRAND = "errand"
    LEARNING = "learning"
    SOCIAL = "social"


class TaskSourceType(StrEnum):
    MANUAL = "manual"
    NOTE = "note"
    AI = "ai"
    CALENDAR = "calendar"
    IMPORT = "import"


class ReminderStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReminderChannel(StrEnum):
    TELEGRAM = "telegram"
    DESKTOP = "desktop"
    EMAIL = "email"


class LearningItemStatus(StrEnum):
    BACKLOG = "backlog"
    LEARNING = "learning"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    ARCHIVED = "archived"

