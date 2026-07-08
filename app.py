import streamlit as st
from datetime import date

from pawpal_system import Owner, Pet, Task, Scheduler, Priority, ScheduledTask

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")
st.title("🐾 PawPal+")
st.caption("A smart daily care planner for your pet.")

# ── Session state ────────────────────────────────────────────
if "owner" not in st.session_state:
    st.session_state.owner = None
if "schedule_result" not in st.session_state:
    st.session_state.schedule_result = None

# ── Sidebar: Owner setup ─────────────────────────────────────
with st.sidebar:
    st.header("👤 Owner Setup")
    owner_name  = st.text_input("Your name", value="Jordan")
    start_time  = st.text_input("Available from (HH:MM)", value="07:00")
    end_time    = st.text_input("Available until (HH:MM)", value="20:00")
    preferences = st.text_area("Preferences", placeholder="e.g. prefer morning walks")

    if st.button("💾 Save Owner"):
        try:
            st.session_state.owner = Owner(
                name=owner_name,
                available_start=start_time,
                available_end=end_time,
                preferences=preferences,
            )
            st.session_state.schedule_result = None
            st.success(f"Owner '{owner_name}' saved!")
        except ValueError as e:
            st.error(str(e))

    if st.session_state.owner:
        o = st.session_state.owner
        st.info(f"**{o.name}**  \n{o.available_start} – {o.available_end}  \n"
                f"{o.available_minutes()} min available")

# ── Guard ────────────────────────────────────────────────────
if not st.session_state.owner:
    st.warning("👈 Enter your name and availability in the sidebar to get started.")
    st.stop()

owner = st.session_state.owner

# ─────────────────────────────────────────────────────────────
# TAB LAYOUT
# ─────────────────────────────────────────────────────────────
tab_pets, tab_tasks, tab_schedule, tab_insights = st.tabs([
    "🐾 Pets", "📋 Tasks", "📅 Schedule", "🔍 Insights"
])

