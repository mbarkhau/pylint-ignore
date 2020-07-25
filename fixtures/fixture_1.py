def function_redefined():
    return 1

def function_redefined():
    return 1

def code_duplication():
    msg_id_count = {}

    def _entry_sort_key(e: Entry):
        frequency = -msg_id_count[e.msg_id]
        return frequency, e.msg_id

    return sorted(entries, key=_entry_sort_key)
