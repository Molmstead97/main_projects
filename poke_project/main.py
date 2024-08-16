from fastapi import Depends, FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, delete
from sqlalchemy.orm import joinedload

from database import get_db
from models import Links, Pokemon, Moves, Item, PokemonResponse, StatsResponse, MovesResponse, Team, TeamMember, TeamMemberMove, TeamMemberResponse, TeamResponse

from api_insertion import fetch_data, insert_pokemon_data, insert_item, insert_move

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# ---- GET REQUESTS ----

# ----- GET POKEMON BY NAME -----
@app.get("/pokemon/{name}", response_model=PokemonResponse)
async def get_pokemon_by_name(name: str, db: Session = Depends(get_db)) -> PokemonResponse:
    pokemon = db.exec(select(Pokemon).where(Pokemon.name == name)).first()
    if pokemon:
        return pokemon

    pokemon_data = fetch_data('pokemon', name)
    if pokemon_data:
        inserted_pokemon = insert_pokemon_data(pokemon_data, db)
        if inserted_pokemon:
            return inserted_pokemon
        else:
            raise HTTPException(status_code=500, detail="Failed to insert Pokémon data")
    else:
        raise HTTPException(status_code=404, detail="Pokémon not found")


# ----- GET POKEMON STATS -----
@app.get("/pokemon/{name}/stats", response_model=StatsResponse)
async def get_pokemon_stats(name: str, db: Session = Depends(get_db)) -> StatsResponse:
    pokemon = db.exec(select(Pokemon).options(joinedload(Pokemon.base_stats)).where(Pokemon.name == name)).first()
    if not pokemon:
        raise HTTPException(status_code=404, detail="Pokémon not found")
    
    if not pokemon.base_stats:
        raise HTTPException(status_code=404, detail="Stats not found")
    
    return pokemon.base_stats

# ----- GET POKEMON MOVES -----
@app.get("/pokemon/{name}/moves", response_model=list[MovesResponse])
async def get_pokemon_moves(name: str, move: str = Query(default=None), db: Session = Depends(get_db)):
    pokemon = db.exec(select(Pokemon).options(joinedload(Pokemon.moves)).where(Pokemon.name == name)).first()
    if not pokemon:
        raise HTTPException(status_code=404, detail="Pokémon not found")
    
    if not pokemon.moves:
        raise HTTPException(status_code=404, detail="Moves not found")
    
    if move:
        filter_moves = [link.move for link in pokemon.moves if link.move_name == move]
        if not filter_moves:
            raise HTTPException(status_code=404, detail="Move not found for this Pokémon")
        
        sorted_moves = sorted(filter_moves, key=lambda move: move.name)
        return [MovesResponse.model_validate(move) for move in sorted_moves]
    
    sorted_moves = sorted([link.move for link in pokemon.moves], key=lambda move: move.name)
    return [MovesResponse.model_validate(move) for move in sorted_moves]

# ----- GET MOVES BY FILTER -----
@app.get("/moves", response_model=list[MovesResponse])
async def get_moves(move_type: str = Query(default=None), 
                    category: str = Query(default=None), 
                    min_power: int = Query(default=None),
                    max_power: int = Query(default=None),
                    min_accuracy: int = Query(default=None),
                    max_accuracy: int = Query(default=None), 
                    limit: int = Query(default=10, le=100, description="Limit the number of results"), 
                    offset: int = Query(default=0, description="Offset for pagination"), 
                    db: Session = Depends(get_db)):
    
    query = select(Moves)

    # Apply filters
    if move_type:
        query = query.where(Moves.move_type == move_type)
    if category:
        query = query.where(Moves.category == category)
    
    # Power filter
    if min_power is not None:
        query = query.where(Moves.power >= min_power)
    if max_power is not None:
        query = query.where(Moves.power <= max_power)
    
    # Accuracy filter
    if min_accuracy is not None:
        query = query.where(Moves.accuracy >= min_accuracy)
    if max_accuracy is not None:
        query = query.where(Moves.accuracy <= max_accuracy)
        
    # Sorting by alphabetical order
    query = query.order_by(Moves.name)

    # Apply pagination
    query = query.offset(offset).limit(limit)

    # Execute query
    moves = db.exec(query).all()

    # Convert Moves to MovesResponse
    try:
        return [MovesResponse.model_validate(move) for move in moves]
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Error validating move data: {str(e)}")

