from app.models.item import Item

# In-memory "database"
items_db = {}
current_id = 1

def get_all_items():
    return [item.to_dict() for item in items_db.values()]

def get_item_by_id(id):
    return items_db.get(id, None)

def create_item(data):
    global current_id
    item = Item(current_id, data['name'], data.get('description', ''))
    items_db[current_id] = item
    current_id += 1
    return item

def update_item(id, data):
    if id not in items_db:
        return None
    item = items_db[id]
    item.name = data['name']
    item.description = data.get('description', item.description)
    return item

def delete_item(id):
    if id not in items_db:
        return False
    del items_db[id]
    return True