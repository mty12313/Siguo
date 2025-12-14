# Mapping of piece names to their rank values (lower rank = weaker, except for special rules)
# Special pieces have fixed behavior:
# - Flag: immobile and must be captured to win
# - Mine: cannot move, only defeated by Engineer
# - Bomb: defeats any piece but also dies
# - Engineer: can defuse Mines
from constants import PIECE_RANKS, MAX_COUNTS
import itertools
_type_counters: dict[str, itertools.count] = {}

name_map = {
    "旗": "Flag",
    "雷": "Mine",
    "炸": "Bomb",
    "兵": "Engineer",
    "排": "PlatoonLeader",
    "连": "CompanyLeader",
    "营": "BattalionLeader",
    "团": "RegimentLeader",
    "旅": "Brigadier",
    "师": "DivisionCommander",
    "军": "CorpsCommander",
    "司": "General",
}

EN2CN = {v: k for k, v in name_map.items()}

class Piece:
    name: str
    rank: int
    owner: str
    revealed: bool
    alive: bool
    movable: bool

    def __init__(self, name, rank, owner, movable=True):
        self.name = name 
        self.rank = rank
        self.owner = owner
        self.revealed = True #If the piece can be seen
        self.alive = True   #If the piece is alive
        self.movable = movable  #If the piece is movable
        self.movable = name not in ("Mine", "Flag") #Flag and Mine can't be moved

        if name not in _type_counters:
            _type_counters[name] = itertools.count(1)
        short = EN2CN.get(name, name[:2])
        self.uid = f"{short}{next(_type_counters[name])}"

    # Return a string representation of the piece for debugging and display.
    def __repr__(self):
        status = "alive" if self.alive else "dead"
        return f"{self.owner} {self.name} ({status})"

    # Mark this piece as revealed
    def reveal(self):
        self.revealed = True

    # Mark this piece as no longer alive
    def kill(self):
        self.alive = False

    #Determine whether this piece can defeat the other piece in battle
    def can_defeat(self, other: 'Piece') -> bool: 
        #Dead piece can't be attack or attack others
        if not self.alive or not other.alive:
            return False 
        
        # The bomb kills itself and every piece it encounters
        if self.rank == 1 or other.rank == 1:
            return True  

        #Mines can only be killed by Engineer except the bomb
        if other.rank == 0:
            return self.rank == 32 

        #According to the rank
        if self.rank > other.rank:
            other.kill()
            return True
        elif self.rank < other.rank:
            self.kill()
            return False
        else:
            # If the rank is the same. Kill both
            self.kill()
            other.kill()
            return False