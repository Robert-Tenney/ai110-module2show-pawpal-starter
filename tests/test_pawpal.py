from __future__ import annotations
 
import uuid
from dataclasses import dataclass, field
from datetime import date, time, timedelta
from typing import Optional
 
 
# ─────────────────────────────────────────────────────────────────────────────
# TaskDetail
# ─────────────────────────────────────────────────────────────────────────────
 
@dataclass
class TaskDetail:
    """
    The when/where specifics of a task on a given day.
    Composed 1-to-1 with a Task.
 
    Attributes
    ----------
    task_id        : ID of the parent Task
    scheduled_time : datetime.time object, e.g. time(8, 0) → 08:00
    location       : where the task happens, e.g. "Riverside Park"
    notes          : free-text notes, e.g. "Give 10 mg Apoquel with food"
    detail_id      : auto-generated UUID
    """
 
    task_id: str
    scheduled_time: time
    location: str = ""
    notes: str = ""
    detail_id: str = field(default_factory=lambda: str(uuid.uuid4()))
 
    def get_summary(self) -> str:
        """Return a compact one-liner suitable for terminal or UI display."""
        time_str = self.scheduled_time.strftime("%I:%M %p")
        parts = [time_str]
        if self.location:
            parts.append(f"@ {self.location}")
        if self.notes:
            parts.append(f"({self.notes})")
        return " ".join(parts)
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Task
# ─────────────────────────────────────────────────────────────────────────────
 
@dataclass
class Task:
    """
    A single pet-care activity.
 
    Attributes
    ----------
    task_type      : short label — "walk" | "feeding" | "medication" | …
    description    : free-text detail
    duration_min   : how many minutes the activity takes
    priority       : "high" | "medium" | "low"
    is_recurring   : True = repeats (daily by default), False = one-off
    frequency      : "daily" | "weekly" — controls next-occurrence offset
    is_completed   : toggled when the owner marks the task done
    due_date       : the calendar date this task instance is due
    pet_id         : which pet this task belongs to
    detail         : attached TaskDetail (when/where)
    """
 
    task_type: str
    description: str
    duration_min: int
    priority: str = "medium"          # "high" | "medium" | "low"
    is_recurring: bool = True
    frequency: str = "daily"          # "daily" | "weekly"
    is_completed: bool = False
    due_date: date = field(default_factory=date.today)
    pet_id: str = ""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    detail: Optional[TaskDetail] = field(default=None, repr=False)
 
    # ── mutators ──────────────────────────────────────────────────────────
 
    def edit_task(
        self,
        task_type: str | None = None,
        description: str | None = None,
        duration_min: int | None = None,
        priority: str | None = None,
        is_recurring: bool | None = None,
        frequency: str | None = None,
    ) -> None:
        """Update any subset of fields in place."""
        if task_type    is not None: self.task_type    = task_type
        if description  is not None: self.description  = description
        if duration_min is not None: self.duration_min = duration_min
        if priority     is not None: self.priority     = priority
        if is_recurring is not None: self.is_recurring = is_recurring
        if frequency    is not None: self.frequency    = frequency
 
    def mark_complete(self) -> Optional["Task"]:
        """
        Mark this task done and — for recurring tasks — automatically
        create and return a new Task instance for the next occurrence.
 
        Recurrence offsets
        ------------------
        * frequency == "daily"  → due_date + 1 day   (timedelta(days=1))
        * frequency == "weekly" → due_date + 7 days  (timedelta(weeks=1))
 
        Returns
        -------
        A new Task ready to be added to the pet's task list, or None if
        this task is not recurring.
 
        Example
        -------
        >>> next_task = walk.mark_complete()
        >>> if next_task:
        ...     biscuit.add_task(next_task)
        """
        self.is_completed = True
 
        if not self.is_recurring:
            return None
 
        # Calculate the next due date using timedelta
        offset = timedelta(days=1) if self.frequency == "daily" else timedelta(weeks=1)
        next_due = self.due_date + offset
 
        # Clone this task for the next occurrence — fresh ID, reset status
        next_task = Task(
            task_type=self.task_type,
            description=self.description,
            duration_min=self.duration_min,
            priority=self.priority,
            is_recurring=self.is_recurring,
            frequency=self.frequency,
            is_completed=False,
            due_date=next_due,
            pet_id=self.pet_id,
        )
 
        # Copy the scheduled time/location so the next occurrence is identical
        if self.detail:
            next_task.set_detail(
                scheduled_time=self.detail.scheduled_time,
                location=self.detail.location,
                notes=self.detail.notes,
            )
 
        return next_task
 
    def mark_incomplete(self) -> None:
        """Reset completion status."""
        self.is_completed = False
 
    def set_detail(
        self,
        scheduled_time: time,
        location: str = "",
        notes: str = "",
    ) -> TaskDetail:
        """Create and attach a TaskDetail to this task; return it."""
        self.detail = TaskDetail(
            task_id=self.task_id,
            scheduled_time=scheduled_time,
            location=location,
            notes=notes,
        )
        return self.detail
 
    # ── display ───────────────────────────────────────────────────────────
 
    def display(self) -> str:
        """Compact one-liner for terminal and Streamlit output."""
        status   = "✓" if self.is_completed else "○"
        time_str = (
            self.detail.scheduled_time.strftime("%I:%M %p")
            if self.detail else "--:--   "
        )
        location = f" @ {self.detail.location}" if self.detail and self.detail.location else ""
        notes    = f" | {self.detail.notes}"    if self.detail and self.detail.notes    else ""
        recur    = " ↺" if self.is_recurring else ""
        return (
            f"  [{status}] {time_str}  {self.task_type.upper():<12} "
            f"{self.description}{location}{notes}  "
            f"({self.duration_min} min, {self.priority}{recur})"
        )
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Pet
# ─────────────────────────────────────────────────────────────────────────────
 
