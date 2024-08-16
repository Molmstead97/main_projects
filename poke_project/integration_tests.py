import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session, select

from main import app, get_db
from models import Team, Pokemon, Item, Moves, Links

# Use a separate test database
TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost/test_database"

# Create the test database engine
test_engine = create_engine(TEST_DATABASE_URL)

# Override the get_db dependency to use the test database
def override_get_db():
    with Session(test_engine) as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Fixture to reset the test database before each test
@pytest.fixture(autouse=True)
def reset_database():
    SQLModel.metadata.drop_all(test_engine)
    SQLModel.metadata.create_all(test_engine)

    # Insert test data into the test database
    with Session(test_engine) as session:
        # Insert Pokémon data
        pikachu = Pokemon(name="Pikachu", natdex_id=25, pokemon_type="Electric", abilities="Static")
        bulbasaur = Pokemon(name="Bulbasaur", natdex_id=1, pokemon_type="Grass", abilities="Overgrow")
        charizard = Pokemon(name="Charizard", natdex_id=6, pokemon_type="Fire", abilities="Blaze")
        squirtle = Pokemon(name="Squirtle", natdex_id=7, pokemon_type="Water", abilities="Torrent")
        session.add_all([pikachu, bulbasaur, charizard, squirtle])

        # Insert Move data
        thunderbolt = Moves(name="Thunderbolt", move_type="Electric", category="special", power=90, accuracy=100, description="")
        quick_attack = Moves(name="Quick Attack", move_type="Normal", category="physical", power=40, accuracy=100, description="")
        vine_whip = Moves(name="Vine Whip", move_type="Grass", category="physcial", power=50, accuracy=100, description="")
        flamethrower = Moves(name="Flamethrower", move_type="Fire", category="special", power=90, accuracy=100, description="")
        water_gun = Moves(name="Water Gun", move_type="Water", category="special", power=40, accuracy=100, description="")

        session.add_all([thunderbolt, quick_attack, vine_whip, flamethrower, water_gun])

        # Insert Item data
        light_ball = Item(name="Light Ball", description="A ball that boosts Pikachu's power.")
        miracle_seed = Item(name="Miracle Seed", description="A seed that boosts Grass-type moves.")
        charcoal = Item(name="Charcoal", description="An item that boosts Fire-type moves.")
        mystic_water = Item(name="Mystic Water", description="An item that boosts Water-type moves.")

        session.add_all([light_ball, miracle_seed, charcoal, mystic_water])

        # Insert Links (for Pokémon moves)
        session.add_all([
            Links(pokemon_name="Pikachu", move_name="Thunderbolt"),
            Links(pokemon_name="Pikachu", move_name="Quick Attack"),
            Links(pokemon_name="Bulbasaur", move_name="Vine Whip"),
            Links(pokemon_name="Charizard", move_name="Flamethrower"),
            Links(pokemon_name="Squirtle", move_name="Water Gun")
        ])

        # Commit the data to the test database
        session.commit()


# Test POST request - Create a new team
def test_create_team():
    # Sample data for creating a team
    data = {
        "team_name": "Test Team",
        "pokemon_1": "Pikachu",
        "pokemon_1_ability": "Static",
        "pokemon_1_item": "Light Ball",
        "pokemon_1_move_1": "Thunderbolt",
        "pokemon_1_move_2": "Quick Attack",
        "pokemon_2": "Bulbasaur",
        "pokemon_2_ability": "Overgrow",
        "pokemon_2_item": "Miracle Seed",
        "pokemon_2_move_1": "Vine Whip"
    }

    response = client.post("/teams/create", params=data)

    assert response.status_code == 200
    assert response.json() == {
        "message": "Team created successfully",
        "team_name": "Test Team"
    }

    # Fetch the team from the database to ensure it's correctly created
    with Session(test_engine) as session:
        team = session.exec(select(Team).where(Team.name == "Test Team")).first()

        assert team is not None
        assert team.name == "Test Team"
        assert len(team.members) == 2


# Test PUT request - Update an existing team
@pytest.mark.asyncio
async def test_update_team():
    # Create a team first using the POST request
    data = {
        "team_name": "Test Team",
        "pokemon_1": "Pikachu",
        "pokemon_1_ability": "Static",
        "pokemon_1_item": "Light Ball",
        "pokemon_1_move_1": "Thunderbolt",
        "pokemon_1_move_2": "Quick Attack",
        "pokemon_2": "Bulbasaur",
        "pokemon_2_ability": "Overgrow",
        "pokemon_2_item": "Miracle Seed",
        "pokemon_2_move_1": "Vine Whip"
    }

    response = client.post("/teams/create", params=data)
    assert response.status_code == 200

    # Now update the team with different Pokémon data
    update_data = {
        "team_name": "Test Team",
        "pokemon_1": "Charizard",
        "pokemon_1_ability": "Blaze",
        "pokemon_1_item": "Charcoal",
        "pokemon_1_move_1": "Flamethrower",
        "pokemon_2": "Squirtle",
        "pokemon_2_ability": "Torrent",
        "pokemon_2_item": "Mystic Water",
        "pokemon_2_move_1": "Water Gun"
    }

    response = client.put("/teams/info", params=update_data)

    assert response.status_code == 200
    assert response.json() == {
        "message": "Team updated successfully",
        "team_name": "Test Team"
    }

    # Fetch the team from the database and verify updates
    with Session(test_engine) as session:
        team = session.exec(select(Team).where(Team.name == "Test Team")).first()

        assert team is not None
        assert len(team.members) == 2

        # Verify that team members are updated correctly
        first_member = team.members[0]
        assert first_member.pokemon.name == "Charizard"
        assert first_member.ability == "Blaze"
        assert first_member.item.name == "Charcoal"
        assert len(first_member.team_member_moves) == 1
        assert first_member.team_member_moves[0].move_name == "Flamethrower"