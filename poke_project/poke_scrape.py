import requests
from bs4 import BeautifulSoup
import json


def scrape_data(pokemon_name):
    url = f"https://pokemondb.net/pokedex/{pokemon_name}".replace(' ', '-').replace('é', 'e')
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        pokemon_data = {}
        
        # Scrape Pokédex data
        pokemon_tables = soup.find_all(class_='vitals-table')
        moves_tables = soup.find_all(class_='data-table')
        
        natdex_id, types, height, weight, abilities = scrape_pokedex_data(pokemon_tables)
        
        # Combine all scraped data into a dictionary
        pokemon_data['National Dex Number'] = natdex_id
        pokemon_data['Name'] = pokemon_name.capitalize().replace('é', 'e')
        pokemon_data['Types'] = types
        pokemon_data['Height'] = height.replace('′', '`').replace('″', "'")
        pokemon_data['Weight'] = weight
        pokemon_data['Abilities'] = abilities
        
        # Scrape and add base stats
        hp, atk, _def, spa, spd, spe, total = scrape_base_stats(pokemon_tables)
        pokemon_data['Base Stats'] = {
            "HP": hp,
            "Atk": atk,
            "Def": _def,
            "Spa": spa,
            "Spd": spd,
            "Spe": spe,
            "Total": total
        }
        
        # Scrape and add moves
        moves = scrape_pokemon_moves(moves_tables)
        pokemon_data['Moves'] = moves
        
        return pokemon_data
        
    else:
        print(f"Failed to fetch data for {pokemon_name}")
        return None


def scrape_pokedex_data(pokemon_tables):
    pokemon_vitals = pokemon_tables[0]
    data_cell = pokemon_vitals.find_all('td')
    
    natdex_id = data_cell[0].text.strip()
    types = "/".join([a.get_text(strip=True) for a in data_cell[1].find_all('a')])
    height = data_cell[3].text.split('(')[1].split(')')[0].strip()
    
    unformatted_weight = data_cell[4].text.split('(')[-1].strip()
    weight = unformatted_weight.split()[0] + " lbs"
            
    abilities = "/".join([a.get_text(strip=True) for a in data_cell[5].find_all('a')])
    
    return natdex_id, types, height, weight, abilities


def scrape_base_stats(pokemon_tables): 
    pokemon_vitals = pokemon_tables[3]
    data_cells = pokemon_vitals.find_all('td')

    hp = data_cells[0].text.strip()
    atk = data_cells[4].text.strip()
    _def = data_cells[8].text.strip()
    spa = data_cells[12].text.strip()
    spd = data_cells[16].text.strip()
    spe = data_cells[20].text.strip()
    total = data_cells[24].text.strip()
    
    return hp, atk, _def, spa, spd, spe, total


def scrape_pokemon_moves(moves_tables):
    all_moves = []
    try:
        for table in moves_tables[:-1]:
            
            move_data_rows = table.find_all('tr')[1:]

            for data in move_data_rows:
                column = data.find_all('td')

                if 'Lv.' in table.text or 'TM' in table.text:
                    move = {
                        "Name": column[1].text.strip(),
                        "Type": column[2].text.strip(),
                        "Category": column[3].get('data-sort-value', ''),
                        "Power": None if column[4].text.strip() in ['—', '∞'] else str(column[4].text.strip()),
                        "Accuracy": None if column[5].text.strip() in ['—', '∞'] else str(column[5].text.strip())
                    }
                
                else:
                    move = {
                        "Name": column[0].text.strip(),
                        "Type": column[1].text.strip(),
                        "Category": column[2].get('data-sort-value', ''),
                        "Power": None if column[3].text.strip() in ['—', '∞'] else str(column[3].text.strip()),
                        "Accuracy": None if column[4].text.strip() in ['—', '∞'] else str(column[4].text.strip())
                    }

                all_moves.append(move)
                
    except Exception as e:
        print("Error:", e)

    return all_moves


def main():
    url = "https://pokemondb.net/pokedex/game/scarlet-violet/indigo-disk"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extracting names of all Pokemon on the page
        pokemon_names_list = [a.text.lower() for a in soup.find_all('a', class_='ent-name')]
       
        # Fetching data for each Pokemon
        all_pokemon_data = []
        for pokemon_name in pokemon_names_list:
            pokemon_data = scrape_data(pokemon_name) 
            if pokemon_data:
                all_pokemon_data.append(pokemon_data)
        
        # Saving data to a JSON file
        with open('indigo_disk_data.json', 'w') as json_file:
            json.dump(all_pokemon_data, json_file, indent=4)
        
        print("Data saved")
    else:
        print("Failed to fetch data from the URL")


if __name__ == "__main__":
    main()

   



