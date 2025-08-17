# chessboard.py - Chessboard Management Module for Four Kingdoms Military Chess

# This module defines the `ChessBoard` class, which handles the layout, structure, and movement logic of the 17x17 game board.
# It serves as the foundation of the game logic and interacts closely with pieces (piece.py), path types (routes.py),
# and gameplay rules (game.py).

# Key responsibilities:
# - Initialize a 17x17 board, distinguishing valid and invalid cells (e.g., corners and central forbidden zones)
# - Place and remove game pieces on the board
# - Determine whether two positions are connected via road or railway
# - Implement movement rules for different piece types:
#   - Engineers can travel freely along connected railway paths
#   - Non-engineer pieces can only move in straight lines or arcs on railways (no right-angle turns)
# - Provide utility functions for validating legal moves during gameplay

from typing import List, Tuple
from piece import Piece
from routes import is_connected_by, get_connections, LineType
from constants import BOARD_SIZE, camp_positions, hq_positions, ALLIANCE, MAX_COUNTS, special_paths, center_blocks

class ChessBoard:
    #_init_ defines an empty 17*17 board
    def __init__(self):
        self.grid = []
        for i in range(17):
            row = []
            for j in range(17):
                row.append(None)
            self.grid.append(row)
        self.rows = len(self.grid)
        self.cols = len(self.grid[0])
        from constants import ALLIANCE as DEFAULT_ALLIANCE
        self.alliance_map = DEFAULT_ALLIANCE.copy()
    
    def set_alliance_map(self, new_map: dict[str,int]):
        """模式切换时调用，传入想要的 owner->阵营  映射"""
        self.alliance_map = new_map

    # Some of the cell is invalid
    def is_valid_cell(self, x: int, y: int) -> bool:
    # Out of Bound
        if not (0 <= x < 17 and 0 <= y < 17):
            return False

    # On the corner
        if (x < 6 and y < 6) or (x > 10 and y < 6) or \
        (x < 6 and y > 10) or (x > 10 and y > 10):
            return False

    # In the middle 
        if (x, y) in center_blocks:
            return False
        return True

    #Return to True if place successful, or show false. 
    def place_piece(self, x: int, y: int, piece: Piece) -> bool:
        if self.grid[y][x] is None:
            self.grid[y][x] = piece
            return True
        return False

    #Bool Function to determine if a piece can be attacked.
    def can_fight(self, from_pos, to_pos):

        #Define the source piece and the piece be attacked
        from_cell = self.grid[from_pos[0]][from_pos[1]]
        to_cell = self.grid[to_pos[0]][to_pos[1]]

        # Can't be attacked if it's in the camp
        if to_cell.terrain == TerrainType.CAMP:
            return False

        # If either the source or destination cell has no piece, the operation is invalid
        if from_cell.piece is None or to_cell.piece is None:
            return False

        # If both pieces belong to the same alliance (i.e., same team), the operation is invalid        
        if self.alliance_map.get(from_cell.piece.owner) == self.alliance_map.get(to_cell.piece.owner):
            return False

        # If both pieces belong to the same side
        if from_cell.piece.side == to_cell.piece.side:
            return False
        return True

    #Determine if one piece can move from (x1,y1) to (x2,y2)
    def can_move(self, x1, y1, x2, y2):
        piece = self.get_piece(x1, y1)

        # If there's no piece at the source or the piece is immobile, return False
        if piece is None or not piece.movable:
            return False

         # Cannot move to the same cell
        if (x1, y1) == (x2, y2):
            return False
        
        # If connected by a road, the move is valid (only one step allowed)
        if is_connected_by(x1, y1, x2, y2, LineType.ROAD):
            return True

        # If directly connected by railway, the move is valid
        if is_connected_by(x1, y1, x2, y2, LineType.RAIL):
            return True

        # Special case: Engineer can move freely along continuous railway paths
        if piece.name == "Engineer" and self.clear_path(x1, y1, x2, y2, LineType.RAIL):
            return True

        # Other pieces can move along straight unblocked railway paths (no turning)
        if self.clear_straight_rail_path(x1, y1, x2, y2):
           return True

        return False

    # Attempt to move a piece from (x1, y1) to (x2, y2).
    # Returns True if the move is successfully executed, False otherwise.
    def move_piece(self, x1: int, y1: int, x2: int, y2: int) -> bool:

        # Check if the move is legal based on movement rules
        if not self.can_move(x1, y1, x2, y2):
            print("Invalid move")
            return False

         # Ensure the target cell is within board bounds
        if not self.is_valid_cell(x2, y2):
            print("Move out of bounds")
            return False

        piece = self.grid[y1][x1]
        target = self.grid[y2][x2]

        # Sanity check: source cell must contain a piece
        if piece is None:
            print("No piece at source.")
            return False

        # Pieces inside HQ cannot be moved
        if self.is_hq(x1, y1):
            print("Cannot move a piece from HQ.")
            return False

         # Check if the piece is movable (e.g., not a landmine or HQ)
        if not piece.movable:
            print("Piece is not movable.")
            return False

        # If the target cell has an enemy piece, validate combat rules
        if target is not None:

            # Cannot attack a piece inside a camp
            if self.is_camp(x2, y2):
                print("Cannot attack a piece inside a camp.")
                return False

             # Cannot attack a piece with the same owner
            if piece.owner == target.owner:
                print("Cannot attack your own piece.")
                return False

            # Cannot attack a piece from the same alliance
            if self.alliance_map.get(piece.owner) == self.alliance_map.get(target.owner):
                print("Cannot attack allied piece.")
                return False

        # Execute the move or combat
        if target is None:
             # Simple move to an empty cell
            self.grid[y2][x2] = piece
            self.grid[y1][x1] = None
        else:
             # Bombs cause mutual destruction
            if piece.name == "Bomb" or target.name == "Bomb":
                piece.kill()
                target.kill()
                self.grid[y2][x2] = None
                self.grid[y1][x1] = None
                return True

            # Normal combat resolution
            if piece.can_defeat(target):
                target.kill()
                self.grid[y2][x2] = piece
            else:
                piece.kill()
                # Mutual destruction if equal rank, or specific special cases (e.g. landmine/engineer)
                if piece.rank == target.rank or piece.rank == 1 or target.rank == 1:
                    target.kill()
                    self.grid[y2][x2] = None

             # Clear the source cell in all combat cases
            self.grid[y1][x1] = None

        return True

    # Safely get the piece at (x, y). Returns None if the cell is invalid or empty.
    def get_piece(self, x: int, y: int) -> Piece | None:
        if not self.is_valid_cell(x, y):
            return None
        return self.grid[y][x]

    # Print the current state of the board to the console.
    def display(self):
        for y in range(17):
            for x in range(17):
                if not self.is_valid_cell(x, y):
                    print(" # ", end="") 
                    continue
                piece = self.grid[y][x]
                if piece is None:
                    print(" . ", end="")
                else:
                    print(piece.name[0], end=" ") 
            print()

    #Define Camp cells
    def set_camp_cells(self):
        for x, y in camp_positions:
            self.grid[x][y].terrain = TerrainType.CAMP

    #If the cell is camp
    def is_camp(self, x: int, y: int) -> bool:
        return (x, y) in camp_positions
    
    #Define Headquarter
    def set_hq_cells(self):
        for y, x in hq_positions:
            self.grid[y][x].terrain = TerrainType.HQ
    
    #If the cell is headquarter
    def is_hq(self, x: int, y: int) -> bool:
        return (y, x) in {
            (0, 7), (7, 0), (0, 9), (9, 0),
            (16, 7), (7, 16), (16, 9), (9, 16)
        }


    # Use BFS to check whether there is a clear path from (x1, y1) to (x2, y2)
    # along the given line_type (e.g., RAIL or ROAD), with no blocking pieces.

    # - The path can only go through empty cells.
    # - The destination (x2, y2) is allowed to be occupied.
    def clear_path(self, x1, y1, x2, y2, line_type):
        from collections import deque
        visited = {(x1, y1)}
        queue = deque([(x1, y1)])
        while queue:
            x, y = queue.popleft()
            if (x, y) == (x2, y2):
                return True
            for (nx, ny), t in get_connections(x, y):
                if t == line_type and (nx, ny) not in visited:
                            if (nx, ny) == (x2, y2):
                                return True
                            if self.get_piece(nx, ny) is None:
                                visited.add((nx, ny))
                                queue.append((nx, ny))
        return False

    # Check whether there is a clear straight railway path from (x1, y1) to (x2, y2).
    # This is for non-Engineer pieces: they can only move along straight railways 
    # or predefined special L-shaped rail paths.

    # Returns True if the path is valid and unobstructed, otherwise False.
    def clear_straight_rail_path(self, x1, y1, x2, y2):
         # 1. Check if both points are on the same predefined special L-shaped path
        for sp in special_paths:
            if (x1,y1) in sp and (x2,y2) in sp:
                i1, i2 = sp.index((x1,y1)), sp.index((x2,y2))
                if i1 > i2:
                    i1, i2 = i2, i1
                # Check that each pair of adjacent cells in the path segment is connected by railway
                for a, b in zip(sp[i1:i2], sp[i1+1:i2+1]):
                    ax, ay = a
                    bx, by = b
                    if not is_connected_by(ax, ay, bx, by, LineType.RAIL):
                        return False
                return True

         # 2. Pure horizontal or vertical railway path
        if x1 == x2 or y1 == y2:
            # Vertical move
            if x1 == x2:
                step = 1 if y2 > y1 else -1
                for y in range(y1 + step, y2, step):
                    if self.get_piece(x1, y) is not None:
                        return False
                    if not is_connected_by(x1, y-step, x1, y, LineType.RAIL):
                        return False
                return is_connected_by(x1, y2-step, x1, y2, LineType.RAIL)
            # Horizontal move
            step = 1 if x2 > x1 else -1
            for x in range(x1 + step, x2, step):
                if self.get_piece(x, y1) is not None:
                    return False
                if not is_connected_by(x-step, y1, x, y1, LineType.RAIL):
                    return False
            return is_connected_by(x2-step, y1, x2, y1, LineType.RAIL)

        return False
    
    # Check whether the given player (owner) can add another piece of the specified type.

    # Returns True if the current count of that piece type is below the allowed maximum
    # defined in MAX_COUNTS. Returns False if the limit has been reached.
    def can_add_piece(self, owner: str, piece_type: str) -> bool:
        count = 0
        for row in self.grid:
            for p in row:
                if p is not None and p.owner == owner and p.name == piece_type:
                    count += 1

        limit = MAX_COUNTS.get(piece_type, 0)
        return count < limit
    
    #显示每一步的隐藏棋子
    def get_all_hidden_positions(self, my_side) -> List[Tuple[int, int]]:
        """
        返回所有敌方尚未揭示的棋子的位置列表。
        my_side: 我方 owner（如 "Red"）
        """
        hidden: List[Tuple[int, int]] = []
        for y, row in enumerate(self.grid):
            for x, piece in enumerate(row):
                # 用 owner 而不是 color 判断阵营
                if piece is not None and piece.owner != my_side:
                    hidden.append((x, y))
        return hidden