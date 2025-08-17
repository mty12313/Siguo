# game_state.py - Turn Management and Elimination Logic for Four Kingdoms Military Chess

# This module defines the GameState class, which tracks global game status,
# handles player turns, determines piece mobility, and automatically performs
# elimination and victory checks during gameplay.

ALLIANCE = {
    "Red": 1,
    "Green": 2,
}

# Color order for turn rotation
COLORS = ['Red', 'Green']

class TwoPlayer:
    #Initialize the game state.
    def __init__(self):
        self.is_playing = False
        self.current_turn_index = 0 # Index in COLORS list indicating which player's turn it is
        self.game_over = False
        self.winning_alliance = None # Alliance number (1 or 2) of the winning side, or None if not yet decided

    def start_game(self):
        self.is_playing = True
        self.current_turn_index = 0

    def stop_game(self):
        self.is_playing = False

    def current_player(self):
        return COLORS[self.current_turn_index]

    def next_turn(self):
        self.current_turn_index = (self.current_turn_index + 1) % len(COLORS)
    
    # Determine whether a piece (excluding Mines) can move on the board.

    # A piece is considered movable if:
    # 1. It is alive and not a Mine
    # 2. It is not blocked by allied Mines along all outward-facing edges
    # 3. It has at least one adjacent cell that is either:
    #     - Empty
    #     - Occupied by an enemy piece
    def is_movable(self, piece, col, row, board) -> bool:
        # Dead pieces or Mines can never move
        if not piece.alive or piece.name == 'Mine':
            return False

         # Check for edge + allied Mine blocking (deadlock on one side)
        if col == 0:
            n = board.get_piece(1, row)
            if n and n.owner == piece.owner and n.name == 'Mine':
                return False
        if col == board.cols - 1:
            n = board.get_piece(board.cols - 2, row)
            if n and n.owner == piece.owner and n.name == 'Mine':
                return False
        if row == 0:
            n = board.get_piece(col, 1)
            if n and n.owner == piece.owner and n.name == 'Mine':
                return False
        if row == board.rows - 1:
            n = board.get_piece(col, board.rows - 2)
            if n and n.owner == piece.owner and n.name == 'Mine':
                return False

       # Check adjacent directions (up, down, left, right)
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = row+dr, col+dc
            if 0 <= nr < board.rows and 0 <= nc < board.cols:
                t = board.get_piece(nc, nr)
                # Movable if neighbor is empty or an enemy
                if t is None or t.owner != piece.owner:
                    return True

        return False

    # Eliminate all pieces belonging to a specific side (color).
    # This function is typically called when a player loses their Flag or all their pieces become immobile.
    # It removes all pieces of the given color from the board and advances the turn if the eliminated side
    # was currently active.
    def eliminate_side(self, color: str, game) -> None:
        # Iterate over the entire board and remove all pieces belonging to the eliminated color
        for r in range(game.board.rows):
            for c in range(game.board.cols):
                p = game.board.get_piece(c, r)
                if p and p.owner == color:
                    game.board.grid[r][c] = None
        # If the eliminated side was about to play, skip their turn
        if COLORS[self.current_turn_index] == color:
            self.next_turn()

    # Automatically check for elimination and victory conditions.

    # This function performs a full board scan to determine if any side should be eliminated
    # based on two conditions:
    # 1. Their Flag is no longer on the board.
    # 2. All of their remaining pieces are immobile (i.e., cannot make a legal move).

    # After elimination checks, it also:
    # 3. Checks if only one alliance remains and sets the game-over flag if so.
    # 4. Updates the movable status of all pieces on the board.
    def check_elimination(self, game) -> None:
        # 1) Eliminate any side that has lost its Flag
        for color in COLORS:
            found_flag = False
            for r in range(game.board.rows):
                for c in range(game.board.cols):
                    p = game.board.get_piece(c, r)
                    if p and p.owner == color and p.name == 'Flag':
                        found_flag = True
                        break
                if found_flag:
                    break
            if not found_flag:
                self.eliminate_side(color, game)

        # 2) Eliminate any side whose remaining pieces are all immobile (stuck)
        for color in COLORS:
            has_live = False
            all_stuck = True
            for r in range(game.board.rows):
                for c in range(game.board.cols):
                    p = game.board.get_piece(c, r)
                    if p and p.owner == color and p.alive:
                        has_live = True
                        if p.movable: 
                            all_stuck = False
                            break
                if not all_stuck:
                    break
            if has_live and all_stuck:
                self.eliminate_side(color, game)

       # 3) Check for victory (only one alliance left on the board)
        self.check_victory(game)

       # 4) Update movable status for all remaining pieces
        self.update_all_movable(game.board)

    # Check if only one alliance remains on the board.

    # If all remaining alive pieces belong to the same alliance, the game ends and
    # that alliance is marked as the winner. Returns True if the game is over, else False.
    def check_victory(self, game) -> bool:
        alive_alliances = set()
        for row in game.board.grid:
            for piece in row:
                if piece and piece.owner in ALLIANCE:
                    alive_alliances.add(ALLIANCE[piece.owner])

        if len(alive_alliances) == 1:
            self.winning_alliance = next(iter(alive_alliances))
            self.game_over = True
            return True
        return False

    # Return a victory message string if the game has ended.
    def get_victory_message(self) -> str:
        if self.game_over:
            winners = [c for c,a in ALLIANCE.items() if a == self.winning_alliance]
            return f"Victory! {winners} WIn!"
        return ""
    
    # Update the 'movable' attribute of all alive pieces on the board.

    # This method scans all cells on the board and evaluates whether each piece
    # is currently movable based on:
    #   - Whether it's alive and not a Mine or Flag (which are never movable)
    #   - Whether it's blocked by allied Mines at the edge of the board
    #   - Whether there is at least one adjacent empty cell or enemy piece
    def update_all_movable(self, board) -> None:
        for r in range(board.rows):
            for c in range(board.cols):
                p = board.get_piece(c, r)
                if not p or not p.alive or p.name in ("Mine", "Flag"):
                    if p:
                        p.movable = False
                    continue

                # Check if the piece is blocked by allied Mines at board edges
                blocked = False
                if c == 0:
                    n = board.get_piece(1, r)
                    if n and n.owner == p.owner and n.name == "Mine":
                        blocked = True
                if c == board.cols - 1:
                    n = board.get_piece(board.cols - 2, r)
                    if n and n.owner == p.owner and n.name == "Mine":
                        blocked = True
                if r == 0:
                    n = board.get_piece(c, 1)
                    if n and n.owner == p.owner and n.name == "Mine":
                        blocked = True
                if r == board.rows - 1:
                    n = board.get_piece(c, board.rows - 2)
                    if n and n.owner == p.owner and n.name == "Mine":
                        blocked = True
                if blocked:
                    p.movable = False
                    continue

               # Check four directions for possible moves (empty or enemy-occupied)
                movable = False
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < board.rows and 0 <= nc < board.cols:
                        t = board.get_piece(nc, nr)
                        if t is None or t.owner != p.owner:
                            movable = True
                            break

                p.movable = movable

two_player_mode = TwoPlayer()
