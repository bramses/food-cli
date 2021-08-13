import myfitnesspal
from chronological import fetch_max_search_doc, main, cleaned_completion, read_prompt
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncio

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

def lookup_food_from_dictation(dictated_text):
    pass



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

            print(food)

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
    ingredients = ingredients_text.split('\n')
    for ingredient in ingredients:
        ingredient = ingredient.replace('-', '')
        find_best_match_food_in_mfp(ingredient)

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
    return dictation

@app.route('/', methods=['GET', 'POST'])
def index():
    return "bram's food journal"

# asyncio.run(split_into_ingredients("I had an egg sandwich with cheese, oatmeal with raisins, and cucumber water"))

# find_best_match_food_in_mfp("talenti rasberry sorbet")

# if __name__ == '__main__':
#     app.debug = True
#     app.run(port=8080)


'''
food cli goals
- have a easy to use food journal from mobile or web
- use mfp to get details of macros i care to track [x]
- local private notion api of calorie intake, dairy, sugar, how i feel, etc
- favorite food list + easy, healthy recipes

voice input (apple dictation) → 
split into ingredients and metadata (gpt3) → 
notion search ->
mfp search → 
time lookup (input date) (api call) → 
add data to notion (notion api) → 
EoD calculate how it went (cron job + notion api)

what are my diet goals?
- knowing whats going into my body (intention)
- balancing energy throughout the day (while acknowledging seasonal shifts)
- healthy easy and cheap options
- eat out as a reward, not as a default
- get all of nutrients covered
- cut down on obvious long term problematic foods (sugar, salt) and overeating
- anime strength and figure
- genetleman strength and figure
- run my business in peak health


run my business in peak health (overeating, meal planning, exercise)
genetleman/anime strength and figure (exercise, sleep)
balancing energy throughout the day (while acknowledging seasonal shifts) (caffeine, sleep)
cut down on obvious long term problematic foods (sugar, salt, breads) and overeating (meal prep)

meal journal -> meal prep
lower carb intake

'''

'''
Ingredients Example:
-1 Bowl of TONKATSU RAMEN
-1 KALE SALAD
-1 Slice of BREAD
-1 Bottle of PICKLE DRESSING
'''