@dataclass
class Pet:
    """
    A pet being cared for.
 
    Stores pet details and owns a list of Task objects.  The Scheduler
    accesses tasks exclusively through the public methods below.
    """
 
    name: str
    species: str        # "dog" | "cat" | "rabbit" | …
    breed: str = ""
    age_years: float = 0.0
    owner_id: str = ""
    pet_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    _tasks: list[Task] = field(default_factory=list, repr=False, compare=False)
 
    # ── task management ───────────────────────────────────────────────────
 
    def add_task(self, task: Task) -> None:
        """Attach a task to this pet and set its pet_id."""
        task.pet_id = self.pet_id
        self._tasks.append(task)
 
    def remove_task(self, task_id: str) -> bool:
        """Remove a task by ID; return True if the task was found."""
        before = len(self._tasks)
        self._tasks = [t for t in self._tasks if t.task_id != task_id]
        return len(self._tasks) < before
 
    def get_tasks(self) -> list[Task]:
        """Return a shallow copy of all tasks for this pet."""
        return list(self._tasks)
 
    def get_pending_tasks(self) -> list[Task]:
        """Return only tasks not yet marked complete."""
        return [t for t in self._tasks if not t.is_completed]
 
    def get_tasks_by_priority(self, priority: str) -> list[Task]:
        """Return tasks matching a given priority level."""
        return [t for t in self._tasks if t.priority == priority]
 
    # ── display ───────────────────────────────────────────────────────────
 
    def summary(self) -> str:
        """Short description string: 'Biscuit (Golden Retriever) — dog, 3 yrs'."""
        breed_str = f" ({self.breed})" if self.breed else ""
        age_str   = f", {self.age_years} yrs" if self.age_years else ""
        return f"{self.name}{breed_str} — {self.species}{age_str}"
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Owner
# ─────────────────────────────────────────────────────────────────────────────
 
@dataclass
class Owner:
    """
    A pet owner who manages one or more pets.
 
    The Scheduler retrieves all tasks via owner.get_all_tasks(), which
    iterates every pet's task list and returns a single flat list.
    """
 
    name: str
    email: str
    phone: str = ""
    owner_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    _pets: list[Pet] = field(default_factory=list, repr=False, compare=False)
 
    # ── pet management ────────────────────────────────────────────────────
 
    def add_pet(self, pet: Pet) -> Pet:
        """Register a pet under this owner; set its owner_id and return it."""
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
        """Case-insensitive name lookup; returns the first match or None."""
        return next(
            (p for p in self._pets if p.name.lower() == name.lower()), None
        )
 
    # ── task aggregation ──────────────────────────────────────────────────
 
    def get_all_tasks(self) -> list[Task]:
        """
        Return every task across ALL of this owner's pets.
        Primary method the Scheduler calls to build a daily plan.
        """
        tasks: list[Task] = []
        for pet in self._pets:
            tasks.extend(pet.get_tasks())
        return tasks
 
    def get_all_pending_tasks(self) -> list[Task]:
        """All incomplete tasks across every pet."""
        return [t for t in self.get_all_tasks() if not t.is_completed]
 
 
