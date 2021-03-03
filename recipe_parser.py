import requests
from bs4 import BeautifulSoup
import nltk
from textblob import TextBlob
from quantulum3 import parser
import re
import warnings
import spacy
from spacy.symbols import *
from spacy.matcher import Matcher 
from spacy.tokens import Span
from nltk.tokenize import word_tokenize
from PyDictionary import PyDictionary

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

    ingredients_dict,ingredients_lst = get_ingredients(ingredients)
    tools_list = get_tools(instructions, ingredients_dict, title)
    methods_list = get_methods(instructions)
    printer(title,ingredients_dict,instructions,tools_list,methods_list)
    # print("Veg Transformation\n")
    # veg_dic, veg_instructions = veg_replace(ingredients_dict,instructions)
    # printer(title,veg_dic,veg_instructions,tools_list,methods_list)

#takes list of ingredients with measurements. Return dictionary with ingredient and measurement
def get_ingredients(lst):
    all = {}
    ingredient_lst = []
    for ingredient in lst:
        quants = parser.parse(ingredient)
        measurement = ""
        if len(quants) == 0:
            all[ingredient] = ""
            ingredient_lst.append(ingredient)
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
            ingredient_lst.append(str(blob).lstrip())
        elif len(blob.noun_phrases) == 1:
            all[blob.noun_phrases[0].lstrip()] = measurement
            noun_list = str(blob.noun_phrases[0].lstrip()).split(" ")
            for noun in noun_list:
                ingredient_lst.append(noun)
        
    return all, ingredient_lst

#helper function for get_tools
def strip_preps(np):
    badTags = ["DT", "PRP$"]
    npStr = ""
    for word in np:
        if word.tag_ not in badTags:
            if word.text == "-":
                npStr = npStr[:-1] + "-"
            else:
                npStr += word.text + " "
    return npStr[:-1]

#takes instructions, ingredients dictionary, and title. Returns list of possible tools
def get_tools(lst, ingredients, title):
    ingr = set()
    noun_phrases = set()
    ingrsList = list(ingredients.keys())
    ingrsList = [x.replace(",", "").replace("-", " ") for x in ingrsList]
    goodWords = ["used for", "used to", "utensil", "tool"]
    
    [ingr.add(word.lower()) for sent in ingrsList for word in sent.split(" ")]
    [ingr.add(word.lower()) for word in title.split(" ")]
    
    for step in lst:
        doc = nlp(step)
        nps = []
        for np in doc.noun_chunks:
            words = np.text.replace(",", "").split(" ")
            flag = False
            for w in words:
                if w in ingr or re.search('\d', w) or re.search('[A-Z]+[a-z]+$', w):
                    flag = True
                    break
            if not flag:
                nps.append(np) 
        [noun_phrases.add(strip_preps(x)) for x in nps]
    
    noun_dict = {}
        
    for key in noun_phrases:
        noun_dict[key] = set(key.split(" "))
    
    for np in noun_dict.keys():
        np_set = set(np.split(" "))
        
        for np1 in noun_dict.keys():
            if np_set != noun_dict[np1]:
                common_set = np_set & noun_dict[np1]
                if common_set != set():
                    if np in noun_phrases: 
                        noun_phrases.remove(np)
                    if np1 in noun_phrases: 
                        noun_phrases.remove(np1) 
                    noun_phrases.add(' '.join([word for word in np.split(" ") if word in common_set]))
                
        for i in ingrsList:
            if np in i and i in noun_phrases:
                noun_phrases.remove(i)
                
    dictionary=PyDictionary()
    np_temp = set(noun_phrases)
    
    for np in np_temp:
        word = np.split(" ")[-1]
        meanings = dictionary.meaning(word)['Noun']
        flag = [True for m in meanings for gw in goodWords if gw in m]
        if flag == []:
            noun_phrases.remove(np)

    return [x for x in noun_phrases if len(x) > 1]

#takes instructions, returns list of verbs
def get_methods(steps):
    verbs = set()
    badWords = ["let", "serve", "bring", "place"]
    pattern=[{'TAG': 'VB'}]
    
    matcher = Matcher(nlp.vocab) 
    matcher.add("verb-phrases", None, pattern)
    
    for step in steps:
        doc = nlp(step)
        matches = matcher(doc)
        tempVerbs = [doc[start:end].text.lower() for _, start, end in matches] 
        [verbs.add(v) for v in tempVerbs if v not in badWords]
        
    return verbs

# read in the allrecipes.com url -> SAMPLE URL TO TEST: https://www.allrecipes.com/recipe/280509/stuffed-french-onion-chicken-meatballs/
def read_in_url():
    recipe_url = input('Please input a url from allrecipes.com: ')

    parse_url(recipe_url)

def printer(title,ingredients_dict,instructions_lst,tools,methods):
    print(title)
    print("Ingredients:")
    for k in ingredients_dict.keys():
        print("\t"+k+": "+ingredients_dict[k])
    print("Tools:")
    for t in tools:
        print("\t" + t)
    print("Methods:")
    for m in methods:
        print("\t" + m)
    print("Instructions:")
    for i,instruction in enumerate(instructions_lst):
        print("\tStep " + str(i+1)+": "+instruction)


#takes ingredients dictionary and replace meat and fish with veggies. Return new dictionary
def veg_replace(dic,instructions):
    meats= ['chicken','wings', 'beef', 'ground beef', 'duck', 'pork', 'ham','prosciutto', 'fish', 'sea bass', 'tilapia', 'salmon', 'halibut', 'trout','flounder',
    'turkey', 'meat stock', 'liver', 'crab', 'shrimp', 'liver', 'bacon', 'lamb','steak']
    meat_substitutes = {'chicken': 'eggplant', 'wings': 'eggplant', 'beef': 'tofu', 'ground beef': 'lentils',
                        'duck': 'tempeh', 'pork': 'seitan', 'ham': 'jackfruit',
                        'prosciutto': 'mushroom', 'fish': 'tofu', 'sea bass': 'cauliflower', 'tilapia': 'seitan',
                        'salmon': 'eggplant', 'halibut': 'tempeh', 'trout': 'tofu', 'flounder': 'jackfruit',
                        'turkey': 'seitan', 'meat stock': 'vegetable stock', 'liver': 'jackfruit',
                        'crab': 'cauliflower', 'shrimp': 'tofu', 'liver': 'tempeh', 'bacon': 'fried shallots',
                        'lamb': 'eggplant','steak':'tofu'}

    deleting_ing = []
    for ing in dic.keys():
        tokens = word_tokenize(ing)
        for token in tokens:
            if token in meats:
                deleting_ing.append(ing)

    for ing in deleting_ing:
        if ing in dic.keys():
            tokens = word_tokenize(ing)
            for token in tokens:
                if token in meat_substitutes.keys():
                    dic[meat_substitutes[token]] = dic[ing]
            del dic[ing]

    for i,instruction in enumerate(instructions):
        for ing in deleting_ing:
            tokens = word_tokenize(ing)
            for token in tokens:
                if token in instruction and token not in meat_substitutes.keys():
                    instructions[i] = instruction.replace(token, "")
                elif token in instruction:
                    instructions[i] = instruction.replace(token,meat_substitutes[token])

    return dic,instructions

if __name__ == '__main__':
    nlp = spacy.load('en_core_web_lg')
    read_in_url()