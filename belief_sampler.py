# belief_sampler.py - Belief Sampler for Four Kingdoms Military Chess (四国军棋)
#
# This module maintains and updates the belief distribution over hidden opponent piece placements.
# It provides functionality to sample complete hidden states for use in POMCP/MCTS.

import random
from collections import defaultdict
from constants import MAX_COUNTS,camp_positions,hq_positions
from chessboard import ChessBoard
from copy import deepcopy
from typing import Tuple, Dict, List

class BeliefSampler:
    def __init__(self,
                 board,
                 positions: List[Tuple[int,int]],
                 piece_types: List[str],      # 显式传入 piece_types
                 max_counts: Dict[str,int],
                 my_side: str):
        """
        board: 当前的棋盘对象，用于获取格子布局和可视信息
        piece_types: 对手所有可能棋子类型列表，如["Flag","Mine","Bomb",...]
        max_counts: dict, 每种棋子的最大数量限制，用于约束信念空间。
                    若为 None,则使用 constants.py 中的 MAX_COUNTS。
        """
        self.board = board
        self.piece_types = piece_types
        # 若外部未传入约束，则使用默认 MAX_COUNTS
        self.max_counts = max_counts if max_counts is not None else MAX_COUNTS
        # beliefs: mapping from position (x,y) to dict of piece_type->probability
        #剩余可分配数量，后续按它来约束
        self.remaining_counts = deepcopy(self.max_counts)
        self.beliefs = defaultdict(lambda: {ptype: 0 for ptype in piece_types})
        self._hq_flag_seen_red = set()    # 记录红方 HQ 首次翻开的坐标
        self._hq_flag_seen_green = set()  # 记录绿方 HQ 首次翻开的坐标
        self.initialize_beliefs()

    def initialize_beliefs(self):
        """
        初始化所有隐藏格子的信念分布，加入相对坐标的区域规则：
        """
        # 这个方法会返回所有 “不是我方” 且 “还没有翻面” 的棋子的位置列表；
        # 每个位置是一个 (x, y) 的元组（坐标）；
        hidden_positions = self.board.get_all_hidden_positions(self.my_side)
        
        rows = self.board.rows  #获取棋盘的总行数 17

        #所有敌方隐藏位置上所有棋子类型的概率初始化为 0.0。
        for pos in hidden_positions:
            for p in self.piece_types:
                self.beliefs[pos][p] = 0.0

        # 针对每个隐藏格子，按所属 owner 计算 rel_y，再判区域
        for x, y in hidden_positions:
            owner = self.board.get_piece(x, y).owner
            # 计算相对后排坐标 rel_y
            # 假设 Red 在底部，Green 在顶部
            if owner == "Red":
                rel_y = y
            else:  # owner == "Green"
                rel_y = rows - 1 - y

            legal = []

            # 1) HQ 只放 Flag
            if self.board.is_hq(x, y):
                legal = ["Flag"]

            # 2) 最后两排（rel_y <= 1）可以放 Mine
            elif rel_y <= 1:
                legal = ["Mine"]

            # 3) 第一排（rel_y == 0）不能放 Bomb
            elif rel_y == 5:
                legal = [ptype for ptype in self.piece_types if ptype != "Bomb"]

            # 4) 其它格子：所有类型都允许
            else:
                legal = list(self.piece_types)

            # 给这些合法类型赋未归一化权重 1
            for ptype in legal:
                self.beliefs[(x, y)][ptype] = 1.0

        # 最后 IPF 归一化并加全局数量约束
        # 比如说，一共有10个格子可以合法地雷 那么进行权重分布
        self._normalize_and_constrain()
 


    def _normalize_and_constrain(self, iterations=5):
        # 使用 IPF（Iterative Proportional Fitting）算法对 belief 分布做归一化处理，
        # 同时施加全局棋子数量约束（每种棋子最多只能放指定数量）。
        # iterations：迭代轮数，用于逼近满足所有约束的合理分布。 一共迭代5轮
        positions = list(self.beliefs.keys())
        # IPF 过程：在“每格归一化”和“类型数量限制”之间交替迭代
        for _ in range(iterations):
            # -------- 第一步：对每一个格子（位置）归一化，使每个格子的概率和为 1 --------
            for pos in positions:
                total = sum(self.beliefs[pos].values())
                if total > 0:
                    for ptype in self.beliefs[pos]:
                        self.beliefs[pos][ptype] /= total
           # -------- 第二步：缩放每种棋子的概率，使其总和符合 max_counts 限制 --------
            for ptype, max_count in self.max_remaining_counts.items():
                # 统计这种棋子在所有位置上的概率总和
                col_total = sum(self.beliefs[pos][ptype] for pos in positions)
                if col_total > 0:
                    scale = max_count / col_total
                    for pos in positions:
                        self.beliefs[pos][ptype] *= scale
        # -------- 最后再做一遍归一化，确保每个位置的概率之和为 1 --------
        for pos in positions:
            total = sum(self.beliefs[pos].values())
            if total > 0:
                for ptype in self.beliefs[pos]:
                    self.beliefs[pos][ptype] /= total

    #更新如果某方棋子从source走到target会有什么样的更新
    def update(self, source: Tuple[int, int], target: Tuple[int, int]):
        if self.my_side == "Red":
            # 我是红方，敌方是绿方，绿方 HQ 在 (7,16),(9,16)
            enemy_hqs = [(7, 16), (9, 16)]
            seen_set = self._hq_flag_seen_green
        else:
            # 我是绿方，敌方是红方，红方 HQ 在 (7,0),(9,0)
            enemy_hqs = [(7, 0), (9, 0)]
            seen_set = self._hq_flag_seen_red

        attacker = self.board.get_piece(*source)
        target_piece = self.board.get_piece(*target)
        #先处理双方有摊军棋的可能
        for hq in enemy_hqs:
            p = self.board.get_piece(*hq)
            # 首次翻开的军旗
            if p and p.name == "Flag" and p.revealed and hq not in seen_set:
                seen_set.add(hq)  # 标记已处理

                # 更新 remaining_counts
                if hasattr(self, "remaining_counts"):
                    self.remaining_counts["General"] = max(self.remaining_counts["General"] - 1, 0)
                
                for ptype in self.piece_types:
                    self.beliefs[target][ptype] = 0.0

                self._normalize_and_constrain()
                return 
        
        #如果是target_piece是走的是非链接铁路段的话 自动判定target_piece为工兵
        if attacker == None:
            from routes import LineType, is_connected_by
            x1,y1 = source; x2,y2 = target
            if is_connected_by(x1,y1,x2,y2,LineType.RAIL) \
            and not self.board.clear_straight_rail_path(x1,y1,x2,y2):
                for p in self.piece_types:
                    self.beliefs[target][p] = 1.0 if p=="Engineer" else 0.0
                if hasattr(self,"remaining_counts"):
                    self.remaining_counts["Engineer"] = max(self.remaining_counts["Engineer"]-1,0)
                self._normalize_and_constrain()
                return
            # 普通走子排除不能动的
            for bad in ("Flag","Mine"):
                self.beliefs[target][bad] = 0.0
            self._normalize_and_constrain()
            return
            
        #如果是我方棋子攻击敌方棋子
        elif attacker and target_piece and attacker.owner == self.my_side and target_piece.owner != self.my_side:
            # —— 在“我方炸弹攻击”分支里 —— 
            if attacker.name == "Bomb":
                # 1) 取出 target 位置的原始 belief 分布
                dist = self.beliefs[target].copy()

                # 2) 对 remaining_counts 做软更新：按概率扣减
                for ptype, prob in dist.items():
                    # 剩余数量减去“它可能是该类型”的概率
                    if hasattr(self, "remaining_counts"):
                        self.remaining_counts[ptype] = max(self.remaining_counts[ptype] - prob, 0.0)

                # 3) 将 source 和 target 位置的 belief 清零（因为双方都死了）
                for pos in (source, target):
                    for ptype in self.piece_types:
                        self.beliefs[pos][ptype] = 0.0

                # 4) 重新做一次归一化 + 全局数量约束
                self._normalize_and_constrain()
                return

            elif attacker.name == "Engineer":
                # 先把战前对目标位置的分布存下来，用于 soft 更新 remaining_counts
                pre_dist = self.beliefs[target].copy()

                # 1) 我活对方死 → 目标一定是 Mine 或 Flag
                if attacker.alive and not target_piece.alive:
                    # 扣减“死去那颗”的可能性额度
                    if hasattr(self, "remaining_counts"):
                        for ptype, prob in pre_dist.items():
                            self.remaining_counts[ptype] = max(self.remaining_counts[ptype] - prob, 0.0)
                    # 只保留 Mine 和 Flag
                    for ptype in self.piece_types:
                        self.beliefs[target][ptype] = 1.0 if ptype in ("Mine", "Flag") else 0.0

                # 2) 互杀 → 目标一定是 Engineer 或 Bomb
                elif not attacker.alive and not target_piece.alive:
                    if hasattr(self, "remaining_counts"):
                        for ptype, prob in pre_dist.items():
                            self.remaining_counts[ptype] = max(self.remaining_counts[ptype] - prob, 0.0)
                    for ptype in self.piece_types:
                        self.beliefs[target][ptype] = 1.0 if ptype in ("Engineer", "Bomb") else 0.0

                # 3) 我死对方活 → 目标不可能是 Mine、Engineer、Bomb、Flag
                elif not attacker.alive and target_piece.alive:
                    # 扣减我被炸死那颗的可能性额度（其实也可以扣 pre_dist）
                    if hasattr(self, "remaining_counts"):
                        for ptype, prob in pre_dist.items():
                            self.remaining_counts[ptype] = max(self.remaining_counts[ptype] - prob, 0.0)
                    # 排除 Mine、Engineer、Bomb、Flag
                    for ptype in ("Mine", "Engineer", "Bomb", "Flag"):
                        self.beliefs[target][ptype] = 0.0

                # 4) 最后，重新归一化并施加数量约束
                self._normalize_and_constrain()
                return

            else:
                # —— 普通兵种（既不是炸弹也不是工兵）攻击后的贝叶斯更新 —— 
                my_rank = attacker.rank

                # 1) 我方活下来，对方死去 （我方胜利）
                if attacker.alive and not target_piece.alive:
                    # 对方一定是比我低的棋子，除了炸弹（炸弹互杀）
                    for ptype in list(self.beliefs[target].keys()):
                        rank = PIECE_RANKS[ptype]
                        # 如果类型是 Bomb，保留；否则 rank 必须 < my_rank
                        if ptype != "Bomb" and rank >= my_rank:
                            self.beliefs[target][ptype] = 0.0

                # 2) 我方与对方同归于尽 （互杀）
                elif not attacker.alive and not target_piece.alive:
                    # 对方要么 rank == my_rank，要么是炸弹
                    for ptype in list(self.beliefs[target].keys()):
                        rank = PIECE_RANKS[ptype]
                        if not (ptype == "Bomb" or rank == my_rank):
                            self.beliefs[target][ptype] = 0.0

                # 3) 我方死去，对方存活 （我方失败）
                elif not attacker.alive and target_piece.alive:
                    # 对方一定比我强，且不是地雷/工兵（工兵 > 地雷）或军旗（Flag 不能动）
                    for ptype in list(self.beliefs[target].keys()):
                        rank = PIECE_RANKS[ptype]
                        if rank <= my_rank:
                            self.beliefs[target][ptype] = 0.0

                # —— 更新完这一格的局部 belief 之后，记得更新 remaining_counts 和归一化 —— 
                if hasattr(self, "remaining_counts"):
                    # 用事前 belief 软扣减 remaining_counts（示例略）
                    pass

                self._normalize_and_constrain()
                return

    def sample_state(self):
        """
        Sample a complete hidden state (assignment of piece types to each hidden position)
        according to current belief distribution, respecting remaining_counts.
        返回 dict: position->piece_type
        """
        from copy import deepcopy
        # 1) 拷贝一份剩余可分配数量，用于在采样时实时扣减
        remaining = deepcopy(self.remaining_counts)
        sampled = {}
        positions = list(self.beliefs.keys())
        random.shuffle(positions) # 随机打乱位置顺序，避免固定偏差
        # 2) 逐个位置采样
        for pos in positions:
            dist = self.beliefs[pos].copy()  # 当前位置的类型概率分布
           # 2.1) 去除那些已无剩余配额的类型
            for ptype in list(dist.keys()):
                if remaining.get(ptype, 0) <= 0:
                    dist.pop(ptype)
            total = sum(dist.values())
            if total <= 0:
                # 若当前分布全为 0，则在剩余还有配额的类型中均匀采样
                dist = {ptype: 1 for ptype, cnt in remaining.items() if cnt > 0}
                total = sum(dist.values())
            # 2.2) 归一化概率后随机选择
            probs = {ptype: val/total for ptype, val in dist.items()}
            choice = random.choices(list(probs.keys()), weights=probs.values())[0]
            sampled[pos] = choice
            # 2.3) 扣减该类型的剩余配额（可以是浮点数）
            remaining[choice] -= 1
        # 3) 返回这次完整采样的对手隐藏状态
        return sampled


    def reset(self):
        """
        重置整个 BeliefSampler 到初始状态：
        - 重新初始化 beliefs（均匀分布 + 位置/区域规则 + IPF 约束）
        - 重置剩余可分配数量 remaining_counts 为 max_counts
        - 清空首次翻旗记录 _hq_flag_seen_red/_hq_flag_seen_green
        """
        # 1) 清空 HQ 翻旗记录
        self._hq_flag_seen_red.clear()
        self._hq_flag_seen_green.clear()

        # 2) 重置 remaining_counts 回到初始 max_counts
        from copy import deepcopy
        self.remaining_counts = deepcopy(self.max_counts)

        # 3) 重新初始化 beliefs（内部会调用 _normalize_and_constrain）
        self.initialize_beliefs()
