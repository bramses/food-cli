import os
from pathlib import Path
from dotenv import load_dotenv
import asyncio
from functools import wraps
import aiohttp

def async_action(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapped

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

async def get_notion_row(names):
    pass

async def get_database(database_id):
    root_url = 'https://api.notion.com/v1/databases'
    url = root_url + '/' + database_id
    headers = {
        'Authorization': 'Bearer ' + os.getenv('NOTION_API_KEY'),
        'Content-Type': 'application/json'
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            return await resp.json()