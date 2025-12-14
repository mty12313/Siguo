# game.py - Pre-Battle Setup and In-Game Interaction Logic for Four Kingdoms Military Chess

# This module defines the Game class, which handles all piece placement,
# initialization, and player interaction before and during the game.

import pygame
from chessboard import ChessBoard
from piece import Piece
from constants import (
    PIECE_RANKS,
    MAX_COUNTS,
    camp_positions,
    COLOR_ZONES,
    OWNER_TO_COLOR,
    ALLOWED_MINE_CELLS,
    FORBIDDEN_BOMB_CELLS,
    ALLOWED_FLAG_CELLS,
)
import random

# Pixel size of each grid cell, used for GUI placement and popup alignment
GRID_SIZE = 40

# Determine which color zone (Red/Green/Blue/Yellow) a grid cell belongs to
# Used to assign ownership when placing pieces
def get_zone_color(row: int, col: int) -> str | None:
    for color, (x1, y1, x2, y2) in COLOR_ZONES.items():
        if x1 <= col <= x2 and y1 <= row <= y2:
            return color
    return None
    

class Game:
    GRID_ROWS = 17
    GRID_COLS = 17

    def __init__(self):
        self.board = ChessBoard()
        self.selected: tuple[int, int] | None = None  # (row, col)
        self.info_items: list[dict] | None = None
        self.info_pos: tuple[int, int] | None = None

        self.popup_board_pos: tuple[int, int] | None = None
        self.popup_owner: str | None = None


        OWNER_TO_COLOR = {
            "Red": (255, 0, 0),
            "Green": (0, 200, 0),
            "Blue": (0, 100, 255),
            "Yellow": (200, 200, 0),
        }

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

        self._init_default_pieces()

        def add_piece(self, row, col, owner, piece_type):
            if self.board.get_piece(row, col) is not None:
                return 
            type_count = 0
            for r in range(self.board.rows):
                for c in range(self.board.cols):
                    p = self.board.get_piece(r, c)
                    if p is not None and p.owner == owner and p.type == piece_type:
                        type_count += 1

            limit = MAX_COUNTS.get(piece_type, 0)
            if type_count >= limit:
                self.show_message(
                    f"{owner} 阵营的 {piece_type} 最多只能放 {limit} 颗，当前已有 {type_count} 颗。"
                )
                return

            self.board.place_piece(row, col, owner, piece_type)


    def on_left_click(self, row: int, col: int) -> bool:
        if self.selected:
            if self.selected == (row, col):
                self.selected = None
                return False

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
            piece = self.board.get_piece(col, row)
            if piece and piece.alive:
                self.selected = (row, col)
            return False

    def on_right_click(self, row: int, col: int) -> None:
        if (row, col) in camp_positions:
            return

        owner = get_zone_color(row, col)
        if not owner:
            return

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
            if piece_type == "Mine" and (row, col) not in ALLOWED_MINE_CELLS:
                continue

            if piece_type == "Bomb" and (row, col) in FORBIDDEN_BOMB_CELLS:
                continue

            if piece_type == "Flag" and (row, col) not in ALLOWED_FLAG_CELLS:
                continue

            if self.board.can_add_piece(owner, piece_type):
                filtered_items.append({
                    "name": item["name"],
                    "color": OWNER_TO_COLOR[owner]
                })

        if not filtered_items:
            self.show_popup(f"提示：{owner} 颜色的所有棋子都已达到最大允许数量，无法再添加。")
            return

        self.info_items = filtered_items
        self.info_pos = (col * GRID_SIZE, row * GRID_SIZE)
        self.popup_board_pos = (row, col)

        owner = get_zone_color(row, col)
        if not owner:
            return
        self.popup_owner = owner
    
    def show_popup(self, message: str):
        print("[弹窗提示]", message)

    def on_popup_click(self, mouse_x: int, mouse_y: int) -> None:
        if not self.info_items or not self.info_pos or not self.popup_board_pos:
            return

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

                dx, dy = mouse_x - center[0], mouse_y - center[1]
                if dx * dx + dy * dy <= radius * radius:
                    short_name = self.info_items[idx]["name"]
                    rank_key = name_map.get(short_name)
                    if rank_key:
                        from piece import PIECE_RANKS
                        owner = self.popup_owner
                        piece = Piece(rank_key, PIECE_RANKS[rank_key], owner)
                        row, col = self.popup_board_pos
                        piece.alive = True
                        piece.revealed = True
                        self.board.grid[row][col] = piece
                        self.board.place_piece(col, row, piece)
                        self.clear_overlay()
                    return


    def clear_overlay(self) -> None:
        """清除弹窗"""
        self.info_items = None
        self.info_pos = None

    def draw_overlay(self, screen: pygame.Surface) -> None:
        """在 pygame 窗口上绘制弹窗菜单(3x4 带圆形的格子）"""
        if not self.info_items or not self.info_pos:
            return

        
        x0, y0 = self.info_pos

        w = self.POPUP_COLS * self.POPUP_CELL_W
        h = self.POPUP_ROWS * self.POPUP_CELL_H
        popup_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        popup_surf.fill((255, 255, 200, 220))
        screen.blit(popup_surf, (x0, y0))
        font = pygame.font.Font("/System/Library/Fonts/STHeiti Medium.ttc", 18)

        for i in range(self.POPUP_ROWS):
            for j in range(self.POPUP_COLS):
                idx = i * self.POPUP_COLS + j
                if idx >= len(self.info_items):
                    break
                item = self.info_items[idx]
                cx = x0 + j * self.POPUP_CELL_W
                cy = y0 + i * self.POPUP_CELL_H
                rect = pygame.Rect(cx, cy, self.POPUP_CELL_W, self.POPUP_CELL_H)
                pygame.draw.rect(screen, (0, 0, 0), rect, 1)

                center = (cx + self.POPUP_CELL_W // 2, cy + self.POPUP_CELL_H // 2)
                radius = min(self.POPUP_CELL_W, self.POPUP_CELL_H) // 3
                pygame.draw.circle(screen, item["color"], center, radius)

                txt = font.render(item["name"], True, (0, 0, 0))
                txt_rect = txt.get_rect(center=center)
                screen.blit(txt, txt_rect)

    def delete_selected_piece(self) -> None:
        if self.selected:
            row, col = self.selected
            self.board.grid[row][col] = None
            self.selected = None

    def get_piece(self, col: int, row: int):
        return self.board.get_piece(col, row)

    def is_camp(self, col: int, row: int) -> bool:
        return self.board.is_camp(col, row)

    def is_hq(self, col: int, row: int) -> bool:
        return self.board.is_hq(col, row)

    def _init_default_pieces(self):
        pass

    def generate_random_setup(self):
        self.board.grid = [[None] * self.GRID_COLS for _ in range(self.GRID_ROWS)]
        self.clear_overlay()

        for owner, (x1, y1, x2, y2) in COLOR_ZONES.items():
            free_cells = [
                (r, c)
                for r in range(y1, y2+1)
                for c in range(x1, x2+1)
                if self.board.is_valid_cell(c, r)
                and (r, c) not in camp_positions
            ]
            random.shuffle(free_cells)

            for piece_type in ("Flag", "Mine", "Bomb"):
                need = MAX_COUNTS[piece_type]
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
    
    def generate_random_setup_red_green(self):
        self.board.grid = [[None] * self.GRID_COLS for _ in range(self.GRID_ROWS)]
        self.clear_overlay()

        for owner, zone in COLOR_ZONES.items():
            if owner not in ("Red", "Green"):
                continue
            x1, y1, x2, y2 = zone

            free_cells = [
                (r, c)
                for r in range(y1, y2 + 1)
                for c in range(x1, x2 + 1)
                if self.board.is_valid_cell(c, r)
                   and (r, c) not in camp_positions
            ]
            random.shuffle(free_cells)

            for piece_type in ("Flag", "Mine", "Bomb"):
                need = MAX_COUNTS[piece_type]
                if piece_type == "Flag":
                    candidates = [cell for cell in free_cells if cell in ALLOWED_FLAG_CELLS]
                elif piece_type == "Mine":
                    candidates = [cell for cell in free_cells if cell in ALLOWED_MINE_CELLS]
                else:
                    candidates = [cell for cell in free_cells if cell not in FORBIDDEN_BOMB_CELLS]

                picks = random.sample(candidates, need)
                for r, c in picks:
                    p = Piece(piece_type, PIECE_RANKS[piece_type], owner)
                    p.alive = True; p.revealed = True
                    self.board.place_piece(c, r, p)
                    free_cells.remove((r, c))

            for piece_type, need in MAX_COUNTS.items():
                if piece_type in ("Flag", "Mine", "Bomb"):
                    continue
                picks = random.sample(free_cells, need)
                for r, c in picks:
                    p = Piece(piece_type, PIECE_RANKS[piece_type], owner)
                    p.alive = True; p.revealed = True
                    self.board.place_piece(c, r, p)
                    free_cells.remove((r, c))

        self.current_turn_index = 0
        self.edit_mode = False