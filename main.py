from routes import is_connected_by, LineType
from chessboard import ChessBoard

def main():
    chessboard = ChessBoard()
    x1, y1 = 16, 7
    x2, y2 = 16, 8

    print("测试点:", (x1, y1), "和", (x2, y2))
    if is_connected_by(x1, y1, x2, y2, LineType.RAIL):
        print("这两个格子通过【铁路】连接 ✅")
    elif is_connected_by(x1, y1, x2, y2, LineType.ROAD):
        print("这两个格子通过【公路】连接 ✅")
    else:
        print("这两个格子【不相连】 ❌")

    piece = chessboard.get_piece(x1, y1)
    print("当前位置棋子:", piece)
    print(chessboard.get_piece(1, 8))

if __name__ == "__main__":
    main()