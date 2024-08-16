import requests
import logging
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from models import Pokemon, Item, Moves, Links, Stats

main_url = "https://pokeapi.co/api/v2/"

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_data(endpoint, name):
    response = requests.get(f'{main_url}/{endpoint}/{name}')
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to fetch {endpoint} data for {name}. Status code: {response.status_code}")
        return None

def insert_move(move_data, db: Session):
    formatted_name = move_data['name'].replace('-', ' ')
    move_db = db.exec(select(Moves).where(Moves.name == formatted_name)).first()
    if not move_db:
        move_db = Moves(
            name=formatted_name,
            move_type=move_data.get('type', {}).get('name'),
            category=move_data.get('damage_class', {}).get('name'),
            power=move_data.get('power'),
            accuracy=move_data.get('accuracy'),
            description=move_data['effect_entries'][0]['short_effect'] if move_data['effect_entries'] else ''
        )
        db.add(move_db)
        try:
            db.commit()
            db.refresh(move_db)
            logger.info(f"Inserted new move: {formatted_name}")
        except IntegrityError:
            db.rollback()
            logger.warning(f"Move {formatted_name} already exists, fetching existing record")
            move_db = db.exec(select(Moves).where(Moves.name == formatted_name)).first()
    return move_db

def insert_pokemon_data(pokemon_data, db: Session):
    moves = []
    for move in pokemon_data['moves']:
        move_data = fetch_data('move', move['move']['name'])
        if move_data:
            moves.append(insert_move(move_data, db))

    stats = Stats(
        hp=pokemon_data['stats'][0]['base_stat'],
        atk=pokemon_data['stats'][1]['base_stat'],
        def_=pokemon_data['stats'][2]['base_stat'],
        spa=pokemon_data['stats'][3]['base_stat'],
        spd=pokemon_data['stats'][4]['base_stat'],
        spe=pokemon_data['stats'][5]['base_stat'],
        total=sum(stat['base_stat'] for stat in pokemon_data['stats'])
    )
    db.add(stats)
    try:
        db.commit()
        db.refresh(stats)
        logger.info(f"Inserted stats for Pokemon {pokemon_data['name']}")
    except IntegrityError:
        db.rollback()
        logger.error(f"Failed to insert stats for Pokemon {pokemon_data['name']}")
        return None

    pokemon = Pokemon(
        natdex_id=pokemon_data['id'],
        name=pokemon_data['name'].replace('-', ' '),
        pokemon_type="/".join([t['type']['name'] for t in pokemon_data['types']]),
        abilities="/".join([a['ability']['name'].replace('-', ' ') for a in pokemon_data['abilities']]),
        base_stats_id=stats.id
    )
    db.add(pokemon)
    try:
        db.commit()
        db.refresh(pokemon)
        logger.info(f"Inserted Pokemon: {pokemon.name}")
    except IntegrityError:
        db.rollback()
        logger.error(f"Failed to insert Pokemon {pokemon.name}, it may already exist")
        return None
    
    for move in moves:
        link = Links(pokemon_name=pokemon.name, move_name=move.name)
        db.add(link)
    try:
        db.commit()
        logger.info(f"Inserted move links for Pokemon: {pokemon.name}")
    except IntegrityError:
        db.rollback()
        logger.error(f"Failed to insert move links for Pokemon {pokemon.name}")
    
    return pokemon

def insert_item(item_data, db: Session):
    item = Item(
        id=item_data['id'],
        name=item_data['name'].replace('-', ' '),
        description=item_data['effect_entries'][0]['short_effect'] if item_data['effect_entries'] else ''
    )
    db.add(item)
    try:
        db.commit()
        db.refresh(item)
        logger.info(f"Inserted Item: {item.name}")
        return item
    except IntegrityError:
        db.rollback()
        logger.error(f"Failed to insert Item {item.name}, it may already exist")
        return None



    
    