import myfitnesspal
from chronological import fetch_max_search_doc, main, cleaned_completion, read_prompt
from datetime import datetime
import pytz
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncio
from notion import get_property_value, set_property_value, query_database, create_page

from flask import Flask, request, redirect, url_for, render_template
from functools import wraps
import json

def async_action(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapped

app = Flask(__name__)

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

client = myfitnesspal.Client(os.getenv("MFP_EMAIL"))

async def create_food(food):
    return await create_page(build_page_properties_from_food(food), os.getenv('NOTION_DATABASE_ID'))

def find_best_match_food_in_mfp(food_name):
    food_items = client.get_food_search_results(food_name)
    if len(food_items) == 0:
        return None
    else:

        best_match_id = food_items[0].mfp_id
        if best_match_id is None:
            return None
        else:
            food_details = client.get_food_item_details(best_match_id)
            food = {}
            food["name"] = food_details.name
            food["brand"] = food_details._brand
            food["serving"] = food_details.serving
            
            try:
                food["calories"] = food_details.calories
            except KeyError as e:
                food["calories"] = -1.0

            try:
                food["fat"] = food_details.fat
            except KeyError as e:
                food["fat"] = -1.0

            try:
                food["carbohydrates"] = food_details.carbohydrates
            except KeyError as e:
                food["carbohydrates"] = -1.0

            try:
                food["protein"] = food_details.protein
            except KeyError as e:
                food["protein"] = -1.0

            try:
                food["sugar"] = food_details.sugar
            except KeyError as e:
                food["sugar"] = -1.0

            try:
                food["fiber"] = food_details.fiber
            except KeyError as e:
                food["fiber"] = -1.0

            try:
                food["sodium"] = food_details.sodium
            except KeyError as e:
                food["sodium"] = -1.0
            
            try:
                food["saturated_fat"] = food_details.saturated_fat
            except KeyError as e:
                food["saturated_fat"] = -1.0

            try:
                food["cholesterol"] = food_details.cholesterol
            except KeyError as e:
                food["cholesterol"] = -1.0

            return food

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

async def find_food_duplicates_in_notion(food_name):
    query = { "filter": { "or": [{ "property": "Food", "text": { "contains": food_name } }]  }}
    query_res = await query_database(os.getenv('NOTION_DATABASE_ID'), query)
    results = query_res['results']


    if len(results) > 0:
        top_result_food_name = ''
        if len(results) > 1:
            print('Found multiple results for ' + food_name)
            top_result = None
            for result in results:
                for food_name in result['properties']['Food']['title']:
                    result_food_name = food_name['text']['content']
                    if result_food_name == 'Copy of ':
                        continue
                    else:
                        top_result = result
                        top_result_food_name = result_food_name
                        break
        else:
            top_result = results[0]
            top_result_food_name = top_result['properties']['Food']['title'][0]['text']['content']
        
        top_result['properties'] = { "Food" : 'Copy of ' + top_result_food_name }
        print(json.dumps(top_result, indent=4))
        return top_result # only interested in the closest match

    return results

def infer_meal_from_time():
    now = datetime.now(pytz.timezone(os.getenv('TIMEZONE')))
    if now.hour >= int(os.getenv('BREAKFAST_START')) and now.hour < int(os.getenv('BREAKFAST_END')):
        return 'breakfast'
    elif now.hour >= int(os.getenv('LUNCH_START')) and now.hour < int(os.getenv('LUNCH_END')):
        return 'lunch'
    elif now.hour >= int(os.getenv('DINNER_START')) and now.hour < int(os.getenv('DINNER_END')):
        return 'dinner'
    else:
        return 'snack'

def build_page_properties_from_food(food = dict()):
    properties = dict()
    properties['Food'] = set_property_value(food.get('name', ''), 'title', 'Food')
    properties['Brand'] = set_property_value(food.get('brand', ''), 'rich_text', 'Brand')
    properties['Meal'] = set_property_value(food.get('meal', infer_meal_from_time()), 'select', 'Meal')
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
    now = datetime.now()
    properties['Date'] = set_property_value(now.isoformat() + 'Z', 'date', 'Date')
    properties['Raw_Voice_Dictation'] = set_property_value(food.get('Raw_Voice_Dictation', ''), 'rich_text', 'Raw_Voice_Dictation')
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

async def split_into_ingredients(text):
    ingredients_text = await cleaned_completion(read_prompt('mfpal').format(text),
        temperature=0.0,
        max_tokens=100,
        frequency_penalty=1.0,
        engine='davinci-instruct-beta',
        stop=['\n\n'],
        top_p=1.0
    )
    ingredients = list(map(lambda ingredient: ingredient.replace('-', ''), ingredients_text.split('\n'))) 
   
    return ingredients

async def lookup_food_from_dictation(dictated_text):
    ingredients = await split_into_ingredients(dictated_text)
    for ingredient in ingredients:
        print('Ingredient is %s', ingredient)
        res = find_best_match_food_in_mfp(ingredient)
        res['Raw_Voice_Dictation'] = dictated_text
        notionres = await create_food(res)
        print(notionres)


# use the notion api to aggregate rows into a single row with combined nutrition data
# an array of rows of ids
async def create_aggregate_food(rows):
    pass

@app.route('/<password>/<dictation>', methods=['GET', 'POST'])
@async_action
async def admin(password, dictation):
    if password != os.getenv("DICTATION_PASSWORD"):
        return redirect(url_for('index'))
    else:
        await lookup_food_from_dictation(dictation)
        return 'success'

@app.route('/', methods=['GET', 'POST'])
def index():
    return "bram's food journal"

if __name__ == '__main__':
    app.debug = True
    app.run(port=8080)