"""
This is a python script to create a template to convert a dreamborn.ink Tabletop Simulator export into a Draftmancer Custom Card List.

Run the script like so:
python3 create_template.py '/path/to/dreamborn_tabletop_sim_export.json'

TODOs:
- How to balance packs versus random 12 cards?

Notes:
- https://draftmancer.com/cubeformat.html
"""
import requests
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import csv

CACHED_API_DATA_FILEPATH = 'api_data_cache.json'

parser = argparse.ArgumentParser(
                    prog='ProgramName',
                    description='given a dreamborn \"deck\" of a cube / set / card list, exported in Tabletop Simulator format, create a draftmancer custom card list that can be uploaded and drafted on draftmancer.com',
                    epilog='Text at the bottom of help')

parser.add_argument('dreamborn_export_for_tabletop_sim', help="file path to a .deck export in Tabletop Sim format from dreamborn.ink deck of the cube e.g. example-cube.json or C:\\Users\\dru\\Desktop\\deck.json")
parser.add_argument('--card_evaluations_file', default="DraftBots\\FrankKarstenEvaluations-HighPower.csv", help="relative path to a .csv file containing card name -> 0-5 card rating (power in a vacuum). default: \"DraftBots\\\\FrankKarstenEvaluations-HighPower.csv\"")
parser.add_argument('--boosters_per_player', default=4)
parser.add_argument('--cards_per_booster', default=12)
parser.add_argument('--name', default="custom_card_list", help="Sets name of both the output file and the set/cube list as it appears in draftmancer")
parser.add_argument('--set_card_colors', default=False, help="WARNING** This sets card colors, allowing draftmancer to do color-balancing for you, but it will also encourage bots to draft 1-2 color decks")
parser.add_argument('--color_balance_packs', default=False, help="WARNING** this color-balances ONLY your largest slot, IF it contains enough cards, AND steel may be wonky (treated as colorless). This will ONLY work if card_colors is true, which will encourage bots to draft 1-2 color decks")

def fetch_api_data():
    name_to_card = {}
    page = 1
    while True:
        url = f'https://api.lorcana-api.com/cards/all?page={page}'
        print(f'Fetching {url}...')
        res = requests.get(url)
        data = res.json()
        if len(data) == 0:
            break
        for card in data:
            name_to_card[card['Name']] = card
        page += 1
    return name_to_card

def generate_id_to_card(name_to_card):
    return {to_id(card_name) : name_to_card[card_name] for card_name in name_to_card}

def read_or_fetch_id_to_api_card():
    cached_api_data_file = Path(CACHED_API_DATA_FILEPATH)
    if cached_api_data_file.is_file():
        with cached_api_data_file.open() as f:
            id_to_card = json.load(f)
    else:
        name_to_card = fetch_api_data()
        fix_card_names(name_to_card)
        id_to_card = generate_id_to_card(name_to_card)
        with cached_api_data_file.open(mode='w') as f:
            json.dump(id_to_card, f)
    return id_to_card

def generate_id_to_tts_card_file(file, id_to_tts_card=None):
    with file.open(encoding='utf8') as file:
        data = json.load(file)
    data = data['ObjectStates'][0]
    if id_to_tts_card == None:
        id_to_tts_card = defaultdict(lambda: {'count': 0})
    i = 1
    while True:
        try:
            id = to_id(data['ContainedObjects'][i - 1]['Nickname'])
        except IndexError:
            break
        id_to_tts_card[id]['count'] += 1
        id_to_tts_card[id]['name'] = data['ContainedObjects'][i - 1]['Nickname']
        id_to_tts_card[id]['image_uri'] = data['CustomDeck'][str(i)]['FaceURL']
        i += 1
    return id_to_tts_card

def generate_id_to_tts_card(dreamborn_tts_export_filepath):
    dreamborn_tts_export_path = Path(dreamborn_tts_export_filepath)
    id_to_tts_card = None
    if dreamborn_tts_export_path.is_dir():
        files = dreamborn_tts_export_path.glob('*')
        for file in files:
            if file.is_file():
                print(file)
                id_to_tts_card = generate_id_to_tts_card_file(file, id_to_tts_card)
    else:
        id_to_tts_card = generate_id_to_tts_card_file(dreamborn_tts_export_path, id_to_tts_card)
    return id_to_tts_card

pattern = re.compile(r"[\W_]+", re.ASCII)
def to_id(string):
    string = string.replace('ā', 'a')
    string = string.replace('é','e')
    return re.sub(pattern, '', string).lower()

def fix_card_name(name_to_card, old_name, new_name):
    name_to_card[new_name] = name_to_card[old_name]
    name_to_card[new_name]['Name'] = new_name
    del name_to_card[old_name]    

