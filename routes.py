from enum import Enum

class LineType(Enum):
    ROAD = 1
    RAIL = 2

# 存储格子之间的连线信息：
# connections[(x, y)] = [((nx, ny), LineType), ...]
connections = {}

def add_connection(x1, y1, x2, y2, line_type):
    connections.setdefault((x1, y1), []).append(((x2, y2), line_type))
    connections.setdefault((x2, y2), []).append(((x1, y1), line_type))

def get_connections(x, y):
    return connections.get((x, y), [])

def is_connected_by(x1, y1, x2, y2, line_type):
    return any((nx, ny) == (x2, y2) and t == line_type
               for (nx, ny), t in get_connections(x1, y1))

def is_displayable(row, col):
    # （原有可通行区域逻辑不变）
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
    # 垂直铁路段
    for y in range(1, 15):
        add_connection(6, y, 6, y+1, LineType.RAIL)    # 6,1 → 6,15
        add_connection(10, y, 10, y+1, LineType.RAIL)  # 10,1 → 10,15
    for y in range(6, 10):
        add_connection(15, y, 15, y+1, LineType.RAIL)  # 15,6 → 15,10

    # 水平铁路段
    for x in range(1, 15):
        add_connection(x, 6, x+1, 6, LineType.RAIL)    # 1,6 → 15,6
        add_connection(x, 10, x+1, 10, LineType.RAIL)  # 1,10 → 15,10

    # 四条短段
    for x in range(6, 10):
        add_connection(x, 1, x+1, 1, LineType.RAIL)     # 6,1 → 10,1
        add_connection(x, 15, x+1, 15, LineType.RAIL)   # 6,15 → 10,15
    for y in range(6, 10):
        add_connection(1, y, 1, y+1, LineType.RAIL)     # 1,6 → 1,10

    # 对角线铁路段
    add_connection(5, 6, 6, 5, LineType.RAIL)
    add_connection(5, 10, 6, 11, LineType.RAIL)
    add_connection(10, 5, 11, 6, LineType.RAIL)
    add_connection(10, 11, 11, 10, LineType.RAIL)

    # 四条横道
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

    #井道
    # 新增：8,5 → 8,11
    for y in range(5, 11):
        add_connection(8, y, 8, y+1, LineType.RAIL)

    # 新增：5,8 → 11,8
    for x in range(5, 11):
        add_connection(x, 8, x+1, 8, LineType.RAIL)

def setup_connections(rows=17, cols=17):
    # 先添加道路，但跳过所有铁路段
    for y in range(rows):
        for x in range(cols):
            if not is_displayable(y, x):
                continue
            for dx, dy in ((1, 0), (0, 1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < cols and 0 <= ny < rows and is_displayable(ny, nx)):
                    continue
                # 如果这个相邻对已经在铁路列表里，就跳过添加道路
                if is_connected_by(x, y, nx, ny, LineType.RAIL):
                    continue
                add_connection(x, y, nx, ny, LineType.ROAD)

    # 再添加铁路（只会添加相邻格子）
    setup_rail_connections()

# 自动执行初始化
setup_connections()

camp_positions = [
    (2, 7), (4, 7), (14, 7), (12, 7),
    (2, 9), (4, 9), (14, 9), (12, 9),
    (3, 8), (13, 8),
    (7, 2), (7, 4), (7, 12), (7, 14),
    (9, 2), (9, 4), (9, 12), (9, 14),
    (8, 3), (8, 13)
]

for x, y in camp_positions:
    for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < 17 and 0 <= ny < 17:
            add_connection(x, y, nx, ny, LineType.ROAD)

