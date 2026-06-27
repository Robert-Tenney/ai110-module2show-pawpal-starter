"""
app.py
------
PawPal+ Streamlit UI — Phase 6
Connects the Scheduler logic layer to an interactive web interface.

Run with:  streamlit run app.py  (requires Python ≤ 3.12)
"""

import streamlit as st
from datetime import date, time
from pawpal_system import Owner, Pet, Task, Scheduler, DailySchedule

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="PawPal+",
    page_icon="🐾",
    layout="wide",
)

# ─────────────────────────────────────────────
# Session state bootstrap
# ─────────────────────────────────────────────
if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler()
if "owner" not in st.session_state:
    st.session_state.owner = None
if "pets" not in st.session_state:
    st.session_state.pets = {}          # pet_name → Pet

scheduler: Scheduler = st.session_state.scheduler


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def get_owner() -> Owner | None:
    return st.session_state.owner

def get_pets() -> dict:
    return st.session_state.pets

def all_tasks():
    owner = get_owner()
    if owner:
        return scheduler.get_all_tasks(owner)
    return []


# ─────────────────────────────────────────────
# Sidebar — Owner + Pet setup
# ─────────────────────────────────────────────
with st.sidebar:
    st.title("🐾 PawPal+")
    st.markdown("---")

    # ── Owner ────────────────────────────────
    st.subheader("👤 Owner Info")
    with st.form("owner_form"):
        owner_name  = st.text_input("Your name",  placeholder="Sarah Chen")
        owner_email = st.text_input("Email",       placeholder="sarah@example.com")
        owner_phone = st.text_input("Phone",       placeholder="555-0101")
        save_owner  = st.form_submit_button("Save Owner")

    if save_owner and owner_name and owner_email:
        owner = Owner(name=owner_name, email=owner_email, phone=owner_phone)
        scheduler.register_owner(owner)
        st.session_state.owner = owner
        st.success(f"Welcome, {owner_name}!")

    if get_owner():
        st.caption(f"Logged in as **{get_owner().name}**")

    st.markdown("---")

    # ── Add Pet ──────────────────────────────
    st.subheader("🐶 Add a Pet")
    with st.form("pet_form"):
        pet_name    = st.text_input("Pet name",   placeholder="Biscuit")
        pet_species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
        pet_breed   = st.text_input("Breed",      placeholder="Golden Retriever")
        pet_age     = st.number_input("Age (years)", min_value=0.0, step=0.5)
        add_pet     = st.form_submit_button("Add Pet")

    if add_pet:
        if not get_owner():
            st.error("Please save owner info first.")
        elif not pet_name:
            st.error("Pet name is required.")
        elif pet_name in get_pets():
            st.warning(f"{pet_name} is already registered.")
        else:
            pet = Pet(name=pet_name, species=pet_species,
                      breed=pet_breed, age_years=pet_age)
            scheduler.add_pet_to_owner(pet, get_owner())
            get_pets()[pet_name] = pet
            st.success(f"{pet_name} added!")

    if get_pets():
        st.markdown("**Your pets:**")
        for name in get_pets():
            st.caption(f"• {name}")


# ─────────────────────────────────────────────
# Main area — tabs
# ─────────────────────────────────────────────
st.title("🐾 PawPal+ — Daily Pet Care Planner")

if not get_owner():
    st.info("👈 Start by entering your owner info in the sidebar.")
    st.stop()

if not get_pets():
    st.info("👈 Add at least one pet in the sidebar to get started.")
    st.stop()

tab_schedule, tab_tasks, tab_conflicts, tab_filter = st.tabs([
    "📅 Today's Schedule",
    "➕ Add Task",
    "⚠️ Conflict Check",
    "🔍 Filter & Sort",
])


# ─────────────────────────────────────────────
# TAB 1 — Today's Schedule
# ─────────────────────────────────────────────
with tab_schedule:
    st.header("Today's Schedule")
    today = date.today()
    st.caption(f"📆 {today.strftime('%A, %B %d, %Y')}")

    for pet_name, pet in get_pets().items():
        sched = scheduler.build_schedule_for_pet(pet, on_date=today)
        plan  = sched.generate_plan()

        with st.expander(f"🐾 {pet_name}  —  {pet.summary()}", expanded=True):
            col1, col2, col3 = st.columns(3)
            col1.metric("Time Budget",  f"{sched.time_budget_min} min")
            col2.metric("Time Used",    f"{sched.total_time_used()} min")
            col3.metric("Time Free",    f"{sched.time_remaining()} min")

            if not plan:
                st.info("No tasks scheduled for today.")
            else:
                rows = []
                for task in plan:
                    time_str = (
                        task.detail.scheduled_time.strftime("%I:%M %p")
                        if task.detail else "—"
                    )
                    location = task.detail.location if task.detail and task.detail.location else "—"
                    notes    = task.detail.notes    if task.detail and task.detail.notes    else "—"
                    status   = "✅ Done" if task.is_completed else "⏳ Pending"
                    recur    = "↺ Daily" if task.is_recurring and task.frequency == "daily" \
                               else ("↺ Weekly" if task.is_recurring else "One-off")
                    rows.append({
                        "Time":        time_str,
                        "Type":        task.task_type.title(),
                        "Description": task.description,
                        "Location":    location,
                        "Notes":       notes,
                        "Duration":    f"{task.duration_min} min",
                        "Priority":    task.priority.title(),
                        "Recurrence":  recur,
                        "Status":      status,
                    })
                st.table(rows)

            # Mark complete buttons
            st.markdown("**Mark tasks complete:**")
            pending = [t for t in plan if not t.is_completed]
            if not pending:
                st.success("All tasks completed for today! 🎉")
            else:
                for task in pending:
                    label = (
                        f"{task.detail.scheduled_time.strftime('%I:%M %p')} — "
                        if task.detail else ""
                    )
                    if st.button(f"✓ Complete: {label}{task.description}",
                                 key=f"complete_{task.task_id}"):
                        next_task = scheduler.complete_and_reschedule(task, pet)
                        if next_task:
                            st.success(
                                f"✅ '{task.description}' done! "
                                f"Next occurrence scheduled for {next_task.due_date}."
                            )
                        else:
                            st.success(f"✅ '{task.description}' marked complete.")
                        st.rerun()


