import json
import time
from redis.commands.search.field import NumericField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from redis.commands.json.path import Path


CHAT_IDX_NAME = 'idx:chat'
CHAT_IDX_PREFIX = 'chat:'


# CHATS
def create_chat_index(rdb):
    try:
        schema = (
            NumericField('$.created', as_name='created', sortable=True),
        )
        rdb.ft(CHAT_IDX_NAME).create_index(
            fields=schema,
            definition=IndexDefinition(prefix=[CHAT_IDX_PREFIX], index_type=IndexType.JSON)
        )
        print(f"Chat index '{CHAT_IDX_NAME}' created successfully")
    except Exception as e:
        print(f"Error creating chat index '{CHAT_IDX_NAME}': {e}")

def create_chat(rdb, chat_id, created):
    chat = {'id': chat_id, 'created': created, 'messages': []}
    rdb.json().set(CHAT_IDX_PREFIX + chat_id, "$", chat)
    return chat

def add_chat_messages(rdb, chat_id, messages):
    rdb.json().arrappend(CHAT_IDX_PREFIX + chat_id, '$.messages', *messages)

def get_chat_messages(rdb, chat_id, last_n=None):
    if last_n is None:
        messages = rdb.json().get(CHAT_IDX_PREFIX + chat_id, '$.messages[*]')
    else:
        messages = rdb.json().get(CHAT_IDX_PREFIX + chat_id, f'$.messages[-{last_n}:]')
    return [{'role': m['role'], 'content': m['content']} for m in messages] if messages else []

def save_full_chat_history_to_redis(rdb, chat_id, previous_chat_history):
    """
    Store full chat history into Redis in one go.
    """
    if not chat_exists(rdb, chat_id):
        created = int(time.time())
        create_chat(rdb, chat_id, created)

    messages = []
    for chat in previous_chat_history:
        user_message = {"role": "user", "content": chat["user"]}
        assistant_message = {"role": "assistant", "content": chat["bot"]}
        messages.extend([user_message, assistant_message])

    add_chat_messages(rdb, chat_id, messages)
    
def get_chat(rdb, chat_id):
    return rdb.json().get(chat_id)


def chat_exists(rdb, chat_id):
    return rdb.exists(CHAT_IDX_PREFIX + chat_id)


def get_all_chats(rdb):
    q = Query('*').sort_by('created', asc=False)
    count = rdb.ft(CHAT_IDX_NAME).search(q.paging(0, 0))
    res = rdb.ft(CHAT_IDX_NAME).search(q.paging(0, count.total))
    return [json.loads(doc.json) for doc in res.docs]

def delete_chat(rdb, chat_id):
    key = CHAT_IDX_PREFIX + chat_id
    if rdb.exists(key):
        rdb.delete(key)
        print(f"Chat '{chat_id}' deleted successfully")
        return True
    else:
        print(f"Chat '{chat_id}' not found")
        return False
