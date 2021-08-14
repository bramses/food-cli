import os
from pathlib import Path
from dotenv import load_dotenv
import asyncio
from functools import wraps
import aiohttp
import json

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
        'Notion-Version': os.getenv('NOTION_API_VERSION'),
    }

    async with aiohttp.ClientSession() as session:    
        async with session.get(url, headers=headers) as resp:
            print("Status:", resp.status)
            print("Content-type:", resp.headers['content-type'])

            jsonRes = await resp.json()
            print(jsonRes) 
            return jsonRes     

async def query_database(database_id, query={}):
    root_url = 'https://api.notion.com/v1/databases'
    url = root_url + '/' + database_id + '/query'
    headers = {
        'Authorization': 'Bearer ' + os.getenv('NOTION_API_KEY'),
        'Notion-Version': os.getenv('NOTION_API_VERSION'),
        'Content-Type': 'application/json',
    }

    print(json.dumps(query))

    async with aiohttp.ClientSession() as session:    
        async with session.post(url, headers=headers, data=json.dumps(query)) as resp:
            print("Status:", resp.status)
            print("Content-type:", resp.headers['content-type'])

            jsonRes = await resp.json()
            print(jsonRes) 
            return jsonRes  

async def query_database_name_list(food_names):
    query = {"filter": { "or": []  }}
    for food_name in food_names:
        query["filter"]["or"].append({"property": "Food", "text": { "equals": food_name}})
    return await query_database(os.getenv('NOTION_DATABASE_ID'), query)

# asyncio.run(query_database(os.getenv('NOTION_DATABASE_ID'), {"filter" : { "property" : "Food", "text": { "equals": "test food" } }}))
asyncio.run(query_database_name_list(["test food", "test food 2"]))