# ─────────────────────────────────────────────
# TAB 2 — Add Task
# ─────────────────────────────────────────────
with tab_tasks:
    st.header("Add a Task")

    with st.form("task_form"):
        col1, col2 = st.columns(2)

        with col1:
            selected_pet = st.selectbox("Pet", list(get_pets().keys()))
            task_type    = st.selectbox("Task type",
                           ["walk", "feeding", "medication", "grooming",
                            "enrichment", "vet visit", "other"])
            description  = st.text_input("Description",
                           placeholder="Morning walk around Riverside Park")
            duration     = st.number_input("Duration (minutes)", min_value=1,
                           max_value=480, value=30)
            priority     = st.selectbox("Priority", ["high", "medium", "low"])

        with col2:
            sched_time   = st.time_input("Scheduled time", value=time(8, 0))
            location     = st.text_input("Location", placeholder="Riverside Park")
            notes        = st.text_area("Notes", placeholder="e.g. Give 10mg Apoquel with food",
                           height=80)
            is_recurring = st.checkbox("Recurring task", value=True)
            frequency    = st.selectbox("Frequency", ["daily", "weekly"],
                           disabled=not is_recurring)

        add_task = st.form_submit_button("➕ Add Task", use_container_width=True)

    if add_task:
        if not description:
            st.error("Please enter a description.")
        else:
            pet  = get_pets()[selected_pet]
            task = Task(
                task_type=task_type,
                description=description,
                duration_min=int(duration),
                priority=priority,
                is_recurring=is_recurring,
                frequency=frequency if is_recurring else "daily",
            )
            task.set_detail(
                scheduled_time=sched_time,
                location=location,
                notes=notes,
            )
            pet.add_task(task)

            # Immediately check for conflicts after adding
            sched     = scheduler.build_schedule_for_pet(pet, on_date=date.today())
            conflicts = scheduler.detect_conflicts(sched)
            if conflicts:
                for c in conflicts:
                    st.warning(c.message())
            else:
                st.success(
                    f"✅ Task '{description}' added to {selected_pet}'s schedule "
                    f"at {sched_time.strftime('%I:%M %p')}."
                )


# ─────────────────────────────────────────────
# TAB 3 — Conflict Check
# ─────────────────────────────────────────────
with tab_conflicts:
    st.header("⚠️ Conflict Check")
    st.markdown(
        "Scans each pet's schedule for tasks booked at the exact same time."
    )

    any_conflicts = False
    for pet_name, pet in get_pets().items():
        sched     = scheduler.build_schedule_for_pet(pet, on_date=date.today())
        conflicts = scheduler.detect_conflicts(sched)

        st.subheader(f"🐾 {pet_name}")
        if not conflicts:
            st.success("✓ No conflicts detected.")
        else:
            any_conflicts = True
            for c in conflicts:
                st.warning(c.message())
                st.caption(
                    "💡 Tip: go to **Add Task** and adjust the scheduled "
                    "time of one of these tasks to resolve the conflict."
                )

    if not any_conflicts:
        st.balloons()


# ─────────────────────────────────────────────
# TAB 4 — Filter & Sort
# ─────────────────────────────────────────────
with tab_filter:
    st.header("🔍 Filter & Sort Tasks")

    col1, col2, col3 = st.columns(3)
    with col1:
        filter_pet = st.selectbox(
            "Filter by pet",
            ["All pets"] + list(get_pets().keys()),
        )
    with col2:
        filter_status = st.selectbox(
            "Filter by status",
            ["All", "Pending only", "Completed only"],
        )
    with col3:
        sort_by = st.selectbox("Sort by", ["Scheduled time", "Priority"])

    # Build filtered list
    tasks = all_tasks()

    pet_name_arg = None if filter_pet == "All pets" else filter_pet
    completed_arg = None
    if filter_status == "Pending only":
        completed_arg = False
    elif filter_status == "Completed only":
        completed_arg = True

    filtered = scheduler.filter_tasks(
        tasks,
        pet_name=pet_name_arg,
        completed=completed_arg,
        owner=get_owner(),
    )

    # Sort
    if sort_by == "Scheduled time":
        filtered = scheduler.sort_by_time(filtered)
    else:
        PRIORITY = {"high": 0, "medium": 1, "low": 2}
        filtered = sorted(filtered, key=lambda t: PRIORITY.get(t.priority, 99))

    st.markdown(f"**{len(filtered)} task(s) found**")

    if not filtered:
        st.info("No tasks match the selected filters.")
    else:
        # Look up pet name from pet_id
        pet_id_to_name = {p.pet_id: n for n, p in get_pets().items()}
        rows = []
        for task in filtered:
            time_str = (
                task.detail.scheduled_time.strftime("%I:%M %p")
                if task.detail else "—"
            )
            rows.append({
                "Pet":         pet_id_to_name.get(task.pet_id, "?"),
                "Time":        time_str,
                "Type":        task.task_type.title(),
                "Description": task.description,
                "Priority":    task.priority.title(),
                "Duration":    f"{task.duration_min} min",
                "Status":      "✅ Done" if task.is_completed else "⏳ Pending",
            })
        st.table(rows)