# ─────────────────────────────────────────────────────────────────────────────
# DailySchedule
# ─────────────────────────────────────────────────────────────────────────────
 
@dataclass
class DailySchedule:
    """
    Ordered daily plan for one pet on one calendar date.
 
    generate_plan() sorts by priority then scheduled time, and drops
    tasks that would exceed the owner's available time budget.
    """
 
    pet_id: str
    pet_name: str
    date: date
    time_budget_min: int = 480      # 8 hours of care time available by default
    tasks: list[Task] = field(default_factory=list)
    schedule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
 
    def add_task(self, task: Task) -> None:
        """Append a task to this schedule."""
        self.tasks.append(task)
 
    def total_time_used(self) -> int:
        """Sum of duration_min for every task currently in the schedule."""
        return sum(t.duration_min for t in self.tasks)
 
    def time_remaining(self) -> int:
        """Minutes left in the time budget after accounting for current tasks."""
        return self.time_budget_min - self.total_time_used()
 
    def generate_plan(self) -> list[Task]:
        """
        Return an ordered list of tasks that fit within the time budget.
 
        Sorting strategy
        ----------------
        Primary key   : priority rank  (high=0, medium=1, low=2)
        Secondary key : scheduled_time (tasks without a detail sort last)
 
        Filtering strategy
        ------------------
        Walk the sorted list and include a task only when its duration
        fits in the remaining budget.  Once the budget is exhausted,
        remaining tasks are silently skipped (no crash).
        """
        PRIORITY = {"high": 0, "medium": 1, "low": 2}
 
        sorted_tasks = sorted(
            self.tasks,
            key=lambda t: (
                PRIORITY.get(t.priority, 99),
                t.detail.scheduled_time if t.detail else time(23, 59),
            ),
        )
 
        plan: list[Task] = []
        remaining = self.time_budget_min
        for task in sorted_tasks:
            if task.duration_min <= remaining:
                plan.append(task)
                remaining -= task.duration_min
        return plan
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Conflict namedtuple-style dataclass
# ─────────────────────────────────────────────────────────────────────────────
 
@dataclass
class Conflict:
    """
    Represents a scheduling conflict between two tasks.
 
    Produced by Scheduler.detect_conflicts() and formatted by
    Scheduler.format_conflicts().
    """
 
    pet_name: str
    conflict_time: str          # "HH:MM AM/PM"
    task_a: str                 # description of first task
    task_b: str                 # description of second task
 
    def message(self) -> str:
        """Human-readable warning suitable for terminal or Streamlit st.warning()."""
        return (
            f"⚠  CONFLICT  [{self.pet_name}]  {self.conflict_time}  — "
            f'"{self.task_a}" and "{self.task_b}" are both scheduled at the same time.'
        )
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Scheduler  ← the "brain"
# ─────────────────────────────────────────────────────────────────────────────
 
