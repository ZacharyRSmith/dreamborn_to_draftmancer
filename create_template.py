"""
This is a python script to create a template to convert a dreamborn.ink plain export into a Draftmancer Custom Card List.

Run the script like so:
python3 create_template.py '/path/to/dreamborn_tabletop_sim_export.json'

TODOs:
- How to balance packs versus random 12 cards?
- change name of out.txt
- make code easier for others to read/change

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

API_DATA_FILEPATH = 'api_data.json'
OUT_FILEPATH = 'draftmancer_custom_card_list_template.txt'

parser = argparse.ArgumentParser(
                    prog='ProgramName',
                    description='What the program does',
                    epilog='Text at the bottom of help')

parser.add_argument('dreamborn_export_for_tabletop_sim')
parser.add_argument('--card_evaluations_file')


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


def generate_name_id_to_card(name_to_card):
    return {to_id(card_name) : name_to_card[card_name] for card_name in name_to_card}

def read_or_fetch_name_id_to_api_card():
    api_data_file = Path(API_DATA_FILEPATH)
    if api_data_file.is_file():
        with api_data_file.open() as f:
            name_id_to_card = json.load(f)
    else:
        name_to_card = fetch_api_data()
        fix_card_names(name_to_card)
        name_id_to_card = generate_name_id_to_card(name_to_card)
        with api_data_file.open(mode='w') as f:
            json.dump(name_id_to_card, f)
    return name_id_to_card


def read_id_to_vals(dreamborn_export_for_tabletop_sim__filepath):
    dreamborn_export_for_tabletop_sim__file = Path(dreamborn_export_for_tabletop_sim__filepath)
    with dreamborn_export_for_tabletop_sim__file.open(encoding='utf8') as f:
        data = json.load(f)
    data = data['ObjectStates'][0]

    id_to_vals = defaultdict(lambda: {'count': 0})

    i = 1
    while True:
        try:
            id = to_id(data['ContainedObjects'][i - 1]['Nickname'])
        except IndexError:
            break
        id_to_vals[id]['count'] += 1
        id_to_vals[id]['name'] = data['ContainedObjects'][i - 1]['Nickname']
        id_to_vals[id]['image_uri'] = data['CustomDeck'][str(i)]['FaceURL']

        i += 1

    return id_to_vals


pattern = re.compile(r"[\W_]+", re.ASCII)
def to_id(string):
    string = string.replace('ā', 'a')
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


def generate_custom_card_list(name_to_card, name_to_rating, id_to_vals):
    custom_card_list = []
    # id_to_name_from_plain_export = read_all_ca_names_from_dreamborn_plain_export()
    for name_id in id_to_vals:
        ink_cost = name_to_card[name_id]['Cost']
        set_num = name_to_card[name_id]['Set_Num']
        card_num = name_to_card[name_id]['Card_Num']
        foo = {
            'name': id_to_vals[name_id]['name'],
            'mana_cost': f'{{{ink_cost}}}',
            'type': 'Instant',
            'image_uris': {
                'en': f"https://images.dreamborn.ink/cards/en/tts/00{set_num}-{'{:03}'.format(card_num)}_716x1000.jpeg",
            },
        }
        # foo['rarity'] = lorcana_rarity_to_magic_rarity(name_to_card['Rarity'])
        foo['rating'] = name_to_rating[name_id]
        custom_card_list.append(foo)
    return custom_card_list

def retrieve_name_id_to_rating():
    name_id_to_rating = {}
    with open(file=card_evaluations_file, newline='', encoding='utf8') as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.read(1024))
        dialect.quoting = csv.QUOTE_MINIMAL
        csvfile.seek(0)
        reader = csv.DictReader(csvfile, dialect=dialect)
        for row in reader:
            name_id_to_rating[to_id(row['Card Name'])] = int(row['Rating - Draftmancer'])
    return name_id_to_rating

def write_out(out, id_to_vals):
    with open(OUT_FILEPATH, 'w', encoding="utf-8") as f:
        lines = [
            '[CustomCards]',
            json.dumps(out, indent=4),
            '[Settings]',
            json.dumps(
                {
                    'boostersPerPlayer': 4,
                },
                indent=4
            ),
            f'[MainSlot(12)]',
        ]
        for id in id_to_vals:
            line_str = f"{id_to_vals[id]['count']} {id_to_vals[id]['name']}"
            lines.append(line_str)

        for line in lines:
            f.write(line + '\n')


card_evaluations_file = "DraftBots\\FrankKarstenPoweredCubeEvaluations.csv"

if __name__ == '__main__':
    args = parser.parse_args()
    id_to_vals = read_id_to_vals(args.dreamborn_export_for_tabletop_sim)
    if args.card_evaluations_file:
        card_evaluations_file = args.card_evaluations_file
    # print(id_to_vals)
    name_id_to_api_card = read_or_fetch_name_id_to_api_card()
    name_id_to_rating = retrieve_name_id_to_rating()
    custom_card_list = generate_custom_card_list(name_id_to_api_card, name_id_to_rating, id_to_vals)
    write_out(custom_card_list, id_to_vals)
    # print()