# ----- GET SPECIFIC MOVE ----
@app.get("/move/{name}", response_model=MovesResponse)
async def get_move_by_name(name: str, db: Session = Depends(get_db)) -> MovesResponse:
    move = db.exec(select(Moves).where(Moves.name == name)).first()
    if move:
        return move
    
    move_data = fetch_data('move', name)
    if move_data:
        inserted_move = insert_move(move_data, db)
        if inserted_move:
            return inserted_move
        else:
            raise HTTPException(status_code=500, detail="Failed to insert move data")
    else:
        raise HTTPException(status_code=404, detail="Move not found")

# ----- GET ITEM -----
@app.get("/item/{name}", response_model=Item)
async def get_item(name: str, db: Session = Depends(get_db)) -> Item:
    item = db.exec(select(Item).where(Item.name == name)).first()
    if item:
        return item

    item_data = fetch_data('item', name)
    if item_data:
        inserted_item = insert_item(item_data, db)
        if inserted_item:
            return inserted_item
        else:
            raise HTTPException(status_code=500, detail="Failed to insert item data")
    else:
       raise HTTPException(status_code=404, detail="Item not found")
   
# ----- GET ALL TEAMS -----
@app.get("/teams")
async def get_all_teams(db: Session = Depends(get_db)):
    teams = db.exec(select(Team)).all()
    return [{"team_id": team.id, "team_name": team.name} for team in teams]

# ----- GET SPECIFIC TEAM, INCLUDES POKEMON DATA -----
@app.get("/teams/{team_name}", response_model=TeamResponse)
async def get_team_by_name(team_name: str, db: Session = Depends(get_db)):
    team = db.exec(select(Team).where(Team.name == team_name)).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    team_members = []
    for member in team.members:
        moves = [move.move_name for move in member.team_member_moves]
        item_name = member.item.name if member.item else None  

        # Build the response data
        team_member_response = TeamMemberResponse(
            id=member.id,
            pokemon_name=member.pokemon.name,
            ability=member.ability,
            item_name=item_name,
            moves=moves
        )
        team_members.append(team_member_response)

    return TeamResponse(
        id=team.id,
        name=team.name,
        members=team_members
    )
    
# ----- GET SPECIFIC POKEMON IN TEAM -----
@app.get("/teams/{team_name}/pokemon/{pokemon_name}", response_model=TeamMemberResponse)
async def get_pokemon_on_team(team_name: str, pokemon_name: str, db: Session = Depends(get_db)):
    team = db.exec(select(Team).where(Team.name == team_name)).first()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Find the specific Pokémon on the team
    pokemon_member = next(
        (member for member in team.members if member.pokemon.name == pokemon_name),
        None
    )

    if not pokemon_member:
        raise HTTPException(status_code=404, detail=f"{pokemon_name} not found on the team")

    return TeamMemberResponse(
        id=pokemon_member.id,
        pokemon_name=pokemon_member.pokemon.name,
        ability=pokemon_member.ability,
        item_name=pokemon_member.item.name if pokemon_member.item else None,
        moves=[move.move_name for move in pokemon_member.team_member_moves]
    )

# ---- POST REQUESTS ----