class Scheduler:
    """
    Orchestration engine.  The Streamlit UI talks primarily to this class.
 
    Phase 4 public API (new methods)
    ---------------------------------
    sort_by_time(tasks)              Sort a task list by scheduled_time.
    filter_tasks(tasks, ...)         Filter by pet name and/or completion status.
    detect_conflicts(schedule)       Return a list of Conflict objects.
    format_conflicts(conflicts)      Pretty-print conflict warnings.
    complete_and_reschedule(task, pet)  Mark done and auto-add next occurrence.
    """
 
    def __init__(self) -> None:
        self._owners: dict[str, Owner] = {}
        self._schedules: dict[str, DailySchedule] = {}     # schedule_id → schedule
 
    # ── owner / pet registration ──────────────────────────────────────────
 
    def register_owner(self, owner: Owner) -> Owner:
        """Register an owner with the scheduler and return it."""
        self._owners[owner.owner_id] = owner
        return owner
 
    def get_owner(self, owner_id: str) -> Owner | None:
        """Look up a registered owner by ID."""
        return self._owners.get(owner_id)
 
    def add_pet_to_owner(self, pet: Pet, owner: Owner) -> Pet:
        """Add *pet* to *owner* and return the pet."""
        return owner.add_pet(pet)
 
    # ── task retrieval ────────────────────────────────────────────────────
 
    def get_all_tasks(self, owner: Owner) -> list[Task]:
        """
        Retrieve every task for every pet owned by *owner*.
 
        Flow
        ----
        scheduler.get_all_tasks(owner)
            → owner.get_all_tasks()
                → pet.get_tasks()  (for every pet)
                    → flat list of Task objects
        """
        return owner.get_all_tasks()
 
    def get_tasks_for_pet(self, owner: Owner, pet_name: str) -> list[Task]:
        """Return all tasks for a single pet identified by name."""
        pet = owner.find_pet_by_name(pet_name)
        return pet.get_tasks() if pet else []
 
    def get_pending_tasks(self, owner: Owner) -> list[Task]:
        """Return all incomplete tasks across every pet owned by *owner*."""
        return owner.get_all_pending_tasks()
 
    # ── Phase 4 · SORTING ─────────────────────────────────────────────────
 
    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """
        Return *tasks* sorted in ascending order by scheduled_time.
 
        Uses a lambda as the sort key so Python's built-in Timsort
        (O(n log n)) handles the heavy lifting.  Tasks without a
        TaskDetail (no time set) are sorted to the end of the list.
 
        Parameters
        ----------
        tasks : list[Task]
            Any flat list of Task objects — e.g. from get_all_tasks() or
            filter_tasks().
 
        Returns
        -------
        list[Task]
            A new sorted list; the original list is not mutated.
 
        Example
        -------
        >>> sorted_tasks = scheduler.sort_by_time(biscuit.get_tasks())
        """
        return sorted(
            tasks,
            key=lambda t: t.detail.scheduled_time if t.detail else time(23, 59),
        )
 
    # ── Phase 4 · FILTERING ───────────────────────────────────────────────
 
    def filter_tasks(
        self,
        tasks: list[Task],
        *,
        pet_name: str | None = None,
        completed: bool | None = None,
        owner: Owner | None = None,
    ) -> list[Task]:
        """
        Filter a list of tasks by pet name and/or completion status.
 
        Parameters
        ----------
        tasks     : source list to filter (not mutated)
        pet_name  : keep only tasks whose pet has this name (case-insensitive).
                    Requires *owner* to be supplied for the name→ID lookup.
        completed : True  → keep only completed tasks
                    False → keep only pending tasks
                    None  → no status filter applied
        owner     : the Owner used for pet name → pet_id resolution
 
        Returns
        -------
        A new filtered list.
 
        Examples
        --------
        >>> # Only incomplete tasks for Biscuit
        >>> scheduler.filter_tasks(all_tasks, pet_name="Biscuit",
        ...                        completed=False, owner=sarah)
 
        >>> # All completed tasks regardless of pet
        >>> scheduler.filter_tasks(all_tasks, completed=True)
        """
        result = list(tasks)
 
        # Filter by pet name (resolve name → pet_id via owner)
        if pet_name is not None and owner is not None:
            pet = owner.find_pet_by_name(pet_name)
            if pet:
                result = [t for t in result if t.pet_id == pet.pet_id]
            else:
                result = []   # named pet not found → empty
 
        # Filter by completion status
        if completed is not None:
            result = [t for t in result if t.is_completed == completed]
 
        return result
 
    # ── Phase 4 · RECURRING TASKS ─────────────────────────────────────────
 
    def complete_and_reschedule(self, task: Task, pet: Pet) -> Optional[Task]:
        """
        Mark *task* complete and — if it is recurring — automatically
        create the next occurrence and register it on *pet*.
 
        Uses Task.mark_complete(), which uses timedelta internally:
          daily  → due_date + timedelta(days=1)
          weekly → due_date + timedelta(weeks=1)
 
        Parameters
        ----------
        task : the Task to mark done
        pet  : the Pet whose task list receives the next occurrence
 
        Returns
        -------
        The newly created next-occurrence Task, or None for one-off tasks.
 
        Example
        -------
        >>> next_walk = scheduler.complete_and_reschedule(walk, biscuit)
        >>> print(f"Next walk due: {next_walk.due_date}")
        """
        next_task = task.mark_complete()     # sets is_completed = True
        if next_task:
            pet.add_task(next_task)
        return next_task
 
    # ── Phase 4 · CONFLICT DETECTION ──────────────────────────────────────
 
    def detect_conflicts(self, schedule: DailySchedule) -> list[Conflict]:
        """
        Detect tasks for the same pet that share an exact scheduled_time.
 
        Strategy
        --------
        Build a dict keyed by scheduled_time; if a time slot already has
        an entry, record a Conflict.  This is O(n) and never raises —
        it returns warnings rather than crashing.
 
        Tradeoff: only *exact* time matches are caught.  Two tasks at
        08:00 and 08:10 that together run for 40 minutes will NOT be
        flagged even if they physically overlap.  (Documented in
        reflection.md §2b.)
 
        Parameters
        ----------
        schedule : a DailySchedule whose task list is inspected
 
        Returns
        -------
        list[Conflict] — empty if no conflicts found.
 
        Example
        -------
        >>> conflicts = scheduler.detect_conflicts(biscuit_schedule)
        >>> for c in conflicts:
        ...     print(c.message())
        """
        seen: dict[time, Task] = {}
        conflicts: list[Conflict] = []
 
        for task in schedule.tasks:
            if task.detail is None:
                continue                        # no scheduled time — skip
 
            t = task.detail.scheduled_time
            if t in seen:
                conflicts.append(
                    Conflict(
                        pet_name=schedule.pet_name,
                        conflict_time=t.strftime("%I:%M %p"),
                        task_a=seen[t].description,
                        task_b=task.description,
                    )
                )
            else:
                seen[t] = task
 
        return conflicts
 
    def format_conflicts(self, conflicts: list[Conflict]) -> str:
        """
        Return a formatted block of conflict warnings, or a clean message
        if no conflicts were found.
 
        Parameters
        ----------
        conflicts : output of detect_conflicts()
        """
        if not conflicts:
            return "  ✓  No scheduling conflicts detected."
        lines = [f"  {c.message()}" for c in conflicts]
        return "\n".join(lines)
 
    # ── schedule building ─────────────────────────────────────────────────
 
    def build_schedule_for_pet(
        self,
        pet: Pet,
        on_date: date | None = None,
        time_budget_min: int = 480,
    ) -> DailySchedule:
        """
        Create (or retrieve an existing) DailySchedule for *pet* on *on_date*.
 
        Parameters
        ----------
        pet            : the Pet to schedule
        on_date        : calendar date; defaults to today
        time_budget_min: available care minutes; default 480 (8 hours)
 
        Returns
        -------
        DailySchedule with all of *pet*'s current tasks loaded.
        """
        on_date = on_date or date.today()
 
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
 
    # ── formatting ────────────────────────────────────────────────────────
 
    def format_schedule(self, schedule: DailySchedule) -> str:
        """
        Pretty-print a single pet's daily schedule for terminal output.
 
        Layout
        ------
        ┌────────────────────────────────────────────────────────────┐
        │   Biscuit  ·  2025-06-10                                   │
        │   Budget: 480 min  |  Used: 75 min  |  Free: 405 min       │
        ├────────────────────────────────────────────────────────────┤
        │   [○] 07:30 AM  WALK         Morning walk ↺                │
        └────────────────────────────────────────────────────────────┘
        """
        plan  = schedule.generate_plan()
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
        for line in header.splitlines():
            lines.append(row(line))
 
        lines.append(mid)
        if plan:
            for task in plan:
                lines.append(row(task.display()))
        else:
            lines.append(row("  (no tasks scheduled)"))
 
        lines.append(bottom)
        return "\n".join(lines)
 
    def format_all_schedules(
        self, owner: Owner, on_date: date | None = None
    ) -> str:
        """Format today's schedule for every pet owned by *owner*."""
        on_date   = on_date or date.today()
        schedules = self.build_all_schedules(owner, on_date)
        if not schedules:
            return "No pets registered."
        banner = f"\n{'═' * 62}\n  TODAY'S SCHEDULE  —  {owner.name}\n{'═' * 62}"
        parts  = [banner] + [self.format_schedule(s) for s in schedules]
        parts.append(f"{'═' * 62}\n")
        return "\n".join(parts)
 