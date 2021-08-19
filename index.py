import myfitnesspal
from chronological import fetch_max_search_doc, main, cleaned_completion, read_prompt
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncio
from notion import create_food

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
        print(ingredient)
        res = find_best_match_food_in_mfp(ingredient)
        notionres = await create_food(res)
        print(notionres)

# asyncio.run(lookup_food_from_dictation('i had a chicken wing and 2 slices of sourdough bread'))

# use the notion api to aggregate rows into a single row with combined nutrition data
# an array of rows of ids
# {'name': 'Sorbet', 'brand': 'Talenti', 'serving': 'cup', 'calories': 120.0, 'fat': 0.0, 'carbohydrates': 29.0, 'protein': 0.0, 'sugar': 25.0, 'fiber': 3.0, 'sodium': -1.0, 'saturated_fat': -1.0, 'cholesterol': -1.0}
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

# asyncio.run(split_into_ingredients("I had an egg sandwich with cheese, oatmeal with raisins, and cucumber water"))

# find_best_match_food_in_mfp("talenti rasberry sorbet")

if __name__ == '__main__':
    app.debug = True
    app.run(port=8080)