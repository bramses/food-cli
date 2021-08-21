from datetime import datetime
import pytz
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncio
from functools import wraps
import aiohttp
import json
import string
import random

def async_action(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapped

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

async def on_request_start(
        session, trace_config_ctx, params):
    print("Starting request")
    print(session, trace_config_ctx, params)
    

async def on_request_end(session, trace_config_ctx, params):
    print("Ending request")
    print(session, trace_config_ctx, params)

trace_config = aiohttp.TraceConfig()
trace_config.on_request_start.append(on_request_start)
trace_config.on_request_end.append(on_request_end)

async def create_page(properties, database_id=os.getenv('NOTION_DATABASE_ID')):
    root_url = 'https://api.notion.com/v1/pages'

    headers = {
        'Authorization': 'Bearer ' + os.getenv('NOTION_API_KEY'),
        'Content-Type': 'application/json',
        'Notion-Version': os.getenv('NOTION_API_VERSION'),
    }

    now = datetime.now()

    data = {
        'parent': { "database_id" : database_id },
        'properties': properties,
        'created_time': now.isoformat() + 'Z',
    }

    print(json.dumps(data, indent=4))

    async with aiohttp.ClientSession() as session:
        async with session.post(root_url, headers=headers, json=data) as resp:
            jsonRes = await resp.json()
            print(json.dumps(jsonRes, indent=4))
            if jsonRes['object'] == 'error':
                raise Exception(jsonRes['message'])
            return jsonRes

async def get_database(database_id=os.getenv('NOTION_DATABASE_ID')):
    root_url = 'https://api.notion.com/v1/databases'
    url = root_url + '/' + database_id
    headers = {
        'Authorization': 'Bearer ' + os.getenv('NOTION_API_KEY'),
        'Notion-Version': os.getenv('NOTION_API_VERSION'),
    }

    async with aiohttp.ClientSession() as session:    
        async with session.get(url, headers=headers) as resp:
            jsonRes = await resp.json()
            return jsonRes     

async def query_database(database_id=os.getenv('NOTION_DATABASE_ID'), query={}):
    root_url = 'https://api.notion.com/v1/databases'
    url = root_url + '/' + database_id + '/query'
    headers = {
        'Authorization': 'Bearer ' + os.getenv('NOTION_API_KEY'),
        'Notion-Version': os.getenv('NOTION_API_VERSION'),
        'Content-Type': 'application/json',
    }

    async with aiohttp.ClientSession() as session:    
        async with session.post(url, headers=headers, data=json.dumps(query)) as resp:
            jsonRes = await resp.json()
            return jsonRes

def generate_random_short_string():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))

def set_property_value(property_name, property_value, validation_name=None):
    if property_value == 'title':
        try:
           property_value = {'title' : [{'text': {'content': property_name.lower()}}], 'name': validation_name, 'type': 'title', 'id': generate_random_short_string() }
           return property_value
        except:
            return {'title' : [{'text': {'content': ''}}], 'name': validation_name, 'type': 'title' }
    elif property_value == 'rich_text':
        try:
            if property_name is None:
                raise Exception('Rich text property is empty')
            property_value = {'rich_text': [{'text': {'content': property_name}}], 'name': validation_name, 'type': 'rich_text' }
            return property_value
        except:
            return {'rich_text': [{'text': {'content': 'brandless'}}], 'name': validation_name, 'type': 'rich_text' }
    elif property_value == 'number':
        try:
            property_value = {'number': property_name, 'name': validation_name, 'type': 'number' }
            return property_value
        except:
            return {'number': -1, 'name': validation_name, 'type': 'number' }
    elif property_value == 'checkbox':
        try:
            property_value = {'checkbox': property_name, 'name': validation_name, 'type': 'checkbox' }
            return property_value
        except:
            return {'checkbox': False, 'name': validation_name, 'type': 'checkbox' }
    elif property_value == 'select':
        try:
            if property_name == '':
                property_value = {'select': { 'name': 'default' }, 'name': validation_name, 'type': 'select' }
            else:
                property_value = {'select': { 'name': property_name }, 'name': validation_name, 'type': 'select' }
            return property_value
        except:
            return {'select': { 'name': '' }, 'name': validation_name, 'type': 'select' }
    elif property_value == 'date':
        try:
            property_value = {'date': { 'start': property_name }, 'name': validation_name, 'type': 'date' }
            return property_value
        except:
            now = datetime.now()
            return {'date': { 'start': now.isoformat() + 'Z' }, 'name': validation_name, 'type': 'date' }
    else:
        return None

def get_property_value(page, property_name):
    if property_name == 'id':
        return page['id']
    else:
        try:
            propertyVal = page['properties'][property_name]
            if propertyVal['type'] == 'title':
                return propertyVal['title'][0]['text']['content']
            if propertyVal['type'] == 'checkbox':
                return (property_name, propertyVal['checkbox'])
            if propertyVal['type'] == 'select':
                return propertyVal['select']['name']
            if propertyVal['type'] == 'number':
                return propertyVal['number']
            if propertyVal['type'] == 'rich_text':
                return propertyVal['rich_text'][0]['text']['content']
            if propertyVal['type'] == 'relation':
                return propertyVal['relation']

            return propertyVal
        except:
            return None