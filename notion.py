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

async def create_food(food):
    return await create_page(build_page_properties_from_food(food), os.getenv('NOTION_DATABASE_ID'))

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

    data = {
        'parent': { "database_id" : database_id },
        'properties': properties
    }

    print(json.dumps(data, indent=4))

    async with aiohttp.ClientSession(trace_configs=[trace_config]) as session:
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

async def query_database_for_food_names(food_names):
    query = {"filter": { "or": []  }}
    title_property = 'Food'
    for food_name in food_names:
        query["filter"]["or"].append({"property": title_property, "text": { "equals": food_name}})
    jsonRes = await query_database(os.getenv('NOTION_DATABASE_ID'), query)
    results = jsonRes['results']
    print(json.dumps(results, indent=4))
    food = await build_food_from_page(results[0])
    print(json.dumps(food, indent=4))
    return results

def build_page_properties_from_food(food = dict()):
    properties = dict()
    properties['Food'] = set_property_value(food.get('name', ''), 'title', 'Food')
    properties['Brand'] = set_property_value(food.get('brand', ''), 'rich_text', 'Brand')
    # properties['Meal'] = set_property_value(food.get('meal', ''), 'select', 'Meal')
    properties['Calories'] = set_property_value(food.get('calories', -1), 'number', 'Calories')
    properties['Fat'] = set_property_value(food.get('fat', -1), 'number', 'Fat')
    properties['Saturated_Fat'] = set_property_value(food.get('saturated_fat', -1), 'number', 'Saturated Fat')
    properties['Carbohydrates'] = set_property_value(food.get('carbohydrates', -1), 'number', 'Carbohydrates')
    properties['Sugar'] = set_property_value(food.get('sugar', -1), 'number', 'Sugar')
    properties['Protein'] = set_property_value(food.get('protein', -1), 'number', 'Protein')
    properties['Sodium'] = set_property_value(food.get('sodium', -1), 'number', 'Sodium')
    properties['Fiber'] = set_property_value(food.get('fiber', -1), 'number', 'Fiber')
    properties['Has_Processed_Sugar'] = set_property_value(food.get('has_processed_sugar', False), 'checkbox', 'Has_Processed_Sugar')
    properties['Has_Dairy'] = set_property_value(food.get('has_dairy', False), 'checkbox', 'Has_Dairy')
    properties['Favorite'] = set_property_value(food.get('favorite', False), 'checkbox', 'Favorite')
    return properties

'''
This code is building a dictionary of food details from the given page.
- generated by stenography 🤖
'''
async def build_food_from_page(page):
    food = {}
    food['id'] = get_property_value(page, 'id')
    food['name'] = get_property_value(page, 'Food')
    food['calories'] = get_property_value(page, 'Calories')
    food['fat'] = get_property_value(page, 'Fat')
    food['saturated_fat'] = get_property_value(page, 'Saturated_Fat')
    food['carbohydrates'] = get_property_value(page, 'Carbohydrates')
    food['sugar'] = get_property_value(page, 'Sugar')
    food['protein'] = get_property_value(page, 'Protein')
    food['sodium'] = get_property_value(page, 'Sodium')
    food['fiber'] = get_property_value(page, 'Fiber')
    food['meal'] = get_property_value(page, 'Meal')
    food['has_dairy'] = get_property_value(page, 'Has_Dairy')
    food['has_processed_sugar'] = get_property_value(page, 'Has_Processed_Sugar')
    food['favorite'] = get_property_value(page, 'Favorite')
    food['brand'] = get_property_value(page, 'Brand')
    food['components'] = get_property_value(page, 'Components')
    food['raw_voice_dictation'] = get_property_value(page, 'Raw_Voice_Dictation')


    return food

def generate_random_short_string():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))

def set_property_value(property_name, property_value, validation_name=None):
    if property_value == 'title':
        try:
           property_value = {'title' : [{'text': {'content': property_name}}], 'name': validation_name, 'type': 'title', 'id': generate_random_short_string() }
           return property_value
        except:
            return {'title' : [{'text': {'content': ''}}], 'name': validation_name, 'type': 'title' }
    elif property_value == 'rich_text':
        # return None
        try:
            property_value = {'rich_text': [{'text': {'content': property_name}}], 'name': validation_name, 'type': 'text' }
            return property_value
        except:
            return {'rich_text': [{'text': {'content': ''}}], 'name': validation_name, 'type': 'text' }
    elif property_value == 'number':
        # return None
        try:
            property_value = {'number': property_name, 'name': validation_name, 'type': 'number' }
            return property_value
        except:
            return {'number': -1, 'name': validation_name, 'type': 'number' }
    elif property_value == 'checkbox':
        # return None
        try:
            property_value = {'checkbox': property_name, 'name': validation_name, 'type': 'checkbox' }
            return property_value
        except:
            return {'checkbox': False, 'name': validation_name, 'type': 'checkbox' }
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

asyncio.run(create_food({'name': 'Sorbet', 'brand': 'Talenti', 'serving': 'cup', 'calories': 120.0, 'fat': 0.0, 'carbohydrates': 29.0, 'protein': 0.0, 'sugar': 25.0, 'fiber': 3.0, 'sodium': -1.0, 'saturated_fat': -1.0, 'cholesterol': -1.0}))
# asyncio.run(query_database_for_food_names(['test food']))