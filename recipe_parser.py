import requests
from bs4 import BeautifulSoup
import nltk
from textblob import TextBlob
from quantulum3 import parser
import warnings
nltk.download("wordnet")
nltk.download("brown")
warnings.simplefilter('ignore')


headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '3600',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
    }


# use BeautifulSoup and requests to inspect url HTML
def parse_url(url):
    req = requests.get(url, headers)
    soup = BeautifulSoup(req.content, 'html.parser')

    title = soup.find("h1" , class_="headline heading-content").get_text().lstrip().rstrip()

    ingredient_spans = soup.find_all('span' , class_='ingredients-item-name')
    ingredients = []
    for span in ingredient_spans:
        ingredient = span.get_text().lstrip().rstrip()
        ingredients.append(ingredient)

    instructions_ul = soup.find_all("li" , class_="subcontainer instructions-section-item")
    instructions = []
    for step in instructions_ul:
        instructions.append(step.find("div" , class_="paragraph").get_text().lstrip().rstrip())

    ingredients_dict = get_ingredients(ingredients)
    printer(title,ingredients_dict,instructions)


#takes list of ingredients with measurements. Return dictionary with ingredient and measurement
def get_ingredients(lst):
    all = {}
    for ingredient in lst:
        quants = parser.parse(ingredient)
        measurement = ""
        if len(quants) == 0:
            all[ingredient] = ""
            continue
        if len(quants) == 2 and str(quants[0].unit) == "" and quants[1].value < 1:
            measurement = measurement + str(quants[0].value + quants[1].value)
            measurement = measurement + " " + str(quants[1].unit)
        elif len(quants) == 2 and str(quants[0].unit) == "" and quants[1].value > 1:
            measurement = str(quants[1].value * quants[0].value) + " " + str(quants[1].unit)
        else:
            measurement = str(quants[0].value) + " "+ str(quants[0].unit)

        #delete measurements
        for quant in quants:
            ingredient = ingredient.replace(quant.surface,"")

        blob = TextBlob(ingredient)

        if len(blob.noun_phrases) == 0:
            all[str(blob).lstrip()] = measurement
        elif len(blob.noun_phrases) == 1:
            all[blob.noun_phrases[0].lstrip()] = measurement
        
    return all


# read in the allrecipes.com url -> SAMPLE URL TO TEST: https://www.allrecipes.com/recipe/280509/stuffed-french-onion-chicken-meatballs/
def read_in_url():
    recipe_url = input('Please input a url from allrecipes.com: ')

    parse_url(recipe_url)

def printer(title,ingredients_dict,instructions_lst):
    print(title)
    print("Ingredients:")
    for k in ingredients_dict.keys():
        print("\t"+k+": "+ingredients_dict[k])
    print("Instructions:")
    for i,instruction in enumerate(instructions_lst):
        print("\tStep " + str(i+1)+": "+instruction)

if __name__ == '__main__':
    read_in_url()

