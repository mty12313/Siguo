PIECE_RANKS = {
    "Flag": -1, #军棋
    "Mine": 0, #地雷
    "Bomb": 1, #炸弹 
    "Engineer": 32, #工兵
    "PlatoonLeader": 33, #排长
    "CompanyLeader": 34, #连长
    "BattalionLeader": 35, #营长
    "RegimentLeader": 36, #团长
    "Brigadier": 37, #旅长
    "DivisionCommander": 38, #师长
    "CorpsCommander": 39, #军长
    "General": 40 #司令
}


#标准棋子数量
MAX_COUNTS = {
    "Mine": 3,               # 地雷
    "Flag": 1,               # 军旗
    "Bomb": 2,               # 炸弹
    "Engineer": 3,           # 工兵
    "PlatoonLeader": 3,      # 排长
    "CompanyLeader": 3,      # 连长
    "BattalionLeader": 2,    # 营长
    "RegimentLeader": 2,     # 团长
    "Brigadier": 2,          # 旅长
    "DivisionCommander": 2,  # 师长
    "CorpsCommander": 1,     # 军长
    "General": 1             # 司令
}

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
        self.revealed = True
        self.alive = True
        self.movable = movable
        self.movable = name not in ("Mine", "Flag")

    def __repr__(self):
        status = "alive" if self.alive else "dead"
        return f"{self.owner} {self.name} ({status})"

    def reveal(self):
        self.revealed = True

    def kill(self):
        self.alive = False

    def can_defeat(self, other: 'Piece') -> bool: 
        if not self.alive or not other.alive:
            return False 
        
        if self.rank == 1 or other.rank == 1:
            return True  # The bomb kills itself and every piece it encounters

        if other.rank == 0:
            return self.rank == 32 #Mines can only be killed by Engineer

        if self.rank > other.rank:
            other.kill()
            return True
        elif self.rank < other.rank:
            self.kill()
            return False
        else:
            # 等级相同：同归于尽
            self.kill()
            other.kill()
            return False