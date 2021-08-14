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

async def add_row(food):
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
            jsonRes = await resp.json()
            return jsonRes     

async def query_database(database_id, query={}):
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

async def query_database_name_list(food_names):
    query = {"filter": { "or": []  }}
    title_property = 'Food'
    for food_name in food_names:
        query["filter"]["or"].append({"property": title_property, "text": { "equals": food_name}})
    jsonRes = await query_database(os.getenv('NOTION_DATABASE_ID'), query)
    results = jsonRes['results']
    await build_food_from_page(results[1])
    return results

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

    print(food)
    return food

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

asyncio.run(query_database_name_list(["test food", "test food 2"]))