# ══════════════════════════════════════════════════════════════
# TAB 1 — Pets
# ══════════════════════════════════════════════════════════════
with tab_pets:
    st.subheader("Add a Pet")
    with st.form("add_pet_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            pet_name = st.text_input("Pet name", value="Mochi")
        with col2:
            species  = st.selectbox("Species", ["dog", "cat", "other"])
        with col3:
            age = st.number_input("Age (years)", min_value=0, max_value=30, value=2)
        special_needs  = st.text_input("Special needs", placeholder="e.g. needs harness")
        submitted_pet  = st.form_submit_button("➕ Add Pet")

    if submitted_pet:
        if pet_name.strip():
            owner.add_pet(Pet(
                name=pet_name.strip(), species=species,
                age=age, special_needs=special_needs.strip()
            ))
            st.success(f"Added pet: {pet_name}")
        else:
            st.warning("Please enter a pet name.")

    if owner.pets:
        st.subheader("Your Pets")
        for pet in owner.pets:
            done  = sum(1 for t in pet.tasks if t.completed)
            total = len(pet.tasks)
            with st.expander(f"{pet.species_emoji()} **{pet.name}** — {total} task(s), {done} done"):
                st.write(f"**Species:** {pet.species.capitalize()}")
                st.write(f"**Age:** {pet.age} year(s)")
                if pet.special_needs:
                    st.write(f"**Special needs:** {pet.special_needs}")
    else:
        st.info("No pets added yet.")

# ══════════════════════════════════════════════════════════════
# TAB 2 — Tasks
# ══════════════════════════════════════════════════════════════
with tab_tasks:
    if not owner.pets:
        st.info("Add a pet first before adding tasks.")
    else:
        st.subheader("Add a Task")
        with st.form("add_task_form"):
            pet_names    = [p.name for p in owner.pets]
            target_pet   = st.selectbox("Assign to pet", pet_names)
            col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
            with col1:
                task_title = st.text_input("Task title", value="Morning walk")
            with col2:
                duration   = st.number_input("Duration (min)", min_value=1, max_value=300, value=30)
            with col3:
                priority_str   = st.selectbox("Priority", ["high", "medium", "low"])
            with col4:
                preferred_time = st.selectbox("Preferred time", ["morning", "afternoon", "evening", "any"])
            col_a, col_b = st.columns(2)
            with col_a:
                notes     = st.text_input("Notes (optional)")
            with col_b:
                frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
            submitted_task = st.form_submit_button("➕ Add Task")

        if submitted_task:
            if task_title.strip():
                pet = next(p for p in owner.pets if p.name == target_pet)
                pet.add_task(Task(
                    title=task_title.strip(),
                    duration_minutes=int(duration),
                    priority=Priority.from_str(priority_str),
                    preferred_time=preferred_time,
                    notes=notes.strip(),
                    frequency=frequency,
                    due_date=date.today(),
                ))
                st.success(f"Added '{task_title}' to {target_pet}!")
            else:
                st.warning("Please enter a task title.")

        # ── Task list with sorting & filtering ──────────────
        st.subheader("View & Filter Tasks")
        all_tasks = owner.get_all_tasks()

        if all_tasks:
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                filter_pet = st.selectbox(
                    "Filter by pet",
                    ["All"] + [p.name for p in owner.pets]
                )
            with col_f2:
                filter_status = st.selectbox(
                    "Filter by status",
                    ["All", "Incomplete", "Completed"]
                )
            with col_f3:
                sort_mode = st.selectbox(
                    "Sort by",
                    ["Priority (high first)", "Time of day", "Duration"]
                )

            # Build a temporary scheduler just for sort/filter
            s = Scheduler(owner=owner, pet=owner.pets[0])

            # Apply filter
            pet_name_filter   = None if filter_pet == "All" else filter_pet
            completed_filter  = (
                None  if filter_status == "All"
                else (True if filter_status == "Completed" else False)
            )
            filtered = s.filter_tasks(pet_name=pet_name_filter, completed=completed_filter)

            # Apply sort
            if sort_mode == "Time of day":
                filtered = s.sort_by_time(filtered)
            elif sort_mode == "Duration":
                filtered = sorted(filtered, key=lambda t: t.duration_minutes)
            else:
                filtered = sorted(filtered, key=lambda t: -t.priority_value())

            if filtered:
                ICONS = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
                rows = []
                for t in filtered:
                    rows.append({
                        "Status":    "✅" if t.completed else "⬜",
                        "Priority":  ICONS.get(t.priority.name, "") + " " + t.priority.name.capitalize(),
                        "Task":      t.title,
                        "Duration":  f"{t.duration_minutes} min",
                        "Time":      t.preferred_time.capitalize(),
                        "Frequency": t.frequency.capitalize(),
                    })
                st.table(rows)
            else:
                st.info("No tasks match the current filter.")
        else:
            st.info("No tasks added yet.")

# ══════════════════════════════════════════════════════════════
# TAB 3 — Schedule
# ══════════════════════════════════════════════════════════════
with tab_schedule:
    st.subheader("Build Today's Schedule")

    if not owner.pets or not owner.get_all_tasks():
        st.info("Add at least one pet and one task before building a schedule.")
    else:
        if st.button("✨ Build Schedule", type="primary"):
            scheduler = Scheduler(owner=owner, pet=owner.pets[0])
            schedule, skipped = scheduler.build_schedule()
            conflicts = scheduler.detect_conflicts(schedule)
            st.session_state.schedule_result = (schedule, skipped, conflicts)

        if st.session_state.schedule_result:
            schedule, skipped, conflicts = st.session_state.schedule_result
            total_min = sum(e.task.duration_minutes for e in schedule)
            avail_min = owner.available_minutes()

            # ── Conflict warnings — shown prominently at top ──
            if conflicts:
                st.error("⚠️ Task Conflicts Detected — please review before your day starts:")
                for w in conflicts:
                    st.warning(w)
                st.divider()

            # ── Summary metrics ──
            col1, col2, col3 = st.columns(3)
            col1.metric("Tasks scheduled", len(schedule))
            col2.metric("Time used", f"{total_min} min")
            col3.metric("Time remaining", f"{avail_min - total_min} min")

            # ── Schedule cards ──
            st.markdown("### 🗓️ Today's Plan")
            ICONS = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
            for entry in schedule:
                icon = ICONS.get(entry.task.priority.name, "")
                recur = f" 🔁 {entry.task.frequency}" if entry.task.frequency != "once" else ""
                with st.expander(
                    f"{icon} **{entry.start_time} – {entry.end_time}** | {entry.task.title}{recur}"
                ):
                    st.write(f"**Duration:** {entry.task.duration_minutes} min")
                    st.write(f"**Priority:** {entry.task.priority.name.capitalize()}")
                    st.write(f"**Why:** {entry.reason}")
                    if entry.task.notes:
                        st.info(f"📝 {entry.task.notes}")

            # ── Skipped tasks ──
            if skipped:
                st.warning(f"⚠️ {len(skipped)} task(s) couldn't fit in your available time:")
                for t in skipped:
                    st.write(f"- **{t.title}** ({t.duration_minutes} min, {t.priority.name.capitalize()} priority)")

# ══════════════════════════════════════════════════════════════
# TAB 4 — Insights
# ══════════════════════════════════════════════════════════════
with tab_insights:
    st.subheader("🔍 Schedule Insights")
    all_tasks = owner.get_all_tasks()

    if not all_tasks:
        st.info("Add tasks to see insights.")
    else:
        col1, col2, col3 = st.columns(3)
        completed = [t for t in all_tasks if t.completed]
        pending   = [t for t in all_tasks if not t.completed]
        recurring = [t for t in all_tasks if t.frequency != "once"]

        col1.metric("Total tasks",    len(all_tasks))
        col2.metric("Completed",      len(completed))
        col3.metric("Recurring",      len(recurring))

        # Priority breakdown
        st.markdown("### Priority Breakdown")
        for label, icon in [("HIGH","🔴"), ("MEDIUM","🟡"), ("LOW","🟢")]:
            count = sum(1 for t in all_tasks if t.priority.name == label)
            st.write(f"{icon} **{label.capitalize()}:** {count} task(s)")

        # Pending by time slot
        if pending:
            st.markdown("### Pending Tasks by Time Slot")
            s = Scheduler(owner=owner, pet=owner.pets[0])
            sorted_pending = s.sort_by_time(pending)
            ICONS = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
            rows = [{
                "Time Slot": t.preferred_time.capitalize(),
                "Task":      t.title,
                "Priority":  ICONS.get(t.priority.name,"") + " " + t.priority.name.capitalize(),
                "Duration":  f"{t.duration_minutes} min",
                "Recurring": "🔁" if t.frequency != "once" else "",
            } for t in sorted_pending]
            st.table(rows)