@app.post("/teams/create")
async def create_team(
    team_name: str,
    
    pokemon_1: str,
    pokemon_1_ability: str = Query(None),
    pokemon_1_item: str = Query(None),
    pokemon_1_move_1: str = Query(None),
    pokemon_1_move_2: str = Query(None),
    pokemon_1_move_3: str = Query(None),
    pokemon_1_move_4: str = Query(None),
    
    pokemon_2: str = Query(None),
    pokemon_2_ability: str = Query(None),
    pokemon_2_item: str = Query(None),
    pokemon_2_move_1: str = Query(None),
    pokemon_2_move_2: str = Query(None),
    pokemon_2_move_3: str = Query(None),
    pokemon_2_move_4: str = Query(None),
    
    pokemon_3: str = Query(None),
    pokemon_3_ability: str = Query(None),
    pokemon_3_item: str = Query(None),
    pokemon_3_move_1: str = Query(None),
    pokemon_3_move_2: str = Query(None),
    pokemon_3_move_3: str = Query(None),
    pokemon_3_move_4: str = Query(None),
    
    pokemon_4: str = Query(None),
    pokemon_4_ability: str = Query(None),
    pokemon_4_item: str = Query(None),
    pokemon_4_move_1: str = Query(None),
    pokemon_4_move_2: str = Query(None),
    pokemon_4_move_3: str = Query(None),
    pokemon_4_move_4: str = Query(None),
    
    pokemon_5: str = Query(None),
    pokemon_5_ability: str = Query(None),
    pokemon_5_item: str = Query(None),
    pokemon_5_move_1: str = Query(None),
    pokemon_5_move_2: str = Query(None),
    pokemon_5_move_3: str = Query(None),
    pokemon_5_move_4: str = Query(None),
    
    pokemon_6: str = Query(None),
    pokemon_6_ability: str = Query(None),
    pokemon_6_item: str = Query(None),
    pokemon_6_move_1: str = Query(None),
    pokemon_6_move_2: str = Query(None),
    pokemon_6_move_3: str = Query(None),
    pokemon_6_move_4: str = Query(None),
    
    db: Session = Depends(get_db)
):
    # Check if team name already exists
    existing_team = db.exec(select(Team).where(Team.name == team_name)).first()
    if existing_team:
        raise HTTPException(status_code=400, detail="Team name already exists")

    # Create new team
    new_team = Team(name=team_name)
    db.add(new_team)
    db.commit()
    db.refresh(new_team)

    pokemon_data = [
        (pokemon_1, pokemon_1_ability, pokemon_1_item, [pokemon_1_move_1, pokemon_1_move_2, pokemon_1_move_3, pokemon_1_move_4]),
        (pokemon_2, pokemon_2_ability, pokemon_2_item, [pokemon_2_move_1, pokemon_2_move_2, pokemon_2_move_3, pokemon_2_move_4]),
        (pokemon_3, pokemon_3_ability, pokemon_3_item, [pokemon_3_move_1, pokemon_3_move_2, pokemon_3_move_3, pokemon_3_move_4]),
        (pokemon_4, pokemon_4_ability, pokemon_4_item, [pokemon_4_move_1, pokemon_4_move_2, pokemon_4_move_3, pokemon_4_move_4]),
        (pokemon_5, pokemon_5_ability, pokemon_5_item, [pokemon_5_move_1, pokemon_5_move_2, pokemon_5_move_3, pokemon_5_move_4]),
        (pokemon_6, pokemon_6_ability, pokemon_6_item, [pokemon_6_move_1, pokemon_6_move_2, pokemon_6_move_3, pokemon_6_move_4])
    ]

    pokemon_data = [(name, ability, item, [move for move in moves if move]) 
                    for name, ability, item, moves in pokemon_data if name]

    for pokemon_name, ability, item_name, moves in pokemon_data:
        pokemon = db.exec(select(Pokemon).where(Pokemon.name == pokemon_name)).first()
        if not pokemon:
            raise HTTPException(status_code=404, detail=f"Pokémon {pokemon_name} not found")

        if ability:
            pokemon_abilities = pokemon.abilities.split('/')
            if ability not in pokemon_abilities:
                raise HTTPException(status_code=404, detail=f"{pokemon_name} cannot have the ability {ability}")

        pokemon_moves = db.exec(select(Links).where(Links.pokemon_name == pokemon.name)).all()
        pokemon_move_names = {link.move_name for link in pokemon_moves}

        valid_moves = []
        for move_name in moves:
            if move_name not in pokemon_move_names:
                raise HTTPException(status_code=404, detail=f"{pokemon_name} cannot learn {move_name}")
            move = db.exec(select(Moves).where(Moves.name == move_name)).first()
            if not move:
                raise HTTPException(status_code=404, detail=f"{move_name} not found")
            valid_moves.append(move)

        if item_name:
            item = db.exec(select(Item).where(Item.name == item_name)).first()
            if not item:
                raise HTTPException(status_code=404, detail=f"Item {item_name} not found")
            item_id = item.id
        else:
            item_id = None

        # Create team member and associate moves
        team_member = TeamMember(team_id=new_team.id, pokemon_id=pokemon.natdex_id, item_id=item_id)
        db.add(team_member)
        db.commit()
        db.refresh(team_member)

        for move in valid_moves:
            team_member_move = TeamMemberMove(team_member_id=team_member.id, move_name=move.name)
            db.add(team_member_move)

    db.commit()
    return {"message": "Team created successfully", "team_name": team_name}


