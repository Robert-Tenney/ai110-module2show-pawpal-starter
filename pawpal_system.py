"""
pawpal_system.py
----------------
Logic layer for PawPal+.
All backend classes live here: Owner, Pet, Task, TaskDetail, DailySchedule,
and the Scheduler engine that builds a daily plan.
"""
 
from __future__ import annotations
 
import uuid
from dataclasses import dataclass, field
from datetime import date, time
from typing import Optional
 
 
# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
 
@dataclass
class Owner:
    """Represents a pet owner."""
    name: str
    email: str
    phone: str = ""
    owner_id: str = field(default_factory=lambda: str(uuid.uuid4()))
 
    # --- relationships (populated at runtime, not stored in the dataclass) ---
    _pets: list[Pet] = field(default_factory=list, repr=False, compare=False)
 
    def add_pet(self, pet: "Pet") -> None:
        """Attach a Pet to this owner."""
        pet.owner_id = self.owner_id
        self._pets.append(pet)
 
    def get_pets(self) -> list["Pet"]:
        """Return all pets belonging to this owner."""
        return list(self._pets)
 
 
@dataclass
class Pet:
    """Represents a pet being cared for."""
    name: str
    species: str          # e.g. "dog", "cat", "rabbit"
    breed: str = ""
    owner_id: str = ""
    pet_id: str = field(default_factory=lambda: str(uuid.uuid4()))
 
    def get_schedule(self, on_date: date | None = None) -> "DailySchedule":
        """Return (or create) a DailySchedule for this pet on *on_date*."""
        on_date = on_date or date.today()
        return DailySchedule(pet_id=self.pet_id, date=on_date)
 
 
@dataclass
class Task:
    """
    A single care activity (walk, feeding, medication, grooming, etc.).
    Reusable template — the *when* and *where* live in TaskDetail.
    """
    task_type: str                    # e.g. "walk", "feeding", "medication"
    duration_min: int                 # how long the task takes
    priority: str = "medium"         # "high" | "medium" | "low"
    is_recurring: bool = True         # daily by default
    pet_id: str = ""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
 
    # Each Task has exactly one set of details
    detail: Optional["TaskDetail"] = field(default=None, repr=False)
 
    def edit_task(
        self,
        task_type: str | None = None,
        duration_min: int | None = None,
        priority: str | None = None,
        is_recurring: bool | None = None,
    ) -> None:
        """Update one or more fields on this task."""
        if task_type is not None:
            self.task_type = task_type
        if duration_min is not None:
            self.duration_min = duration_min
        if priority is not None:
            self.priority = priority
        if is_recurring is not None:
            self.is_recurring = is_recurring
 
    def delete_task(self, schedule: "DailySchedule") -> None:
        """Remove this task from the given schedule."""
        schedule.tasks = [t for t in schedule.tasks if t.task_id != self.task_id]
 
 
@dataclass
class TaskDetail:
    """
    The specifics of *when* and *where* a task happens on a given day.
    Composed 1-to-1 with a Task.
    """
    task_id: str
    scheduled_time: time              # e.g. time(8, 0) for 08:00
    location: str = ""               # e.g. "Riverside Park"
    notes: str = ""                  # e.g. "Give 5mg tablet with food"
    detail_id: str = field(default_factory=lambda: str(uuid.uuid4()))
 
    def get_summary(self) -> str:
        """Return a human-readable one-liner for display in the schedule."""
        time_str = self.scheduled_time.strftime("%I:%M %p")
        parts = [time_str]
        if self.location:
            parts.append(f"@ {self.location}")
        if self.notes:
            parts.append(f"({self.notes})")
        return " ".join(parts)
 
 
