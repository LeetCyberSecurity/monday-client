def update_items_page_in_place(data, modify_fn):
    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'items_page' and isinstance(value, dict):
                modify_fn(value)
                return True  # Stop after first occurrence
            else:
                if update_items_page_in_place(value, modify_fn):
                    return True
    elif isinstance(data, list):
        for item in data:
            if update_items_page_in_place(item, modify_fn):
                return True
    return False
