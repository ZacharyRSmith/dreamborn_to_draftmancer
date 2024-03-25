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

API_DATA_FILEPATH = 'api_data.json'
OUT_FILEPATH = 'draftmancer_custom_card_list_template.txt'

parser = argparse.ArgumentParser(
                    prog='ProgramName',
                    description='What the program does',
                    epilog='Text at the bottom of help')

parser.add_argument('dreamborn_export_for_tabletop_sim')


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


def read_name_to_card():
    api_data_file = Path(API_DATA_FILEPATH)
    if api_data_file.is_file():
        with api_data_file.open() as f:
            name_to_card = json.load(f)
    else:
        name_to_card = fetch_api_data()
        with api_data_file.open(mode='w') as f:
            json.dump(name_to_card, f)
    return name_to_card


def read_id_to_vals(dreamborn_export_for_tabletop_sim__filepath):
    dreamborn_export_for_tabletop_sim__file = Path(dreamborn_export_for_tabletop_sim__filepath)
    with dreamborn_export_for_tabletop_sim__file.open() as f:
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


pattern = re.compile('[\W_]+', re.ASCII)
def to_id(string):
    string = string.replace('ā', 'a')
    return re.sub(pattern, '', string).lower()


def transform_name_to_card(name_to_card):
    # set correct keys using API's typos
    name_to_card['Rabbit - Reluctant Host'] = name_to_card['Rabbit - Reluctent Host']
    name_to_card['Pinocchio - Talkative Puppet'] = name_to_card['Pinocchio - Talkative Pupper']
    name_to_card['Perplexing Signposts'] = name_to_card['Preplexing Signposts']
    name_to_card['Kristoff - Official Ice Master'] = name_to_card['Kristoff - Offical Ice Master']

    # set ids using names
    for name, card in list(name_to_card.items()):
        id = to_id(name)
        name_to_card[id] = card


def read_all_card_names_from_dreamborn_plain_export():
    with open('all_cards.txt') as f:
        lines = f.readlines()
    id_to_name = {}
    for l in lines:
        name = l.split('1 ')[1].strip()
        id_to_name[to_id(name)] = name
    return id_to_name


def get_out(id_to_vals, name_to_card):
    out = []
    id_to_name_from_plain_export = read_all_card_names_from_dreamborn_plain_export()
    for id, vals in id_to_vals.items():
        if id in name_to_card:
            ink_cost = name_to_card[id]['Cost']
        else:
            print(f'Ink cost not found for: {vals["name"]}')
            ink_cost = 0

        if to_id(vals['name']) in id_to_name_from_plain_export:
            name = id_to_name_from_plain_export[to_id(vals['name'])]
        else:
            print(f"Name {vals['name']} from dreamborn TableTop Simulator export not found in names from dreamborn plain export!")
            name = vals['name']

        out.append({
            'name': name,
            'mana_cost': f'{{{ink_cost}}}',
            'type': 'Instant',
            'image_uris': {
                'en': vals['image_uri'],
            },
        })
    return out


def write_out(out):
    with open(OUT_FILEPATH, 'w') as f:
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
        for line in lines:
            f.write(line + '\n')


if __name__ == '__main__':
    args = parser.parse_args()

    id_to_vals = read_id_to_vals(args.dreamborn_export_for_tabletop_sim)
    name_to_card = read_name_to_card()
    transform_name_to_card(name_to_card)
    out = get_out(id_to_vals, name_to_card)
    write_out(out)
