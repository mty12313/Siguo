import pygame
import sys
from game import Game
from game_state import game_state
from two_player_mode import two_player_mode


# ----------------------- visual constants ---------------------------
PADDING_CELLS = 2
GRID_SIZE = 40
BOARD_ROWS = 17
BOARD_COLS = 17
WIDTH = GRID_SIZE * (BOARD_COLS + 2 * PADDING_CELLS)
HEIGHT = GRID_SIZE * (BOARD_ROWS + 2 * PADDING_CELLS)
FPS = 60


WHITE = (255, 255, 255)
GRAY = (220, 220, 220)
BLUE = (50, 50, 255)
BLACK = (0, 0, 0)

OWNER_TO_COLOR = {
    "Red": (255, 0, 0),
    "Green": (0, 200, 0),
    "Blue": (0, 100, 255),
    "Yellow": (200, 200, 0),
}

DISPLAY_NAMES = {
    "General": "司", "CorpsCommander": "军", "DivisionCommander": "师",
    "Brigadier": "旅", "RegimentLeader": "团", "BattalionLeader": "营",
    "CompanyLeader": "连", "PlatoonLeader": "排", "Engineer": "兵",
    "Bomb": "炸", "Mine": "雷", "Flag": "旗",
}

# ----------------------- helper -------------------------------------

def _is_obstacle_cell(row: int, col: int) -> bool:
    """Return True for黑色障碍格子 (不能走 / 不可选)."""
    if (row < 6 and col < 6) or (row < 6 and col >= 11) or (row >= 11 and col < 6) or (row >= 11 and col >= 11):
        return True
    center_blocks = {
        (6, 7), (6, 9),
        (7, 6), (7, 7), (7, 8), (7, 9), (7, 10),
        (8, 7), (8, 9),
        (9, 6), (9, 7), (9, 8), (9, 9), (9, 10),
        (10, 7), (10, 9),
    }
    return (row, col) in center_blocks

# ----------------------- main loop ----------------------------------

