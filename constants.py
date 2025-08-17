# constants.py
# This module stores shared configuration constants such as camp and headquarter positions
# for the Four Kingdoms Military Chess game.

# Board size (17x17 standard)
BOARD_SIZE = 17

#Ranks
PIECE_RANKS = {
    "Flag": -1,                 #军棋
    "Mine": 41,                 #地雷
    "Bomb": 1,                  #炸弹 
    "Engineer": 32,             #工兵
    "PlatoonLeader": 33,        #排长
    "CompanyLeader": 34,        #连长
    "BattalionLeader": 35,      #营长
    "RegimentLeader": 36,       #团长
    "Brigadier": 37,            #旅长
    "DivisionCommander": 38,    #师长
    "CorpsCommander": 39,       #军长
    "General": 40               #司令
}


#Standard Piece Numbers
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

# Camp positions on the board. Pieces in camps cannot be attacked.
camp_positions = [
    (2, 7), (4, 7), (14, 7), (12, 7),
    (2, 9), (4, 9), (14, 9), (12, 9),
    (3, 8), (13, 8),
    (7, 2), (7, 4), (7, 12), (7, 14),
    (9, 2), (9, 4), (9, 12), (9, 14),
    (8, 3), (8, 13)
]

# Headquarter positions. Pieces in HQ cannot move.
hq_positions = [
    (0, 7), (7, 0), (0, 9), (9, 0),
    (16, 7), (7, 16), (16, 9), (9, 16)
]

# Alliance mapping: Red+Green are team 1, Blue+Yellow are team 2
ALLIANCE = {
    "Red": 1,
    "Green": 1,
    "Blue": 2,
    "Yellow": 2,
}

#Special railway L-shaped paths used for engineer movement logic
special_paths = [
    [(1,6),(2,6),(3,6),(4,6),(5,6),(6,5),(6,4),(6,3),(6,2),(6,1)],
    [(1,10),(2,10),(3,10),(4,10),(5,10),(6,11),(6,12),(6,13),(6,14),(6,15)],
    [(10,1),(10,2),(10,3),(10,4),(10,5),(11,6),(12,6),(13,6),(14,6),(15,6)],
    [(10,15),(10,14),(10,13),(10,12),(10,11),(11,10),(12,10),(13,10),(14,10),(15,10)],
]

#Center blocks
center_blocks = {
        (6, 7), (6, 9),
        (7, 6), (7, 7), (7, 8), (7, 9), (7, 10),
        (8, 7), (8, 9),
        (9, 6), (9, 7), (9, 8), (9, 9), (9, 10),
        (10, 7), (10, 9)
    }

# Zones assigned to each player for initial piece placement (x1, y1, x2, y2)
COLOR_ZONES = {
    "Red":    (6, 11, 10, 16),
    "Green":  (6, 0, 10, 5),
    "Blue":   (0, 6, 5, 10),
    "Yellow": (11, 6, 16, 10),
}

# RGB color mapping for each player
OWNER_TO_COLOR = {
    "Red":    (255, 0, 0),
    "Green":  (0, 200, 0),
    "Blue":   (0, 100, 255),
    "Yellow": (200, 200, 0),
}

# Cells where Mines are allowed (edges of the board)
ALLOWED_MINE_CELLS = {
    (row, col)
    for row in range(17)
    for col in range(17)
    if row in (0, 1, 15, 16) or col in (0, 1, 15, 16)
}

# Cells where Bombs are NOT allowed (central critical rows and columns)
FORBIDDEN_BOMB_CELLS = {
    (row, col)
    for row in range(17)
    for col in range(17)
    if row in (5, 11) or col in (5, 11)
}

# Designated Headquarter (Flag) positions
ALLOWED_FLAG_CELLS = {
    (0, 7), (7, 0), (0, 9), (9, 0),
    (16, 7), (7, 16), (16, 9), (9, 16)
}