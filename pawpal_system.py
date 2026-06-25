"""
pawpal_system.py
----------------
Logic layer for PawPal+.
Classes: Task, TaskDetail, Pet, Owner, DailySchedule, Scheduler.
"""
 
from __future__ import annotations
 
import uuid
from dataclasses import dataclass, field
from datetime import date, time
from typing import Optional
 
 
# ─────────────────────────────────────────────
# Task
# ─────────────────────────────────────────────
 
@dataclass
class TaskDetail:
    """
    The when/where specifics of a task on a given day.
    Composed 1-to-1 with a Task.
    """
    task_id: str
    scheduled_time: time              # e.g. time(8, 0)  → 08:00
    location: str = ""               # e.g. "Riverside Park"
    notes: str = ""                  # e.g. "Give 5 mg tablet with food"
    detail_id: str = field(default_factory=lambda: str(uuid.uuid4()))
 
    def get_summary(self) -> str:
        """One-liner suitable for terminal or UI display."""
        time_str = self.scheduled_time.strftime("%I:%M %p")
        parts = [time_str]
        if self.location:
            parts.append(f"@ {self.location}")
        if self.notes:
            parts.append(f"({self.notes})")
        return " ".join(parts)
 
 
@dataclass
class Task:
    """
    A single pet-care activity.
 
    Attributes
    ----------
    task_type     : short label, e.g. "walk", "feeding", "medication"
    description   : free-text detail, e.g. "Morning walk around the block"
    duration_min  : how many minutes the activity takes
    priority      : "high" | "medium" | "low"
    is_recurring  : True = daily, False = one-off
    is_completed  : toggled when the owner marks the task done
    pet_id        : which pet this task belongs to
    detail        : optional TaskDetail (when/where)
    """
    task_type: str
    description: str
    duration_min: int
    priority: str = "medium"
    is_recurring: bool = True
    is_completed: bool = False
    pet_id: str = ""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    detail: Optional[TaskDetail] = field(default=None, repr=False)
 
    # ── mutators ──────────────────────────────
 
    def edit_task(
        self,
        task_type: str | None = None,
        description: str | None = None,
        duration_min: int | None = None,
        priority: str | None = None,
        is_recurring: bool | None = None,
    ) -> None:
        """Update any subset of fields in place."""
        if task_type is not None:
            self.task_type = task_type
        if description is not None:
            self.description = description
        if duration_min is not None:
            self.duration_min = duration_min
        if priority is not None:
            self.priority = priority
        if is_recurring is not None:
            self.is_recurring = is_recurring
 
    def mark_complete(self) -> None:
        """Mark this task as done for today."""
        self.is_completed = True
 
    def mark_incomplete(self) -> None:
        """Reset completion status."""
        self.is_completed = False
 
    def set_detail(self, scheduled_time: time, location: str = "", notes: str = "") -> TaskDetail:
        """Create and attach a TaskDetail to this task; return it."""
        self.detail = TaskDetail(
            task_id=self.task_id,
            scheduled_time=scheduled_time,
            location=location,
            notes=notes,
        )
        return self.detail
 
    # ── display ───────────────────────────────
 
    def display(self) -> str:
        """Compact one-liner for terminal output."""
        status = "✓" if self.is_completed else "○"
        time_str = (
            self.detail.scheduled_time.strftime("%I:%M %p")
            if self.detail else "--:--   "
        )
        location = f" @ {self.detail.location}" if self.detail and self.detail.location else ""
        notes    = f" | {self.detail.notes}"    if self.detail and self.detail.notes    else ""
        return (
            f"  [{status}] {time_str}  {self.task_type.upper():<12} "
            f"{self.description}{location}{notes}  "
            f"({self.duration_min} min, {self.priority})"
        )
 
 
# ─────────────────────────────────────────────
# Pet
# ─────────────────────────────────────────────
 