def fix_card_names(name_to_card):
    # set correct keys using API's typos
    fix_card_name(name_to_card, 'Benja - Bold United', 'Benja - Bold Uniter')
    fix_card_name(name_to_card, 'Kristoff - Offical Ice Master', 'Kristoff - Official Ice Master')
    fix_card_name(name_to_card, 'Snowanna Rainbeau', 'Snowanna Rainbeau - Cool Competitor')
    fix_card_name(name_to_card, 'Vannelope Von Schweetz - Random Roster Racer', 'Vanellope von Schweetz - Random Roster Racer')
    fix_card_name(name_to_card, 'Snow White - Fair-haired', 'Snow White - Fair-Hearted')
    fix_card_name(name_to_card, 'Merlin\'s Cottage', 'Merlin\'s Cottage - The Wizard\'s Home')
    fix_card_name(name_to_card, 'Arthur - King Victorius', 'Arthur - King Victorious')
    fix_card_name(name_to_card, 'Seven Dwarfs\' Mine', 'Seven Dwarfs\' Mine - Secure Fortress')

def read_all_card_names_from_dreamborn_plain_export():
    with open('all_cards.txt', encoding='utf8') as f:
        lines = f.readlines()
    id_to_name = {}
    for l in lines:
        name = l.split('1 ')[1].strip()
        id_to_name[to_id(name)] = name
    return id_to_name

lorcana_color_to_draftmancer_color =  {
    "Amber": "W",
    "Amethyst": "B",
    "Emerald": "G",
    "Ruby": "R",
    "Steel": "",
    "Sapphire": "U"
}
def to_draftmancer_color(lorcana_color):
    if set_card_colors:
        return lorcana_color_to_draftmancer_color[lorcana_color]
    else:
        return ""

lorcana_rarity_to_draftmancer_rarity =  {
    "Common": "common",
    "Uncommon": "uncommon",
    "Rare": "rare",
    "Super Rare": "mythic",
    "Legendary": "mythic"
}
def to_draftmancer_rarity(lorcana_rarity):
    return lorcana_rarity_to_draftmancer_rarity[lorcana_rarity]

def generate_custom_card_list(id_to_card, name_to_rating, id_to_tts_card):
    custom_card_list = []
    for id in id_to_tts_card:
        card = id_to_card[id]
        ink_cost = card['Cost']
        custom_card = {
            'name': id_to_tts_card[id]['name'], # IMPORTANT dreamborn names stored in TTS cards are canonical so you can import / export to / from dreamborn
            'mana_cost': f'{{{ink_cost}}}',
            'type': 'Instant',
            'image_uris': {
                'en': id_to_tts_card[id]['image_uri']
            },
            'rating': name_to_rating[id],
            'rarity': to_draftmancer_rarity(card['Rarity']),
        }
        if (set_card_colors):
            custom_card['colors'] = [to_draftmancer_color(card['Color'])]
        custom_card_list.append(custom_card)
    return custom_card_list

def retrieve_id_to_rating():
    id_to_rating = {}
    with open(file=card_evaluations_file, newline='', encoding='utf8') as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.read(1024))
        dialect.quoting = csv.QUOTE_MINIMAL
        csvfile.seek(0)
        reader = csv.DictReader(csvfile, dialect=dialect)
        for row in reader:
            id_to_rating[to_id(row['Card Name'])] = int(row['Rating - Draftmancer'])
    return id_to_rating

def write_out(out, id_to_tts_card):
    file_name = f'{card_list_name}.draftmancer.txt'
    with open(file_name, 'w', encoding="utf-8") as f:
        settings = {
                    'boostersPerPlayer': boosters_per_player,
                    'name': card_list_name
        }
        if color_balance_packs == True:
            settings['colorBalance'] = True
        lines = [
            '[CustomCards]',
            json.dumps(out, indent=4),
            '[Settings]',
            json.dumps(
                settings,
                indent=4
            ),
            f'[MainSlot({cards_per_booster})]',
        ]
        for id in id_to_tts_card:
            line_str = f"{id_to_tts_card[id]['count']} {id_to_tts_card[id]['name']}"
            lines.append(line_str)
        for line in lines:
            f.write(line + '\n')

card_evaluations_file = None
boosters_per_player = None
cards_per_booster = None
card_list_name = None
set_card_colors = False
color_balance_packs = False

if __name__ == '__main__':
    # parse CLI arguments
    args = parser.parse_args()
    id_to_tts_card = generate_id_to_tts_card(args.dreamborn_export_for_tabletop_sim)
    card_evaluations_file = args.card_evaluations_file
    boosters_per_player = int(args.boosters_per_player)
    card_list_name = args.name
    cards_per_booster = int(args.cards_per_booster)
    set_card_colors = bool(args.set_card_colors)
    color_balance_packs = bool(args.color_balance_packs)
    # process
    id_to_api_card = read_or_fetch_id_to_api_card()
    id_to_rating = retrieve_id_to_rating()
    custom_card_list = generate_custom_card_list(id_to_api_card, id_to_rating, id_to_tts_card)
    write_out(custom_card_list, id_to_tts_card)
