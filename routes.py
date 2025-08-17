# routes.py - Board Connectivity Module for Four Kingdoms Military Chess

# This module defines all road and railway connections on the 17x17 game board.
# It is responsible for setting up, storing, and querying the connectivity between
# grid cells, including special movement rules for railways.

# Enum for connection types between cells
from enum import Enum
from constants import special_paths, camp_positions, center_blocks

class LineType(Enum):
    ROAD = 1
    RAIL = 2

# Stores all connectivity information on the board.
# connections[(x, y)] = list of ((neighbor_x, neighbor_y), LineType)
connections = {}

# Add a bidirectional connection between two adjacent cells with the specified line type.
def add_connection(x1, y1, x2, y2, line_type):
    connections.setdefault((x1, y1), []).append(((x2, y2), line_type))
    connections.setdefault((x2, y2), []).append(((x1, y1), line_type))

# Get all neighbors connected to cell (x, y).
def get_connections(x, y):
    return connections.get((x, y), [])

# Check if (x1, y1) and (x2, y2) are connected by the given line type.
def is_connected_by(x1, y1, x2, y2, line_type):
    return any((nx, ny) == (x2, y2) and t == line_type
               for (nx, ny), t in get_connections(x1, y1))

#  Determine whether the cell at (row, col) is part of the valid game area.
#  Excludes four corner quadrants and central blocked positions.
def is_displayable(row, col):
    if (row < 6 and col < 6) or (row < 6 and col >= 11) or \
       (row >= 11 and col < 6) or (row >= 11 and col >= 11):
        return False
    center_blocks = {
        (6, 7), (6, 9),
        (7, 6), (7, 7), (7, 8), (7, 9), (7, 10),
        (8, 7), (8, 9),
        (9, 6), (9, 7), (9, 8), (9, 9), (9, 10),
        (10, 7), (10, 9)
    }
    if (row, col) in center_blocks:
        return False
    return True

def setup_rail_connections():
    # Vertical rails
    for y in range(1, 15):
        add_connection(6, y, 6, y+1, LineType.RAIL)    # 6,1 → 6,15
        add_connection(10, y, 10, y+1, LineType.RAIL)  # 10,1 → 10,15
    for y in range(6, 10):
        add_connection(15, y, 15, y+1, LineType.RAIL)  # 15,6 → 15,10

    # Horizontal rails
    for x in range(1, 15):
        add_connection(x, 6, x+1, 6, LineType.RAIL)    # 1,6 → 15,6
        add_connection(x, 10, x+1, 10, LineType.RAIL)  # 1,10 → 15,10

    # Short horizontal ends (top/bottom)
    for x in range(6, 10):
        add_connection(x, 1, x+1, 1, LineType.RAIL)     # 6,1 → 10,1
        add_connection(x, 15, x+1, 15, LineType.RAIL)   # 6,15 → 10,15
    for y in range(6, 10):
        add_connection(1, y, 1, y+1, LineType.RAIL)     # 1,6 → 1,10

    # Diagonal connections (4 corners of central rails)
    add_connection(5, 6, 6, 5, LineType.RAIL)
    add_connection(5, 10, 6, 11, LineType.RAIL)
    add_connection(10, 5, 11, 6, LineType.RAIL)
    add_connection(10, 11, 11, 10, LineType.RAIL)

    # Middle horizontal lines
    # 6,5 → 10,5
    for x in range(6, 10):
        add_connection(x, 5, x+1, 5, LineType.RAIL)
    # 5,6 → 5,10
    for y in range(6, 10):
        add_connection(5, y, 5, y+1, LineType.RAIL)
    # 6,9 → 10,9
    for x in range(6, 10):
        add_connection(x, 11, x+1, 11, LineType.RAIL)
    # 11,6 → 11,10
    for y in range(6, 10):
        add_connection(11, y, 11, y+1, LineType.RAIL)

    ## Cross shape in center
    for y in range(5, 11):
        add_connection(8, y, 8, y+1, LineType.RAIL)

    for x in range(5, 11):
        add_connection(x, 8, x+1, 8, LineType.RAIL)

def setup_connections(rows=17, cols=17):
    # Automatically initialize all road and rail connections on the board.
    #Roads are created between all adjacent displayable cells except those already connected by rail.
    for y in range(rows):
        for x in range(cols):
            if not is_displayable(y, x):
                continue
            for dx, dy in ((1, 0), (0, 1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < cols and 0 <= ny < rows and is_displayable(ny, nx)):
                    continue
                if is_connected_by(x, y, nx, ny, LineType.RAIL):
                    continue
                add_connection(x, y, nx, ny, LineType.ROAD)

    setup_rail_connections()

setup_connections()

# Add diagonal road connections between each camp cell and its four diagonals
for x, y in camp_positions:
    for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < 17 and 0 <= ny < 17:
            add_connection(x, y, nx, ny, LineType.ROAD)

