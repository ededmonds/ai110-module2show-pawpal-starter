import streamlit as st

# ── Step 1: Import backend classes ──────────────────────────
from pawpal_system import Owner, Pet, Task, Scheduler, Priority

# ── Page config ─────────────────────────────────────────────
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")
st.title("🐾 PawPal+")
st.caption("A smart daily care planner for your pet.")

# ── Step 2: Session state — create Owner once, persist it ───
# st.session_state acts like a dictionary that survives reruns.
# We only create the Owner if it doesn't already exist there.
if "owner" not in st.session_state:
    st.session_state.owner = None

if "schedule_result" not in st.session_state:
    st.session_state.schedule_result = None


# ── Sidebar: Owner setup ─────────────────────────────────────
with st.sidebar:
    st.header("👤 Owner Setup")

    owner_name    = st.text_input("Your name", value="Jordan")
    start_time    = st.text_input("Available from (HH:MM)", value="07:00")
    end_time      = st.text_input("Available until (HH:MM)", value="20:00")
    preferences   = st.text_area("Preferences", placeholder="e.g. prefer morning walks")

    if st.button("💾 Save Owner"):
        try:
            st.session_state.owner = Owner(
                name=owner_name,
                available_start=start_time,
                available_end=end_time,
                preferences=preferences,
            )
            st.success(f"Owner '{owner_name}' saved!")
        except ValueError as e:
            st.error(str(e))

    if st.session_state.owner:
        st.info(f"Current owner: **{st.session_state.owner.name}**  \n"
                f"Window: {st.session_state.owner.available_start} – "
                f"{st.session_state.owner.available_end}")


# ── Guard: require Owner before anything else ─────────────────
if not st.session_state.owner:
    st.warning("👈 Start by entering your name and availability in the sidebar.")
    st.stop()

owner = st.session_state.owner


# ── Step 3: Wire UI to logic ──────────────────────────────────

# ─── Add a Pet ───────────────────────────────────────────────
st.subheader("🐾 Add a Pet")

with st.form("add_pet_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species  = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        age      = st.number_input("Age (years)", min_value=0, max_value=30, value=2)
    special_needs = st.text_input("Special needs", placeholder="e.g. needs harness")
    submitted_pet = st.form_submit_button("➕ Add Pet")

if submitted_pet:
    if pet_name.strip():
        # Calls owner.add_pet() — the method from Phase 2
        new_pet = Pet(
            name=pet_name.strip(),
            species=species,
            age=age,
            special_needs=special_needs.strip(),
        )
        owner.add_pet(new_pet)
        st.success(f"Added {new_pet.species_emoji()} {new_pet.name}!")
    else:
        st.warning("Please enter a pet name.")

# Show current pets
if owner.pets:
    st.markdown("**Your pets:**")
    for pet in owner.pets:
        st.markdown(f"- {pet.species_emoji()} **{pet.name}** (age {pet.age})"
                    + (f" — {pet.special_needs}" if pet.special_needs else ""))
else:
    st.info("No pets added yet.")

st.divider()

# ─── Add a Task ──────────────────────────────────────────────
st.subheader("📋 Add a Task")

if not owner.pets:
    st.info("Add a pet first before adding tasks.")
else:
    with st.form("add_task_form"):
        pet_names   = [p.name for p in owner.pets]
        target_pet  = st.selectbox("Assign to pet", pet_names)

        col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
        with col1:
            task_title = st.text_input("Task title", value="Morning walk")
        with col2:
            duration   = st.number_input("Duration (min)", min_value=1, max_value=300, value=30)
        with col3:
            priority_str = st.selectbox("Priority", ["high", "medium", "low"])
        with col4:
            preferred_time = st.selectbox("Preferred time",
                                          ["any", "morning", "afternoon", "evening"])

        notes         = st.text_input("Notes (optional)")
        submitted_task = st.form_submit_button("➕ Add Task")

    if submitted_task:
        if task_title.strip():
            # Find the selected pet and call pet.add_task() — the method from Phase 2
            selected_pet = next(p for p in owner.pets if p.name == target_pet)
            new_task = Task(
                title=task_title.strip(),
                duration_minutes=int(duration),
                priority=Priority.from_str(priority_str),
                preferred_time=preferred_time,
                notes=notes.strip(),
            )
            selected_pet.add_task(new_task)
            st.success(f"Added task '{new_task.title}' to {selected_pet.name}!")
        else:
            st.warning("Please enter a task title.")

    # Show tasks per pet
    for pet in owner.pets:
        if pet.tasks:
            st.markdown(f"**{pet.species_emoji()} {pet.name}'s tasks:**")
            for t in pet.tasks:
                icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(t.priority.name, "")
                st.markdown(f"  {icon} {t.title} — {t.duration_minutes} min")

st.divider()

# ─── Generate Schedule ────────────────────────────────────────
st.subheader("📅 Generate Daily Schedule")

all_tasks = owner.get_all_tasks()

if st.button("✨ Build Schedule", type="primary"):
    if not all_tasks:
        st.warning("Add at least one task before generating a schedule.")
    elif not owner.pets:
        st.warning("Add at least one pet first.")
    else:
        # Wire Scheduler to the Owner — uses owner.get_all_tasks() internally
        scheduler = Scheduler(owner=owner, pet=owner.pets[0])
        schedule, skipped = scheduler.build_schedule()
        st.session_state.schedule_result = (schedule, skipped)

# Display schedule if it exists in session state
if st.session_state.schedule_result:
    schedule, skipped = st.session_state.schedule_result
    total_available = owner.available_minutes()
    total_scheduled = sum(e.task.duration_minutes for e in schedule)

    st.success(f"Schedule built for **{owner.name}** — {len(schedule)} task(s) planned")

    col_x, col_y = st.columns(2)
    col_x.metric("Tasks scheduled", len(schedule))
    col_y.metric("Time used", f"{total_scheduled} / {total_available} min")

    st.markdown("### 🗓️ Daily Plan")
    for entry in schedule:
        icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(entry.task.priority.name, "")
        with st.expander(
            f"{icon} {entry.start_time} – {entry.end_time} | **{entry.task.title}**"
        ):
            st.markdown(f"**Duration:** {entry.task.duration_minutes} min")
            st.markdown(f"**Priority:** {entry.task.priority.name.capitalize()}")
            st.markdown(f"**Why:** {entry.reason}")
            if entry.task.notes:
                st.markdown(f"**Notes:** {entry.task.notes}")

    if skipped:
        st.warning(f"⚠️ {len(skipped)} task(s) couldn't fit:")
        for t in skipped:
            st.markdown(f"- **{t.title}** ({t.duration_minutes} min)")
