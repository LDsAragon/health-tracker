"""Paquete de acceso a datos. Re-exporta todo para que `import database as db` no cambie."""
from .conn import get_db, db_path, DB_PATH, _columns, snapshot_to, is_valid_db, restore_from, reset_db
from .schema import SCHEMA, MIGRATIONS, init_db
from .notes import (
    add_note, update_note, delete_note,
    get_notes_for_date, get_notes_range, search_notes,
)
from .events import (
    get_recurring_events, add_recurring_event, update_recurring_event,
    delete_recurring_event, end_recurring_event, set_recurring_visibility,
    event_applies, get_completion, complete_event, uncomplete_event,
    get_completions_range, get_completion_stats,
)
from .journal import (
    get_journal_categories, add_journal_category, update_journal_category,
    delete_journal_category, get_journal_entries_for_date,
    get_journal_entries_range, add_journal_entry, update_journal_entry,
    delete_journal_entry,
)
from .todos import (
    get_todos_for_date, add_todo, toggle_todo, update_todo, move_todo,
    delete_todo, reorder_todos, get_todos_range, get_todo_counts_range,
)
from .settings import get_setting, set_setting, get_all_settings
from .stats import (
    numeric_series, bool_counts, option_distribution, chartable_fields, build_series, grouped_series,
    time_summary, TIME_TYPES,
)
from .charts import get_charts, add_chart, delete_chart
