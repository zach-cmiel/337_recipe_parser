
import requests
from bs4 import BeautifulSoup


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
    ingredient_spans = soup.find_all('span', class_='ingredients-item-name')

    ingredients = []
    for span in ingredient_spans:
        ingredient = span.get_text().lstrip().rstrip()
        ingredients.append(ingredient)

    print(ingredients)

# read in the allrecipes.com url -> SAMPLE URL TO TEST: https://www.allrecipes.com/recipe/280509/stuffed-french-onion-chicken-meatballs/
def read_in_url():
    recipe_url = input('Please input a url from allrecipes.com: ')

    parse_url(recipe_url)

read_in_url()