# ----PUT REQUESTS----

@app.put("/teams/update")
async def update_team(
    team_name: str,
    
    pokemon_1: str,
    pokemon_1_ability: str = Query(None),
    pokemon_1_item: str = Query(None),
    pokemon_1_move_1: str = Query(None),
    pokemon_1_move_2: str = Query(None),
    pokemon_1_move_3: str = Query(None),
    pokemon_1_move_4: str = Query(None),
    
    pokemon_2: str = Query(None),
    pokemon_2_ability: str = Query(None),
    pokemon_2_item: str = Query(None),
    pokemon_2_move_1: str = Query(None),
    pokemon_2_move_2: str = Query(None),
    pokemon_2_move_3: str = Query(None),
    pokemon_2_move_4: str = Query(None),
    
    pokemon_3: str = Query(None),
    pokemon_3_ability: str = Query(None),
    pokemon_3_item: str = Query(None),
    pokemon_3_move_1: str = Query(None),
    pokemon_3_move_2: str = Query(None),
    pokemon_3_move_3: str = Query(None),
    pokemon_3_move_4: str = Query(None),
   
    pokemon_4: str = Query(None),
    pokemon_4_ability: str = Query(None),
    pokemon_4_item: str = Query(None),
    pokemon_4_move_1: str = Query(None),
    pokemon_4_move_2: str = Query(None),
    pokemon_4_move_3: str = Query(None),
    pokemon_4_move_4: str = Query(None),
    
    pokemon_5: str = Query(None),
    pokemon_5_ability: str = Query(None),
    pokemon_5_item: str = Query(None),
    pokemon_5_move_1: str = Query(None),
    pokemon_5_move_2: str = Query(None),
    pokemon_5_move_3: str = Query(None),
    pokemon_5_move_4: str = Query(None),
    
    pokemon_6: str = Query(None),
    pokemon_6_ability: str = Query(None),
    pokemon_6_item: str = Query(None),
    pokemon_6_move_1: str = Query(None),
    pokemon_6_move_2: str = Query(None),
    pokemon_6_move_3: str = Query(None),
    pokemon_6_move_4: str = Query(None),
    
    db: Session = Depends(get_db)
):
    # Fetch the team by name
    team = db.exec(select(Team).where(Team.name == team_name)).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Process each Pokémon
    pokemon_data = [
        (pokemon_1, pokemon_1_ability, pokemon_1_item, [pokemon_1_move_1, pokemon_1_move_2, pokemon_1_move_3, pokemon_1_move_4]),
        (pokemon_2, pokemon_2_ability, pokemon_2_item, [pokemon_2_move_1, pokemon_2_move_2, pokemon_2_move_3, pokemon_2_move_4]),
        (pokemon_3, pokemon_3_ability, pokemon_3_item, [pokemon_3_move_1, pokemon_3_move_2, pokemon_3_move_3, pokemon_3_move_4]),
        (pokemon_4, pokemon_4_ability, pokemon_4_item, [pokemon_4_move_1, pokemon_4_move_2, pokemon_4_move_3, pokemon_4_move_4]),
        (pokemon_5, pokemon_5_ability, pokemon_5_item, [pokemon_5_move_1, pokemon_5_move_2, pokemon_5_move_3, pokemon_5_move_4]),
        (pokemon_6, pokemon_6_ability, pokemon_6_item, [pokemon_6_move_1, pokemon_6_move_2, pokemon_6_move_3, pokemon_6_move_4])
    ]

    pokemon_data = [(name, ability, item, [move for move in moves if move]) 
                    for name, ability, item, moves, in pokemon_data if name]

    existing_members = {member.id: member for member in team.members}
    new_team_member_ids = set()

    for i, (pokemon_name, ability_name, item_name, moves) in enumerate(pokemon_data):
        
        pokemon = db.exec(select(Pokemon).where(Pokemon.name == pokemon_name)).first()
        if not pokemon:
            raise HTTPException(status_code=404, detail=f"{pokemon_name} not found")

        if ability_name:
            pokemon_abilities = pokemon.abilities.split("/")
            if ability_name not in pokemon_abilities:
                raise HTTPException(status_code=404, detail=f"{pokemon_name} cannot have the ability {ability_name}")

        if moves is None:
            moves = []
        
        pokemon_moves = db.exec(select(Links).where(Links.pokemon_name == pokemon.name)).all()
        pokemon_move_names = {link.move_name for link in pokemon_moves}
        
        valid_moves = []
        for move_name in moves:
            if move_name not in pokemon_move_names:
                raise HTTPException(status_code=404, detail=f"{pokemon_name} cannot learn {move_name}")

            move = db.exec(select(Moves).where(Moves.name == move_name)).first()
            if not move:
                raise HTTPException(status_code=404, detail=f"{move_name} not found")

            valid_moves.append(move)

        if item_name:
            item = db.exec(select(Item).where(Item.name == item_name)).first()
            if not item:
                raise HTTPException(status_code=404, detail=f"{item_name} not found")
            item_id = item.id
        else:
            item_id = None

        # Determine the team member to update or create
        if i < len(team.members):
            team_member = team.members[i]
            new_team_member_ids.add(team_member.id)
        else:
            team_member = TeamMember(team_id=team.id, pokemon_id=pokemon.natdex_id, item_id=item_id)
            db.add(team_member)
            new_team_member_ids.add(team_member.id)
        
        # Update team member details
        team_member.pokemon_id = pokemon.natdex_id
        team_member.item_id = item_id
        team_member.ability = ability_name  # Set the ability for the team member

        # Clear existing moves in the team context
        db.exec(delete(TeamMemberMove).where(TeamMemberMove.team_member_id == team_member.id))

        # Add new moves specific to the team member
        for move in valid_moves:
            team_member_move = TeamMemberMove(team_member_id=team_member.id, move_name=move.name)
            db.add(team_member_move)

    # Remove extra team members and their moves
    extra_member_ids = set(existing_members.keys()) - new_team_member_ids
    if extra_member_ids:
    # Delete all associated moves for the team members being removed
        db.exec(delete(TeamMemberMove).where(TeamMemberMove.team_member_id.in_(extra_member_ids)))
    
    # Delete the team members
    db.exec(delete(TeamMember).where(TeamMember.id.in_(extra_member_ids)))

    # Remove any extra team members
    extra_member_ids = set(existing_members.keys()) - new_team_member_ids
    if extra_member_ids:
        db.exec(delete(TeamMember).where(TeamMember.id.in_(extra_member_ids)))

    # Commit changes to the database
    db.commit()
    return {"message": "Team updated successfully", "team_name": team.name}


# ----DELETE REQUESTS----

@app.delete("/teams/delete")
async def delete_team(team_name: str, db: Session = Depends(get_db)):
    
    team = db.exec(select(Team).where(Team.name == team_name)).first()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    db.exec(delete(TeamMemberMove).where(TeamMemberMove.team_member_id.in_(
        select(TeamMember.id).where(TeamMember.team_id == team.id)
    )))
    db.exec(delete(TeamMember).where(TeamMember.team_id == team.id))

    db.exec(delete(Team).where(Team.id == team.id))

    db.commit()

    return {"message": f"Team '{team_name}' deleted successfully"}