@dataclass
class Pet:
    """
    A pet being cared for.
 
    Stores pet details and owns a list of Task objects.
    """
    name: str
    species: str          # "dog" | "cat" | "rabbit" | …
    breed: str = ""
    age_years: float = 0.0
    owner_id: str = ""
    pet_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    _tasks: list[Task] = field(default_factory=list, repr=False, compare=False)
 
    # ── task management ───────────────────────
 
    def add_task(self, task: Task) -> None:
        """Attach a task to this pet."""
        task.pet_id = self.pet_id
        self._tasks.append(task)
 
    def remove_task(self, task_id: str) -> bool:
        """Remove a task by ID; return True if found and removed."""
        before = len(self._tasks)
        self._tasks = [t for t in self._tasks if t.task_id != task_id]
        return len(self._tasks) < before
 
    def get_tasks(self) -> list[Task]:
        """Return a copy of all tasks for this pet."""
        return list(self._tasks)
 
    def get_pending_tasks(self) -> list[Task]:
        """Return tasks not yet marked complete."""
        return [t for t in self._tasks if not t.is_completed]
 
    def get_tasks_by_priority(self, priority: str) -> list[Task]:
        """Return tasks matching a given priority level."""
        return [t for t in self._tasks if t.priority == priority]
 
    # ── display ───────────────────────────────
 
    def summary(self) -> str:
        breed_str = f" ({self.breed})" if self.breed else ""
        age_str   = f", {self.age_years} yrs" if self.age_years else ""
        return f"{self.name}{breed_str} — {self.species}{age_str}"
 
 
# ─────────────────────────────────────────────
# Owner
# ─────────────────────────────────────────────
 
@dataclass
class Owner:
    """
    A pet owner who manages one or more pets.
 
    The Scheduler retrieves all tasks by calling
    owner.get_all_tasks(), which walks every pet's task list.
    """
    name: str
    email: str
    phone: str = ""
    owner_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    _pets: list[Pet] = field(default_factory=list, repr=False, compare=False)
 
    # ── pet management ────────────────────────
 
    def add_pet(self, pet: Pet) -> Pet:
        """Register a pet under this owner; return the pet."""
        pet.owner_id = self.owner_id
        self._pets.append(pet)
        return pet
 
    def remove_pet(self, pet_id: str) -> bool:
        """Remove a pet by ID; return True if found."""
        before = len(self._pets)
        self._pets = [p for p in self._pets if p.pet_id != pet_id]
        return len(self._pets) < before
 
    def get_pets(self) -> list[Pet]:
        """Return all pets belonging to this owner."""
        return list(self._pets)
 
    def find_pet_by_name(self, name: str) -> Pet | None:
        """Case-insensitive name lookup; returns the first match."""
        name_lower = name.lower()
        return next((p for p in self._pets if p.name.lower() == name_lower), None)
 
    # ── task aggregation ──────────────────────
 
    def get_all_tasks(self) -> list[Task]:
        """
        Return every task across ALL of this owner's pets.
        This is the primary method the Scheduler calls to build the daily plan.
        """
        tasks: list[Task] = []
        for pet in self._pets:
            tasks.extend(pet.get_tasks())
        return tasks
 
    def get_all_pending_tasks(self) -> list[Task]:
        """All incomplete tasks across every pet."""
        return [t for t in self.get_all_tasks() if not t.is_completed]
 
 
# ─────────────────────────────────────────────
# DailySchedule
# ─────────────────────────────────────────────
 
@dataclass
class DailySchedule:
    """
    Ordered daily plan for one pet on one calendar date.
    """
    pet_id: str
    pet_name: str
    date: date
    time_budget_min: int = 480          # 8 hours default
    tasks: list[Task] = field(default_factory=list)
    schedule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
 
    def add_task(self, task: Task) -> None:
        self.tasks.append(task)
 
    def total_time_used(self) -> int:
        return sum(t.duration_min for t in self.tasks)
 
    def time_remaining(self) -> int:
        return self.time_budget_min - self.total_time_used()
 
    def generate_plan(self) -> list[Task]:
        """
        Sort tasks by priority then scheduled time;
        include only tasks that fit within the time budget.
        """
        PRIORITY = {"high": 0, "medium": 1, "low": 2}
 
        def sort_key(t: Task):
            p = PRIORITY.get(t.priority, 99)
            # secondary sort: scheduled time (tasks without a detail go last)
            t_val = t.detail.scheduled_time if t.detail else time(23, 59)
            return (p, t_val)
 
        sorted_tasks = sorted(self.tasks, key=sort_key)
 
        plan: list[Task] = []
        remaining = self.time_budget_min
        for task in sorted_tasks:
            if task.duration_min <= remaining:
                plan.append(task)
                remaining -= task.duration_min
        return plan
 
 
# ─────────────────────────────────────────────
# Scheduler  ← the "brain"
# ─────────────────────────────────────────────
 
