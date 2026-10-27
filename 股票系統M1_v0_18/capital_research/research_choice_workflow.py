"""External immutable Journal IO for choice records; no numerical RUN route."""
from rotation_research.store import Journal
from .research_choice import choose_saved, validate_record


def select_and_save(root, key, request):
    value = choose_saved(request)
    validate_record(value)
    store = Journal(root)
    try:
        saved = store.save(key, value)
        validate_record(saved['value'])
    except ValueError as exc:
        not_saved = str(exc).startswith(('Identity conflict:', 'Invalid identity'))
        return dict(storage_status='NOT_SAVED' if not_saved else 'UNKNOWN', reasons=[str(exc)], record=None,
            saved_files_preserved=True)
    except OSError as exc:
        return dict(storage_status='UNKNOWN', reasons=[str(exc)], record=None, saved_files_preserved=True)
    return dict(storage_status='SAVED_AND_READ_BACK', reasons=[], record=saved)


def read_choice(root, key):
    saved = Journal(root).read(key)
    validate_record(saved['value'])
    return dict(storage_status='READ_ONLY', reasons=[], record=saved)
