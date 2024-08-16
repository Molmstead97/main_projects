from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List

# ----- MAIN MODELS -----

class Links(SQLModel, table=True):
    __tablename__ = 'links'
    pokemon_name: str = Field(foreign_key='pokemon.name', primary_key=True)
    move_name: str = Field(foreign_key='moves.name', primary_key=True)
    pokemon: 'Pokemon' = Relationship(back_populates='moves')
    move: 'Moves' = Relationship(back_populates='pokemon')

class Pokemon(SQLModel, table=True):
    __tablename__ = 'pokemon'
    natdex_id: int = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    pokemon_type: str
    abilities: str
    base_stats_id: Optional[int] = Field(default=None, foreign_key='stats.id', nullable=True)
    base_stats: 'Stats' = Relationship(back_populates='pokemon')
    moves: List[Links] = Relationship(back_populates='pokemon')  

class Moves(SQLModel, table=True):
    __tablename__ = 'moves'
    name: str = Field(default=None, primary_key=True)
    move_type: str
    category: str
    power: Optional[int] = Field(default=None, nullable=True)
    accuracy: Optional[int] = Field(default=None, nullable=True)
    description: str
    pokemon: List[Links] = Relationship(back_populates='move')  # Many-to-Many with Pokemon

class Stats(SQLModel, table=True):
    __tablename__ = 'stats'
    id: int = Field(default=None, primary_key=True)
    hp: int
    atk: int
    def_: int
    spa: int
    spd: int
    spe: int
    total: Optional[int] = Field(default=None, nullable=True)
    pokemon: List['Pokemon'] = Relationship(back_populates='base_stats')

class Item(SQLModel, table=True):
    __tablename__ = 'items'
    id: int = Field(default=None, primary_key=True)
    name: str
    description: str

# ------ RESPONSE MODELS -----

class PokemonResponse(SQLModel):
    natdex_id: int
    name: str
    pokemon_type: str
    abilities: str
    
    class Config:
        from_attributes = True
        
class StatsResponse(SQLModel):
    hp: int
    atk: int
    def_: int
    spa: int
    spd: int
    spe: int
    total: int
    
    class Config:
        from_attributes = True
        
class MovesResponse(SQLModel):
    name: str
    move_type: str
    category: str
    power: int | None
    accuracy: int | None
    description: str
    
    class Config:
        from_attributes = True
        
class TeamMemberResponse(SQLModel):
    id: int
    pokemon_name: str
    ability: Optional[str]
    item_name: Optional[str]
    moves: List[str]

    class Config:
        from_attributes = True

class TeamResponse(SQLModel):
    id: int
    name: str
    members: List[TeamMemberResponse]

    class Config:
        from_attributes = True

# ----- TEAM MODELS ------

class TeamMemberMove(SQLModel, table=True):
    __tablename__ = 'team_member_moves'
    id: Optional[int] = Field(default=None, primary_key=True)
    team_member_id: int = Field(foreign_key="team_members.id")
    move_name: str = Field(foreign_key="moves.name")
    move: Moves = Relationship()
    team_member: "TeamMember" = Relationship(back_populates="team_member_moves")

class TeamMember(SQLModel, table=True):
    __tablename__ = 'team_members'
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: int = Field(foreign_key="teams.id")
    pokemon_id: int = Field(foreign_key="pokemon.natdex_id")
    item_id: Optional[int] = Field(foreign_key="items.id", default=None)
    ability: Optional[str] = Field(default=None)
    team: "Team" = Relationship(back_populates="members")
    pokemon: Pokemon = Relationship()
    item: Optional[Item] = Relationship()
    team_member_moves: List[TeamMemberMove] = Relationship(back_populates="team_member") 

class Team(SQLModel, table=True):
    __tablename__ = 'teams'
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    members: List[TeamMember] = Relationship(back_populates="team")
    