def main() -> None:
    pygame.init()
    pygame.font.init()
    font = pygame.font.Font("/System/Library/Fonts/STHeiti Medium.ttc", 18)

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("四国军棋 - 可视化棋盘")
    clock = pygame.time.Clock()

    #功能按钮
    BUTTONS = [
       {"label": "清空",     "rect": pygame.Rect(20,  20, 60, 30)},
        {"label": "保存",     "rect": pygame.Rect(90,  20, 60, 30)},
        {"label": "撤销",     "rect": pygame.Rect(160, 20, 60, 30)},
        {"label": "四方随机",  "rect": pygame.Rect(230, 20, 60, 30)},  # 原“随机”
        {"label": "红绿随机",  "rect": pygame.Rect(300, 20, 60, 30)},  # 新增按钮
        {"label": "开始",     "rect": pygame.Rect(370, 20, 60, 30)},
        {"label": "红绿开始",    "rect": pygame.Rect(440, 20, 60, 30)},
    ]
    game = Game()  # core logic instance
    state_manager = game_state

    running = True
    while running:
        clock.tick(FPS)

        # --------------------- events ------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # ========== 按 ESC 键关闭弹窗 ==========
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if game.info_items:
                    game.clear_overlay()

            # --------------- 先处理左键点击弹窗 ---------------
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                
                #button的作用
                for button in BUTTONS:
                    if not button["rect"].collidepoint(mx, my):
                        continue

                    if button["label"] == "四方随机":
                        game.generate_random_setup()
                        game.clear_overlay()

                    elif button["label"] == "红绿随机":
                        # 只为红方和绿方生成随机阵容
                        game.generate_random_setup_red_green()
                        game.clear_overlay()

                    elif button["label"] == "开始":
                        state_manager = game_state
                        game.board.set_alliance_map({  # 四方四块都互为敌人的形式
                            "Red":   1,
                            "Green": 1,
                            "Blue":  2,
                            "Yellow":2,
                        })
                        state_manager.start_game()
                        print("游戏开始，当前轮到：", state_manager.current_player())
                        # 隐藏所有非红方正面
                        for r in range(BOARD_ROWS):
                            for c in range(BOARD_COLS):
                                p = game.get_piece(c, r)
                                if p and p.owner != 'Red':
                                    p.revealed = False
                    elif button["label"] == "清空":
                        game.board.grid = [[None]*BOARD_COLS for _ in range(BOARD_ROWS)]
                        game.clear_overlay()

                    elif button["label"] == "红绿开始":
                        # 初始化红绿双人模式并直接进入对战
                        state_manager = two_player_mode
                        game.belief_sampler.initialize(game.board)
                        game.board.set_alliance_map({
                            "Red":   1,
                            "Green": 2,
                        })
                        state_manager.start_game()
                        print("红绿模式启动，当前轮到：", state_manager.current_player())
                        # 隐藏所有非红方正面
                        for r in range(BOARD_ROWS):
                            for c in range(BOARD_COLS):
                                p = game.get_piece(c, r)
                                if p:
                                    p.revealed = False

                    # …… 你如果还有“保存”“退出”等等，就在这里继续elif

                    break

                # 如果弹窗正在显示，就只处理弹窗点击，并跳过后续的格子点击
                if game.info_items:
                    game.on_popup_click(mx, my)
                    continue

                # 否则转换成格子坐标，处理普通左键选中/移动
                col = mx // GRID_SIZE - PADDING_CELLS
                row = my // GRID_SIZE - PADDING_CELLS
                if state_manager.is_playing and game.selected is None:
                    piece = game.get_piece(col, row)
                    if piece and piece.owner != state_manager.current_player():
                        print("不是你的回合！")
                        continue
                if not _is_obstacle_cell(row, col):
                    moved = game.on_left_click(row, col)   # 现在它会返回 True/False
                    if moved and state_manager.is_playing:
                        mover = state_manager.current_player()
                        hidden = game.board.get_all_hidden_positions(my_side=mover)

                        # 1. 打印隐藏位置
                        print(f"\n>>> {mover} 走完后的隐藏敌方棋子：")
                        for x, y in hidden:
                            p = game.get_piece(x, y)
                            print(f"  位置 {(x, y)} {p.uid} owner={p.owner} revealed={p.revealed}")

                        # 2. 打印 belief sampler 中的 legal 分布
                        print(f"\n>>> {mover} 隐藏位置上的合法棋子类型分布（legal distribution）：")
                        bs = game.belief_sampler  # 你的 belief sampler 对象
                        for pos in hidden:
                            dist = bs.beliefs[pos]  # {piece_type: probability}
                            # 按概率从高到低排序输出
                            sorted_dist = sorted(dist.items(), key=lambda kv: kv[1], reverse=True)
                            probs_str = ", ".join(f"{ptype}: {prob:.2f}" for ptype, prob in sorted_dist)
                            print(f"  位置 {pos} -> {probs_str}")

                            
                            state_manager.next_turn()             # 真正走子后切轮次
            # --------------- 再处理右键弹窗 ---------------
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                x, y = event.pos
                col = x // GRID_SIZE - PADDING_CELLS
                row = y // GRID_SIZE - PADDING_CELLS
                if _is_obstacle_cell(row, col):
                    continue

                if not state_manager.is_playing:
                    # —— 编辑模式：原有弹出菜单 —— 
                    game.on_right_click(row, col)
                else:
                    # —— 对战模式：切换翻面 —— 
                    piece = game.get_piece(col, row)
                    if piece:
                        piece.revealed = not piece.revealed

            # --------------- 删除键 ---------------
            elif event.type == pygame.KEYDOWN and game.selected:
                if event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                    print("Delete pressed")
                    game.delete_selected_piece()

        
        # --------------------- drawing -----------------------------
        screen.fill(BLACK)

        #功能按钮
        font = pygame.font.Font("/System/Library/Fonts/STHeiti Medium.ttc", 18)
        for button in BUTTONS:
            pygame.draw.rect(screen, (200, 200, 200), button["rect"])       # 背景
            pygame.draw.rect(screen, (0, 0, 0), button["rect"], 2)          # 边框
            label = font.render(button["label"], True, (0, 0, 0))           # 文字
            label_rect = label.get_rect(center=button["rect"].center)
            screen.blit(label, label_rect)

        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                rect = pygame.Rect(
                    (col + PADDING_CELLS) * GRID_SIZE,
                    (row + PADDING_CELLS) * GRID_SIZE,
                    GRID_SIZE, GRID_SIZE
                )
                if _is_obstacle_cell(row, col):
                    pygame.draw.rect(screen, BLACK, rect)
                else:
                    pygame.draw.rect(screen, WHITE, rect)
                    pygame.draw.rect(screen, GRAY, rect, 1)

                # camps / HQ colouring
                if game.is_camp(col, row):
                    pygame.draw.rect(screen, (180, 180, 180), rect)
                elif game.is_hq(col, row):
                    pygame.draw.rect(screen, (100, 100, 100), rect)

                piece = game.get_piece(col, row)
                if piece and piece.alive:
                    center = (
                        (col + PADDING_CELLS) * GRID_SIZE + GRID_SIZE // 2,
                        (row + PADDING_CELLS) * GRID_SIZE + GRID_SIZE // 2,
                    )

                    # 对战开始后，且不是红方、且未揭示的棋子画“背面”
                    if state_manager.is_playing and piece.owner != 'Red' and not piece.revealed:
                        # 仍然用自己的颜色，只是不 blit 文字
                        color = OWNER_TO_COLOR[piece.owner]
                        pygame.draw.circle(screen, color, center, GRID_SIZE // 2 - 6)
                        pygame.draw.circle(screen, BLACK,  center, GRID_SIZE // 2 - 6, 2)

                    else:
                        # 正常画“正面” + 文字
                        color = OWNER_TO_COLOR[piece.owner]
                        pygame.draw.circle(screen, color, center, GRID_SIZE // 2 - 6)
                        pygame.draw.circle(screen, BLACK,  center, GRID_SIZE // 2 - 6, 2)

                        # 对战未开始 或 红方 或 已revealed 才画文字
                        if (not state_manager.is_playing) or piece.owner == 'Red' or piece.revealed:
                            text = DISPLAY_NAMES.get(piece.name, piece.name[:2])
                            label = font.render(text, True, BLACK)
                            screen.blit(label, label.get_rect(center=center))
                # ---------------- 绘制棋子 end ----------------

        # highlight selection
        if game.selected:
            row, col = game.selected
            rect = pygame.Rect(
                (col + PADDING_CELLS) * GRID_SIZE,
                (row + PADDING_CELLS) * GRID_SIZE,
                GRID_SIZE, GRID_SIZE
            )
            pygame.draw.rect(screen, BLUE, rect, 3)

        game.draw_overlay(screen) #draw small
        if state_manager.is_playing:
            state_manager.check_elimination(game)

        # —— 简易胜利判断 —— 
        if state_manager.game_over:
            print(state_manager.get_victory_message())
            running = False  # 跳出主循环
        pygame.display.flip()

       

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