@dataclass
class DailySchedule:
    """
    Collects all Tasks for one pet on one date and generates an ordered plan.
    """
    pet_id: str
    date: date
    time_budget_min: int = 480        # 8 hours of care time available by default
    tasks: list[Task] = field(default_factory=list)
    schedule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
 
    def add_task(self, task: Task) -> None:
        """Add a task to this schedule."""
        self.tasks.append(task)
 
    def generate_plan(self) -> list[Task]:
        """
        Return an ordered list of tasks that fit within the time budget.
 
        Strategy (fill in Phase 4):
          1. Sort by priority (high → medium → low).
          2. Among equal priority, sort by duration (shortest first).
          3. Walk the sorted list; include a task only if its duration fits
             the remaining budget.
        """
        # TODO (Phase 4): implement full scheduling logic
        priority_order = {"high": 0, "medium": 1, "low": 2}
        sorted_tasks = sorted(
            self.tasks,
            key=lambda t: (priority_order.get(t.priority, 99), t.duration_min),
        )
 
        plan: list[Task] = []
        remaining = self.time_budget_min
        for task in sorted_tasks:
            if task.duration_min <= remaining:
                plan.append(task)
                remaining -= task.duration_min
 
        return plan
 
 
# ---------------------------------------------------------------------------
# Scheduler (orchestration helper)
# ---------------------------------------------------------------------------
 
class Scheduler:
    """
    Top-level engine that ties owners, pets, tasks, and schedules together.
    The Streamlit UI will talk primarily to this class.
    """
 
    def __init__(self) -> None:
        self._owners: dict[str, Owner] = {}
        self._pets: dict[str, Pet] = {}
        self._schedules: dict[str, DailySchedule] = {}   # keyed by schedule_id
 
    # -- Owner management --------------------------------------------------
 
    def add_owner(self, owner: Owner) -> Owner:
        """Register an owner and return it."""
        self._owners[owner.owner_id] = owner
        return owner
 
    def get_owner(self, owner_id: str) -> Owner | None:
        return self._owners.get(owner_id)
 
    # -- Pet management ----------------------------------------------------
 
    def add_pet(self, pet: Pet, owner: Owner) -> Pet:
        """Register a pet, link it to an owner, and return it."""
        owner.add_pet(pet)
        self._pets[pet.pet_id] = pet
        return pet
 
    def get_pet(self, pet_id: str) -> Pet | None:
        return self._pets.get(pet_id)
 
    def list_pets(self, owner_id: str) -> list[Pet]:
        return [p for p in self._pets.values() if p.owner_id == owner_id]
 
    # -- Schedule management -----------------------------------------------
 
    def get_or_create_schedule(
        self, pet: Pet, on_date: date | None = None
    ) -> DailySchedule:
        """Return an existing schedule for (pet, date) or create a new one."""
        on_date = on_date or date.today()
        for sched in self._schedules.values():
            if sched.pet_id == pet.pet_id and sched.date == on_date:
                return sched
        sched = DailySchedule(pet_id=pet.pet_id, date=on_date)
        self._schedules[sched.schedule_id] = sched
        return sched
 
    def add_task_to_schedule(
        self,
        task: Task,
        detail: TaskDetail,
        schedule: DailySchedule,
    ) -> None:
        """Attach a TaskDetail to its Task, then add the Task to the schedule."""
        task.detail = detail
        schedule.add_task(task)
 
    def build_plan(self, schedule: DailySchedule) -> list[Task]:
        """Generate and return the ordered daily plan for a schedule."""
        return schedule.generate_plan()
 
    def format_plan(self, schedule: DailySchedule) -> str:
        """
        Return a pretty-printed string of the daily plan.
        Example output:
            Daily plan for 2025-06-10:
              08:00 AM — Morning walk (30 min) [priority: high] @ Riverside Park
              09:00 AM — Feeding (10 min) [priority: high]
        """
        plan = self.build_plan(schedule)
        if not plan:
            return "No tasks scheduled for this day."
 
        lines = [f"Daily plan for {schedule.date}:"]
        for task in plan:
            detail = task.detail
            time_str = (
                detail.scheduled_time.strftime("%I:%M %p") if detail else "--:--"
            )
            location = f" @ {detail.location}" if detail and detail.location else ""
            notes = f" ({detail.notes})" if detail and detail.notes else ""
            lines.append(
                f"  {time_str} — {task.task_type.title()} "
                f"({task.duration_min} min) "
                f"[priority: {task.priority}]"
                f"{location}{notes}"
            )
        return "\n".join(lines)
 