from piece import Piece, MAX_COUNTS
from routes import is_connected_by, get_connections, LineType

BOARD_SIZE = 17 #standard board size

#盟友系统
ALLIANCE = {
    "Red": 1,
    "Green": 1,
    "Blue": 2,
    "Yellow": 2,
}


class ChessBoard:
    def __init__(self): #initial
        self.grid = []
        for i in range(17):
            row = []
            for j in range(17):
                row.append(None)
            self.grid.append(row)
        self.rows = len(self.grid)
        self.cols = len(self.grid[0])

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
        invalid_center_cells = {
            (6, 7), (6, 9),
            (7, 6), (7, 7), (7, 8), (7, 9), (7, 10),
            (8, 7), (8, 9),
            (9, 6), (9, 7), (9, 8), (9, 9), (9, 10),
            (10, 7), (10, 9)
        }
        if (x, y) in invalid_center_cells:
            return False
        return True

    #Return to True if place successful, or show false. 
    def place_piece(self, x: int, y: int, piece: Piece) -> bool:
        if self.grid[y][x] is None:
            self.grid[y][x] = piece
            return True
        return False

    def can_fight(self, from_pos, to_pos):
        from_cell = self.grid[from_pos[0]][from_pos[1]]
        to_cell = self.grid[to_pos[0]][to_pos[1]]

        # 如果目标格子在 camp，不可被攻击
        if to_cell.terrain == TerrainType.CAMP:
            return False

        if from_cell.piece is None or to_cell.piece is None:
            return False

        if ALLIANCE.get(from_cell.piece.owner) == ALLIANCE.get(to_cell.piece.owner):
            return False

        if from_cell.piece.side == to_cell.piece.side:
            return False
        return True

    def move_piece(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        # 1. 基本合法性检查
        if not self.can_move(x1, y1, x2, y2):
            print("Invalid move")
            return False

        if not self.is_valid_cell(x2, y2):
            print("Invalid target position.")
            return False

        piece = self.grid[y1][x1]
        target = self.grid[y2][x2]

        if piece is None:
            print("No piece at source.")
            return False

        if self.is_hq(x1, y1):
            print("Cannot move a piece from HQ.")
            return False

        if not piece.movable:
            print("Piece is not movable.")
            return False

        # 2. 如果目标格有棋子，先做额外的攻击合法性检查
        if target is not None:
            # 营地内的棋子不可攻击
            if self.is_camp(x2, y2):
                print("Cannot attack a piece inside a camp.")
                return False

            # 同主人（owner）不可攻击
            if piece.owner == target.owner:
                print("Cannot attack your own piece.")
                return False

            # 同联盟（红绿一队，蓝黄一队）不可攻击
            if ALLIANCE.get(piece.owner) == ALLIANCE.get(target.owner):
                print("Cannot attack allied piece.")
                return False

        # 3. 执行移动或战斗
        if target is None:
            # 普通走子
            self.grid[y2][x2] = piece
            self.grid[y1][x1] = None
        else:
            # 炸弹同归于尽
            if piece.name == "Bomb" or target.name == "Bomb":
                piece.kill()
                target.kill()
                self.grid[y2][x2] = None
                self.grid[y1][x1] = None
                return True

            # 其它吃子判定
            if piece.can_defeat(target):
                target.kill()
                self.grid[y2][x2] = piece
            else:
                piece.kill()
                # 若同排或有地雷／工兵特殊情况也同归于尽
                if piece.rank == target.rank or piece.rank == 1 or target.rank == 1:
                    target.kill()
                    self.grid[y2][x2] = None

            # 清空原位
            self.grid[y1][x1] = None

        return True

    def get_piece(self, x: int, y: int) -> Piece | None:
        if not self.is_valid_cell(x, y):
            return None
        return self.grid[y][x]

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

    #Define Camp
    def set_camp_cells(self):
        camp_positions = [
            (2, 7), (4, 7), (14, 7), (12, 7),
            (2, 9), (4, 9), (14, 9), (12, 9),
            (3, 8), (13, 8),
            (7, 2), (7, 4), (7, 12), (7, 14),
            (9, 2), (9, 4), (9, 12), (9, 14),
            (8, 3), (8, 13)
        ]
        for x, y in camp_positions:
            self.grid[x][y].terrain = TerrainType.CAMP

    def is_camp(self, x: int, y: int) -> bool:
        return (x, y) in {
            (2, 7), (4, 7), (14, 7), (12, 7),
            (2, 9), (4, 9), (14, 9), (12, 9),
            (3, 8), (13, 8),
            (7, 2), (7, 4), (7, 12), (7, 14),
            (9, 2), (9, 4), (9, 12), (9, 14),
            (8, 3), (8, 13)
        }
    
    def set_hq_cells(self):
        hq_positions = [
            (0, 7), (7, 0), (0, 9), (9, 0),
            (16, 7), (7, 16), (16, 9), (9, 16)
        ]   
        for y, x in hq_positions:
            self.grid[y][x].terrain = TerrainType.HQ
    
    def is_hq(self, x: int, y: int) -> bool:
        return (y, x) in {
            (0, 7), (7, 0), (0, 9), (9, 0),
            (16, 7), (7, 16), (16, 9), (9, 16)
        }

    def clear_path(self, x1, y1, x2, y2, line_type):
        """
        简单的 BFS 判断 x1,y1 到 x2,y2 在 line_type 上是否连通且无阻挡。
        """
        from collections import deque
        visited = {(x1, y1)}
        queue = deque([(x1, y1)])
        while queue:
            x, y = queue.popleft()
            if (x, y) == (x2, y2):
                return True
            for (nx, ny), t in get_connections(x, y):
                if t == line_type and (nx, ny) not in visited:
                            # 如果是终点，即便被占也算连通
                            if (nx, ny) == (x2, y2):
                                return True
                            # 否则只能扩展空格
                            if self.get_piece(nx, ny) is None:
                                visited.add((nx, ny))
                                queue.append((nx, ny))
        return False

    def can_move(self, x1, y1, x2, y2):
        piece = self.get_piece(x1, y1)
        if piece is None or not piece.movable:
            return False

        # 同一格不动
        if (x1, y1) == (x2, y2):
            return False
        
        if is_connected_by(x1, y1, x2, y2, LineType.ROAD):
            return True

        if is_connected_by(x1, y1, x2, y2, LineType.RAIL):
            return True
    # 工兵：只要铁路多段连通且中间无阻挡即可
        if piece.name == "Engineer" and self.clear_path(x1, y1, x2, y2, LineType.RAIL):
            return True
        if self.clear_straight_rail_path(x1, y1, x2, y2):
           return True
        return False

    def clear_straight_rail_path(self, x1, y1, x2, y2):
    # ── 0. 定义所有“特殊 L 型”路径──
        special_paths = [
            # 原来 (1,6)->(5,6)->(6,5)->(6,1)
            [(1,6),(2,6),(3,6),(4,6),(5,6),(6,5),(6,4),(6,3),(6,2),(6,1)],
            # 新增 (1,10)->(5,10)->(6,11)->(6,15)
            [(1,10),(2,10),(3,10),(4,10),(5,10),(6,11),(6,12),(6,13),(6,14),(6,15)],

            [(10,1),(10,2),(10,3),(10,4),(10,5),(11,6),(12,6),(13,6),(14,6),(15,6)],

            [(10,15),(10,14),(10,13),(10,12),(10,11),(11,10),(12,10),(13,10),(14,10),(15,10)],
        ]
        # 如果两个点都落在同一条 special_path 上，就当成连续铁路处理
        for sp in special_paths:
            if (x1,y1) in sp and (x2,y2) in sp:
                i1, i2 = sp.index((x1,y1)), sp.index((x2,y2))
                if i1 > i2:
                    i1, i2 = i2, i1
                # 检查 sp[i1]→...→sp[i2] 上每一对相邻格子是否有铁路
                for a, b in zip(sp[i1:i2], sp[i1+1:i2+1]):
                    ax, ay = a
                    bx, by = b
                    if not is_connected_by(ax, ay, bx, by, LineType.RAIL):
                        return False
                return True

        # ── 1. 原有的纯横／竖直铁路判断──
        if x1 == x2 or y1 == y2:
            # 竖直走
            if x1 == x2:
                step = 1 if y2 > y1 else -1
                for y in range(y1 + step, y2, step):
                    if self.get_piece(x1, y) is not None:
                        return False
                    if not is_connected_by(x1, y-step, x1, y, LineType.RAIL):
                        return False
                return is_connected_by(x1, y2-step, x1, y2, LineType.RAIL)
            # 水平走
            step = 1 if x2 > x1 else -1
            for x in range(x1 + step, x2, step):
                if self.get_piece(x, y1) is not None:
                    return False
                if not is_connected_by(x-step, y1, x, y1, LineType.RAIL):
                    return False
            return is_connected_by(x2-step, y1, x2, y1, LineType.RAIL)

        # ── 2. 其他情况──
        return False
    
    def can_add_piece(self, owner: str, piece_type: str) -> bool:
        count = 0
        # 直接遍历 grid，少写两行 rows/cols 属性
        for row in self.grid:
            for p in row:
                if p is not None and p.owner == owner and p.name == piece_type:
                    count += 1

        limit = MAX_COUNTS.get(piece_type, 0)
        return count < limit