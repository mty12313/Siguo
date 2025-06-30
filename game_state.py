# game_state.py

# 颜色顺序
COLORS = ['Red', 'Yellow', 'Green', 'Blue']

# 同盟映射：Red/Yellow 属于同盟1，Green/Blue 属于同盟2
ALLIANCE = {
    'Red': 1,
    'Yellow': 2,
    'Green': 1,
    'Blue': 2,
}

class GameState:
    def __init__(self):
        self.is_playing = False
        self.current_turn_index = 0
        self.game_over = False
        self.winning_alliance = None

    def start_game(self):
        self.is_playing = True
        self.current_turn_index = 0

    def stop_game(self):
        self.is_playing = False

    def current_player(self):
        return COLORS[self.current_turn_index]

    def next_turn(self):
        self.current_turn_index = (self.current_turn_index + 1) % len(COLORS)
    
    def is_movable(self, piece, col, row, board) -> bool:
        """
        判断一枚非地雷棋子当前是否可动，
        包含边界被己方地雷堵死和四方向走空/吃敌逻辑。
        """
        if not piece.alive or piece.name == 'Mine':
            return False

        # 边界＋己方地雷死棋
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

        # 四方向常规检查
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = row+dr, col+dc
            if 0 <= nr < board.rows and 0 <= nc < board.cols:
                t = board.get_piece(nc, nr)
                if t is None or t.owner != piece.owner:
                    return True

        return False

    def eliminate_side(self, color: str, game) -> None:
        """删除该方所有棋子，并如果正好是它的回合就跳到下一个."""
        for r in range(game.board.rows):
            for c in range(game.board.cols):
                p = game.board.get_piece(c, r)
                if p and p.owner == color:
                    game.board.grid[r][c] = None
        if COLORS[self.current_turn_index] == color:
            self.next_turn()

    def check_elimination(self, game) -> None:
        """
        自动检查：
          1) 若某方的 Flag 不在棋盘上则淘汰该方
          2) 若某方所有存活棋子都不可移动，则淘汰该方
          3) 检查胜利
          4) 更新所有棋子可动状态
        """
        # 1) Flag 淘汰
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

        # 2) 死棋（所有存活棋子不可动）淘汰
        for color in COLORS:
            has_live = False
            all_stuck = True
            for r in range(game.board.rows):
                for c in range(game.board.cols):
                    p = game.board.get_piece(c, r)
                    if p and p.owner == color and p.alive:
                        has_live = True
                        if p.movable:           # 只要有一颗可动就不淘汰
                            all_stuck = False
                            break
                if not all_stuck:
                    break
            if has_live and all_stuck:
                self.eliminate_side(color, game)

        # 3) 胜利检查
        self.check_victory(game)

        # 4) 更新可动状态
        self.update_all_movable(game.board)

    def check_victory(self, game) -> bool:
        """
        检查是否只剩一个同盟的棋子，若是则设置 game_over 并返回 True。
        """
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

    def get_victory_message(self) -> str:
        if self.game_over:
            winners = [c for c,a in ALLIANCE.items() if a == self.winning_alliance]
            return f"胜利！同盟 {winners} 获胜！"
        return ""
    
    def update_all_movable(self, board) -> None:
        """
        遍历棋盘上所有存活的棋子，基于边界+己方地雷和四方向可走/可吃敌逻辑，
        同步更新每个 piece.movable。
        """
        for r in range(board.rows):
            for c in range(board.cols):
                p = board.get_piece(c, r)
                if not p or not p.alive or p.name in ("Mine", "Flag"):
                    if p:
                        p.movable = False
                    continue

                # 边界+己方地雷专门判死
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

                # 四方向普通判可动：有空格或敌人即可
                movable = False
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < board.rows and 0 <= nc < board.cols:
                        t = board.get_piece(nc, nr)
                        if t is None or t.owner != p.owner:
                            movable = True
                            break

                p.movable = movable

# 单例全局状态
game_state = GameState()
