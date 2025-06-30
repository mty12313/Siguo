import pygame
from chessboard import ChessBoard
from piece import Piece, PIECE_RANKS, MAX_COUNTS
import random

# 每个格子的像素大小，用于计算弹窗位置
GRID_SIZE = 40

#自动判读棋子初始区域
COLOR_ZONES = {
    "Red":    (6, 11, 10, 16),
    "Green":  (6, 0, 10, 5),
    "Blue":   (0, 6, 5, 10),
    "Yellow": (11, 6, 16, 10),
}

OWNER_TO_COLOR = {
    "Red":    (255, 0, 0),
    "Green":  (0, 200, 0),
    "Blue":   (0, 100, 255),
    "Yellow": (200, 200, 0),
}

#地雷允许区域
ALLOWED_MINE_CELLS = {
    (row, col)
    for row in range(17)
    for col in range(17)
    if row in (0, 1, 15, 16) or col in (0, 1, 15, 16)
}

#炸弹非法区域
FORBIDDEN_BOMB_CELLS = {
    (row, col)
    for row in range(17)
    for col in range(17)
    if row in (5, 11) or col in (5, 11)
}

#军棋只能防止这些区域
ALLOWED_FLAG_CELLS = {
    (0, 7), (7, 0), (0, 9), (9, 0),
    (16, 7), (7, 16), (16, 9), (9, 16)
}

#行营位置
CAMPS_CELLS = {
    (2, 7), (4, 7), (14, 7), (12, 7),
    (2, 9), (4, 9), (14, 9), (12, 9),
    (3, 8), (13, 8),
    (7, 2), (7, 4), (7, 12), (7, 14),
    (9, 2), (9, 4), (9, 12), (9, 14),
    (8, 3), (8, 13)
}

#判断区域
def get_zone_color(row: int, col: int) -> str | None:
    for color, (x1, y1, x2, y2) in COLOR_ZONES.items():
        if x1 <= col <= x2 and y1 <= row <= y2:
            return color
    return None
    