class Scheduler:
    """
    Orchestration engine.  The Streamlit UI talks to this class.
 
    How the Scheduler retrieves tasks from the Owner
    ------------------------------------------------
    scheduler.get_all_tasks(owner)
        → calls owner.get_all_tasks()
        → which calls pet.get_tasks() for every pet the owner has
        → returns a flat list of every Task across all pets
 
    From that list the Scheduler can filter, sort, and build per-pet
    DailySchedule objects for any date.
    """
 
    def __init__(self) -> None:
        self._owners: dict[str, Owner] = {}
        self._schedules: dict[str, DailySchedule] = {}     # schedule_id → schedule
 
    # ── owner / pet registration ──────────────
 
    def register_owner(self, owner: Owner) -> Owner:
        self._owners[owner.owner_id] = owner
        return owner
 
    def get_owner(self, owner_id: str) -> Owner | None:
        return self._owners.get(owner_id)
 
    def add_pet_to_owner(self, pet: Pet, owner: Owner) -> Pet:
        return owner.add_pet(pet)
 
    # ── task retrieval ────────────────────────
 
    def get_all_tasks(self, owner: Owner) -> list[Task]:
        """
        Retrieve every task for every pet owned by *owner*.
        Entry point for building schedules.
        """
        return owner.get_all_tasks()
 
    def get_tasks_for_pet(self, owner: Owner, pet_name: str) -> list[Task]:
        """Return tasks for a single named pet."""
        pet = owner.find_pet_by_name(pet_name)
        return pet.get_tasks() if pet else []
 
    def get_pending_tasks(self, owner: Owner) -> list[Task]:
        """All incomplete tasks across every pet."""
        return owner.get_all_pending_tasks()
 
    # ── schedule building ─────────────────────
 
    def build_schedule_for_pet(
        self,
        pet: Pet,
        on_date: date | None = None,
        time_budget_min: int = 480,
    ) -> DailySchedule:
        """
        Create a DailySchedule for *pet* on *on_date*, register it,
        and return the generated plan (tasks already sorted + filtered).
        """
        on_date = on_date or date.today()
 
        # Reuse an existing schedule if one already exists for (pet, date)
        for sched in self._schedules.values():
            if sched.pet_id == pet.pet_id and sched.date == on_date:
                return sched
 
        sched = DailySchedule(
            pet_id=pet.pet_id,
            pet_name=pet.name,
            date=on_date,
            time_budget_min=time_budget_min,
        )
        for task in pet.get_tasks():
            sched.add_task(task)
 
        self._schedules[sched.schedule_id] = sched
        return sched
 
    def build_all_schedules(
        self,
        owner: Owner,
        on_date: date | None = None,
    ) -> list[DailySchedule]:
        """Build one DailySchedule per pet for the given owner."""
        on_date = on_date or date.today()
        return [
            self.build_schedule_for_pet(pet, on_date)
            for pet in owner.get_pets()
        ]
 
    # ── formatting ────────────────────────────
 
    def format_schedule(self, schedule: DailySchedule) -> str:
        """
        Pretty-print a single pet's daily schedule for terminal output.
 
        Example
        -------
        ┌─────────────────────────────────────────────────────┐
        │  Biscuit (Golden Retriever)  ·  2025-06-10          │
        │  Time budget: 480 min  |  Used: 75 min  |  Free: 405│
        ├─────────────────────────────────────────────────────┤
        │  [○] 07:30 AM  WALK         Morning walk @ Park     │
        │  [○] 08:00 AM  FEEDING      Breakfast               │
        └─────────────────────────────────────────────────────┘
        """
        plan = schedule.generate_plan()
        width = 60
 
        header = (
            f"  {schedule.pet_name}  ·  {schedule.date}\n"
            f"  Budget: {schedule.time_budget_min} min  |  "
            f"Used: {schedule.total_time_used()} min  |  "
            f"Free: {schedule.time_remaining()} min"
        )
 
        top    = "┌" + "─" * width + "┐"
        mid    = "├" + "─" * width + "┤"
        bottom = "└" + "─" * width + "┘"
 
        def row(text: str) -> str:
            return "│ " + text.ljust(width - 1) + "│"
 
        lines = [top]
        for header_line in header.splitlines():
            lines.append(row(header_line))
 
        if plan:
            lines.append(mid)
            for task in plan:
                lines.append(row(task.display()))
        else:
            lines.append(mid)
            lines.append(row("  (no tasks scheduled)"))
 
        lines.append(bottom)
        return "\n".join(lines)
 
    def format_all_schedules(
        self, owner: Owner, on_date: date | None = None
    ) -> str:
        """Format today's schedule for every pet owned by *owner*."""
        on_date = on_date or date.today()
        schedules = self.build_all_schedules(owner, on_date)
        if not schedules:
            return "No pets registered."
        sections = [
            f"\n{'═' * 62}\n  TODAY'S SCHEDULE  —  {owner.name}\n{'═' * 62}"
        ]
        for sched in schedules:
            sections.append(self.format_schedule(sched))
        sections.append(f"{'═' * 62}\n")
        return "\n".join(sections)