class Game:
    """Core game logic (no GUI). Handles selection, movement, piece state,
    and renders a right-click info overlay within pygame."""

    GRID_ROWS = 17
    GRID_COLS = 17

    def __init__(self):
        # 游戏状态
        self.board = ChessBoard()
        self.selected: tuple[int, int] | None = None  # (row, col)

        # 弹窗菜单数据和位置
        self.info_items: list[dict] | None = None
        self.info_pos: tuple[int, int] | None = None  # 像素坐标 (x, y)

        self.popup_board_pos: tuple[int, int] | None = None  # 记录右键点的棋盘格子(row, col)
        self.popup_owner: str | None = None


        OWNER_TO_COLOR = {
            "Red": (255, 0, 0),
            "Green": (0, 200, 0),
            "Blue": (0, 100, 255),
            "Yellow": (200, 200, 0),
        }

        # 定义3x4菜单项（颜色和名称）
        self.POPUP_ITEMS = [
            {"color": "Red", "name": "司"},
            {"color": "Red", "name": "军"},
            {"color": "Red", "name": "师"},
            {"color": "Red", "name": "旅"},
            {"color": "Red", "name": "团"},
            {"color": "Red", "name": "营"},
            {"color": "Red", "name": "连"},
            {"color": "Red", "name": "排"},
            {"color": "Red", "name": "兵"},
            {"color": "Red", "name": "炸"},
            {"color": "Red", "name": "雷"},
            {"color": "Red", "name": "旗"},
        ]

        self.POPUP_ROWS = 3
        self.POPUP_COLS = 4
        self.POPUP_CELL_W = 50
        self.POPUP_CELL_H = 50

        # 初始化示例棋子，可替换
        self._init_default_pieces()

        def add_piece(self, row, col, owner, piece_type):
            # —— 先检查格子是否为空 —— 
            if self.board.get_piece(row, col) is not None:
                return  # 已有棋子，就不添加

            # —— 统计该 owner 的该类型棋子已经放了多少 —— 
            type_count = 0
            for r in range(self.board.rows):
                for c in range(self.board.cols):
                    p = self.board.get_piece(r, c)
                    if p is not None and p.owner == owner and p.type == piece_type:
                        type_count += 1

            # —— 拿 MAX_COUNTS 限制对比 —— 
            limit = MAX_COUNTS.get(piece_type, 0)
            if type_count >= limit:
                # 这里用你习惯的提示方式
                self.show_message(
                    f"{owner} 阵营的 {piece_type} 最多只能放 {limit} 颗，当前已有 {type_count} 颗。"
                )
                return

            # —— 通过检查，正式放置 —— 
            self.board.place_piece(row, col, owner, piece_type)


    # ---------------------- 用户操作 ----------------------
    def on_left_click(self, row: int, col: int) -> bool:
        """
        处理左键点击：选中或移动棋子。
        返回 True 表示这次确实走了一步，False 表示只是选中或失败。
        """
        if self.selected:
            # 再次点击同一格取消
            if self.selected == (row, col):
                self.selected = None
                return False

            # 尝试走子，move_piece 返回 True/False
            moved = self.board.move_piece(
                self.selected[1], self.selected[0],
                col, row
            )
            if moved:
                self.selected = None
                self.clear_overlay()
                return True
            else:
                return False

        else:
            # 还没选中：尝试选中一个棋子
            piece = self.board.get_piece(col, row)
            if piece and piece.alive:
                self.selected = (row, col)
            return False

    def on_right_click(self, row: int, col: int) -> None:
        # 允许弹菜单的位置集合（坐标已调换为 (row, col)）
        allowed = {
            (2, 7), (4, 7), (14, 7), (12, 7),
            (2, 9), (4, 9), (14, 9), (12, 9),
            (3, 8), (13, 8),
            (7, 2), (7, 4), (7, 12), (7, 14),
            (9, 2), (9, 4), (9, 12), (9, 14),
            (8, 3), (8, 13)
        }
        # 非法位置不弹菜单
        if (row, col) in allowed:
            return

        # 当前玩家颜色，比如 "Red"/"Blue"
        owner = get_zone_color(row, col)
        if not owner:
            # 不在任何指定区域内，不弹出菜单
            return

        # 对原始的 POPUP_ITEMS 进行过滤：
        # 只保留 board.can_add_piece(owner, piece_type) == True 的项
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

        filtered_items = []
        for item in self.POPUP_ITEMS:
            short = item["name"]
            piece_type = name_map.get(short)
            if not piece_type:
                continue
            # 地雷限制：只能放边缘
            if piece_type == "Mine" and (row, col) not in ALLOWED_MINE_CELLS:
                continue

            # 炸弹限制：不能放在5行/11行/5列/11列
            if piece_type == "Bomb" and (row, col) in FORBIDDEN_BOMB_CELLS:
                continue

            # 军旗限制：只能放在8个指定格子
            if piece_type == "Flag" and (row, col) not in ALLOWED_FLAG_CELLS:
                continue

            if self.board.can_add_piece(owner, piece_type):
                # 用区域 owner 的颜色为弹窗小圆着色
                filtered_items.append({
                    "name": item["name"],
                    "color": OWNER_TO_COLOR[owner]
                })

        # 如果所有类型都达上限，则提示并返回
        if not filtered_items:
            self.show_popup(f"提示：{owner} 颜色的所有棋子都已达到最大允许数量，无法再添加。")
            return

        # 只弹出允许添加的类型
        self.info_items = filtered_items
        # 记录画面上鼠标的位置（像素坐标）
        self.info_pos = (col * GRID_SIZE, row * GRID_SIZE)
        # 记录右键点击的棋盘格坐标
        self.popup_board_pos = (row, col)

        owner = get_zone_color(row, col)
        if not owner:
            return
        self.popup_owner = owner
    
    def show_popup(self, message: str):
        # 临时处理：打印到控制台
        print("[弹窗提示]", message)

        # TODO: 如果你使用 Pygame 画文字，可在这里实现绘制逻辑

    def on_popup_click(self, mouse_x: int, mouse_y: int) -> None:
        """判断鼠标是否点击在菜单某个圆上，点击后放置棋子"""
        if not self.info_items or not self.info_pos or not self.popup_board_pos:
            return

        # 中文 → 英文棋子名 映射表
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

        x0, y0 = self.info_pos
        for i in range(self.POPUP_ROWS):
            for j in range(self.POPUP_COLS):
                idx = i * self.POPUP_COLS + j
                if idx >= len(self.info_items):
                    break

                cx = x0 + j * self.POPUP_CELL_W
                cy = y0 + i * self.POPUP_CELL_H
                center = (cx + self.POPUP_CELL_W // 2, cy + self.POPUP_CELL_H // 2)
                radius = min(self.POPUP_CELL_W, self.POPUP_CELL_H) // 3

                # 检查点击是否在圆内
                dx, dy = mouse_x - center[0], mouse_y - center[1]
                if dx * dx + dy * dy <= radius * radius:
                    short_name = self.info_items[idx]["name"]
                    rank_key = name_map.get(short_name)
                    if rank_key:
                        from piece import PIECE_RANKS  # 保证此行可用，已全局导入也可以不写
                        owner = self.popup_owner
                        piece = Piece(rank_key, PIECE_RANKS[rank_key], owner)
                        row, col = self.popup_board_pos
                        piece.alive = True
                        piece.revealed = True
                        self.board.grid[row][col] = piece  # 直接覆盖
                        self.board.place_piece(col, row, piece)
                        self.clear_overlay()
                    return


    def clear_overlay(self) -> None:
        """清除弹窗"""
        self.info_items = None
        self.info_pos = None

    # ---------------------- 渲染方法 ----------------------
    def draw_overlay(self, screen: pygame.Surface) -> None:
        """在 pygame 窗口上绘制弹窗菜单(3x4 带圆形的格子）"""
        if not self.info_items or not self.info_pos:
            return

        
        x0, y0 = self.info_pos

        # 绘制半透明背景
        w = self.POPUP_COLS * self.POPUP_CELL_W
        h = self.POPUP_ROWS * self.POPUP_CELL_H
        popup_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        popup_surf.fill((255, 255, 200, 220))
        screen.blit(popup_surf, (x0, y0))
        font = pygame.font.Font("/System/Library/Fonts/STHeiti Medium.ttc", 18)

        # 逐个格子绘制
        for i in range(self.POPUP_ROWS):
            for j in range(self.POPUP_COLS):
                idx = i * self.POPUP_COLS + j
                if idx >= len(self.info_items):
                    break
                item = self.info_items[idx]
                cx = x0 + j * self.POPUP_CELL_W
                cy = y0 + i * self.POPUP_CELL_H
                # 单元格边框
                rect = pygame.Rect(cx, cy, self.POPUP_CELL_W, self.POPUP_CELL_H)
                pygame.draw.rect(screen, (0, 0, 0), rect, 1)
                # 圆形
                center = (cx + self.POPUP_CELL_W // 2, cy + self.POPUP_CELL_H // 2)
                radius = min(self.POPUP_CELL_W, self.POPUP_CELL_H) // 3
                pygame.draw.circle(screen, item["color"], center, radius)
                # 名称文字
                txt = font.render(item["name"], True, (0, 0, 0))
                txt_rect = txt.get_rect(center=center)
                screen.blit(txt, txt_rect)

    # ------------------- 其他接口省略 -------------------
    def delete_selected_piece(self) -> None:
        if self.selected:
            row, col = self.selected
            # —— 直接把格子设为 None —— 
            self.board.grid[row][col] = None
            self.selected = None

    def get_piece(self, col: int, row: int):
        return self.board.get_piece(col, row)

    def is_camp(self, col: int, row: int) -> bool:
        return self.board.is_camp(col, row)

    def is_hq(self, col: int, row: int) -> bool:
        return self.board.is_hq(col, row)

    def _init_default_pieces(self):
        # 初始化默认棋子：已移除
        pass

    def generate_random_setup(self):
        self.board.grid = [[None] * self.GRID_COLS for _ in range(self.GRID_ROWS)]
        self.clear_overlay()

        # 按颜色区依次布子
        for owner, (x1, y1, x2, y2) in COLOR_ZONES.items():
            # 1. 收集该区所有合法空格
            free_cells = [
                (r, c)
                for r in range(y1, y2+1)
                for c in range(x1, x2+1)
                if self.board.is_valid_cell(c, r)
                and (r, c) not in CAMPS_CELLS
            ]
            random.shuffle(free_cells)

            # 2. 分三步放“Flag → Mine → Bomb”
            for piece_type in ("Flag", "Mine", "Bomb"):
                need = MAX_COUNTS[piece_type]
                # 筛出符合该类型放置规则的候选格
                if piece_type == "Flag":
                    candidates = [cell for cell in free_cells if cell in ALLOWED_FLAG_CELLS]
                elif piece_type == "Mine":
                    candidates = [cell for cell in free_cells if cell in ALLOWED_MINE_CELLS]
                else:  # Bomb
                    candidates = [cell for cell in free_cells if cell not in FORBIDDEN_BOMB_CELLS]

                if len(candidates) < need:
                    raise RuntimeError(f"{owner} 阵营的 {piece_type} 放置失败：可用格子不足")

                picks = random.sample(candidates, need)
                for (r, c) in picks:
                    p = Piece(piece_type, PIECE_RANKS[piece_type], owner)
                    p.alive = True
                    p.revealed = True
                    self.board.place_piece(c, r, p)
                    free_cells.remove((r, c))

            # 3. 再放其他普通棋子
            for piece_type, need in MAX_COUNTS.items():
                if piece_type in ("Flag", "Mine", "Bomb"):
                    continue
                if len(free_cells) < need:
                    raise RuntimeError(f"{owner} 阵营的 {piece_type} 放置失败：可用格子不足")

                picks = random.sample(free_cells, need)
                for (r, c) in picks:
                    p = Piece(piece_type, PIECE_RANKS[piece_type], owner)
                    p.alive = True
                    p.revealed = True
                    self.board.place_piece(c, r, p)
                    free_cells.remove((r, c))