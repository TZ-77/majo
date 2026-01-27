import tkinter as tk
from tkinter import messagebox
import tkinter.simpledialog as simpledialog
import random

# --- 基礎資料定義 ---
TILE_NAMES = [
    '1萬','2萬','3萬','4萬','5萬','6萬','7萬','8萬','9萬',
    '1筒','2筒','3筒','4筒','5筒','6筒','7筒','8筒','9筒',
    '1條','2條','3條','4條','5條','6條','7條','8條','9條',
    '東','南','西','北','中','發','白',
    '春','夏','秋','冬','梅','蘭','竹','菊'
]

WAN = range(0, 9); TONG = range(9, 18); TIAO = range(18, 27)
WINDS = range(27, 31); DRAGONS = range(31, 34); HONORS = range(27, 34)

def counts34(tiles):
    c = [0] * 34
    for t in tiles:
        if 0 <= t < 34: c[t] += 1
    return c

def is_hun_yi_se(all_tiles):
    """混一色: 只有一種數牌 + 字牌"""
    suits = [False, False, False]  # 萬, 筒, 條
    has_honor = False
    for t in all_tiles:
        if t < 9: suits[0] = True
        elif t < 18: suits[1] = True
        elif t < 27: suits[2] = True
        elif t < 34: has_honor = True
    return suits.count(True) == 1 and has_honor

def is_qing_yi_se(all_tiles):
    """清一色: 只有一種數牌，無字牌"""
    suits = [False, False, False]
    has_honor = False
    for t in all_tiles:
        if t < 9: suits[0] = True
        elif t < 18: suits[1] = True
        elif t < 27: suits[2] = True
        elif t < 34: has_honor = True
    
    # 如果有字牌就不是清一色
    if has_honor:
        return False
    
    # 只能有一種數牌
    return suits.count(True) == 1

def is_zi_yi_se(all_tiles):
    """字一色: 所有牌都是字牌（東南西北中發白）"""
    for t in all_tiles:
        if t < 27:  # 不是字牌
            return False
    return True

def is_ping_hu(all_tiles, exposed, flowers=None, is_zi_mo=False, waiting_count=None, winning_tile=None, pure_hand=None, need_melds=None):
    """平胡: 嚴格判斷台灣麻將平胡規則"""
    # 1. 有花牌不算平胡
    if flowers and len(flowers) > 0:
        return False
    
    # 2. 不能有字牌
    for t in all_tiles:
        if t >= 27:  # 字牌
            return False
    
    # 3. 將（眼/雀頭）不能是字牌
    if winning_tile is not None and winning_tile >= 27:
        return False
    
    # 4. 自摸不算平胡（台灣麻將規則）
    if is_zi_mo:
        return False
    
    # 5. 獨聽不算平胡
    if waiting_count is not None and waiting_count == 1:
        return False
    
    # 6. 檢查副露是否有碰/槓
    for combo in exposed:
        if len(combo) >= 3 and combo[0] == combo[1]:  # 刻子或槓子
            return False
    
    # 7. 檢查手牌是否全部是順子（包含將牌）
    if pure_hand is not None and need_melds is not None:
        # pure_hand 已經是17張牌，直接用於分解
        hand_for_decomposition = list(pure_hand)
        
        deco = MJLogic.find_one_decomposition_17(hand_for_decomposition, need_melds)
        if deco:
            # 檢查是否全是順子
            all_chow = all(m[0] == "chow" for m in deco[1])
            # 檢查將牌是否不是字牌
            pair_tile = deco[0]
            if pair_tile >= 27:  # 將牌是字牌
                return False
            return all_chow
    
    return True

def is_quan_qiu_ren(hand_tiles, exposed, is_zi_mo):
    """全求人: 手牌只剩將牌(2張)，全靠吃碰槓，且必須是榮胡（別人放炮）
    hand_tiles: 胡牌後的手牌（包含將牌，共2張）
    """
    pure_hand = [t for t in hand_tiles if t < 34]
    # 全求人：5組副露 + 只剩將牌（2張） + 榮胡
    return len(pure_hand) == 2 and len(exposed) == 5 and not is_zi_mo

def is_ban_qiu_ren(hand_tiles, exposed, is_zi_mo):
    """半求人: 手牌只剩將牌(2張)，全靠吃碰槓，且必須是自摸
    hand_tiles: 胡牌後的手牌（包含將牌，共2張）
    """
    pure_hand = [t for t in hand_tiles if t < 34]
    # 半求人：5組副露 + 只剩將牌（2張） + 自摸
    return len(pure_hand) == 2 and len(exposed) == 5 and is_zi_mo

def count_waiting_tiles(hand, exposed, winning_tile=None):
    """計算聽幾張牌 (用於獨聽判定)
    hand: 胡牌前的手牌（不包含胡的牌）
    """
    waiting = []
    for test_tile in range(34):
        # 把測試牌加入手牌，檢查是否能胡
        test_hand = list(hand) + [test_tile]
        if MJLogic.is_hu(test_hand, exposed):
            waiting.append(test_tile)
    return waiting

def is_du_ting(hand, exposed, winning_tile=None):
    """獨聽: 只聽一張牌"""
    waiting = count_waiting_tiles(hand, exposed, winning_tile)
    return len(waiting) == 1

def is_peng_peng_hu(pure_hand, exposed, need_melds):
    """碰碰胡: 所有面子都是刻子（包含手牌和副露）"""
    # 檢查副露部分是否全是刻子
    for combo in exposed:
        if len(combo) >= 3:
            # 刻子：三張相同的牌
            if combo[0] == combo[1] == combo[2]:
                continue  # 是刻子
            elif len(combo) == 4 and combo[0] == combo[1] == combo[2] == combo[3]:
                continue  # 槓子也屬於刻子類
            else:
                # 如果有順子，就不是碰碰胡
                return False
    
    # 檢查手牌部分是否可以分解為全刻子
    c = counts34(pure_hand)
    
    def can_all_pong(cc, melds_left, pair_found):
        """檢查是否可以分解為全刻子 + 一對將"""
        # 找到第一個有牌的位置
        first = next((i for i, v in enumerate(cc) if v > 0), -1)
        
        if first == -1:
            # 所有牌都用完了
            return melds_left == 0 and pair_found
        
        # 如果還沒有將牌，且有2張以上，嘗試選為將牌
        if not pair_found and cc[first] >= 2:
            cc[first] -= 2
            if can_all_pong(cc, melds_left, True):
                cc[first] += 2
                return True
            cc[first] += 2
        
        # 嘗試形成刻子
        if cc[first] >= 3 and melds_left > 0:
            cc[first] -= 3
            if can_all_pong(cc, melds_left - 1, pair_found):
                cc[first] += 3
                return True
            cc[first] += 3
        
        return False
    
    return can_all_pong(list(c), need_melds, False)

def count_an_ke(pure_hand, exposed, winning_tile=None, is_zi_mo=False):
    """計算暗刻數量（修正版）"""
    # 取得手牌計數（17張）
    hand_counts = counts34(pure_hand)
    
    an_ke_count = 0
    
    # 如果是榮胡，需要考慮胡牌前的手牌狀態
    hand_before = None
    if not is_zi_mo and winning_tile is not None:
        hand_before = list(pure_hand)
        if winning_tile in hand_before:
            hand_before.remove(winning_tile)
    
    for i in range(34):
        if is_zi_mo:
            # 自摸：直接看手牌是否有3張或4張
            if hand_counts[i] >= 3:
                an_ke_count += 1
        else:
            # 榮胡：看胡牌前的手牌狀態
            if hand_before is not None:
                hand_counts_before = counts34(hand_before)
                if hand_counts_before[i] >= 3:
                    # 檢查是否為將牌
                    if i == winning_tile:
                        # 如果胡的牌是刻子中的一張，要特別處理
                        if hand_counts_before[i] == 3:
                            # 胡之前有3張，這是刻子
                            an_ke_count += 1
                        elif hand_counts_before[i] == 2:
                            # 胡之前有2張，這是將牌，不是刻子
                            pass
                    else:
                        an_ke_count += 1
    
    return an_ke_count

def is_da_si_xi(all_tiles, exposed):
    """大四喜: 東南西北四組刻子"""
    c_all = counts34(all_tiles)
    
    # 檢查四種風牌
    wind_counts = [c_all[27], c_all[28], c_all[29], c_all[30]]  # 東南西北
    
    # 大四喜: 四種風牌都有刻子（3張或4張）
    for i in range(4):
        if wind_counts[i] < 3:
            return False
    
    return True

def is_xiao_si_xi(all_tiles, exposed):
    """小四喜: 東南西北其中三組刻子，一組對子（將牌）"""
    c_all = counts34(all_tiles)
    
    # 檢查四種風牌
    wind_counts = [c_all[27], c_all[28], c_all[29], c_all[30]]  # 東南西北
    
    # 計算刻子數和將牌數
    pong_count = 0
    pair_count = 0
    
    for i in range(4):
        if wind_counts[i] >= 3:
            pong_count += 1
        elif wind_counts[i] == 2:
            pair_count += 1
    
    # 小四喜: 三種風牌有刻子，一種當將牌
    if pong_count == 3 and pair_count == 1:
        return True
    
    return False

def is_da_san_yuan(all_tiles, exposed):
    """大三元: 中發白三組刻子"""
    c_all = counts34(all_tiles)
    
    # 檢查三元牌 (中=31, 發=32, 白=33)
    dragon_counts = [c_all[31], c_all[32], c_all[33]]  # 中發白
    
    # 大三元: 三種三元牌都有刻子（3張或4張）
    for i in range(3):
        if dragon_counts[i] < 3:
            return False
    
    return True

def is_xiao_san_yuan(all_tiles, exposed):
    """小三元: 中發白其中兩組刻子，一組對子（將牌）"""
    c_all = counts34(all_tiles)
    
    # 檢查三元牌 (中=31, 發=32, 白=33)
    dragon_counts = [c_all[31], c_all[32], c_all[33]]  # 中發白
    
    # 計算刻子數和將牌數
    pong_count = 0
    pair_count = 0
    
    for i in range(3):
        if dragon_counts[i] >= 3:
            pong_count += 1
        elif dragon_counts[i] == 2:
            pair_count += 1
    
    # 小三元: 兩種三元牌有刻子，一種當將牌
    if pong_count == 2 and pair_count == 1:
        return True
    
    return False

class MJLogic:
    @staticmethod
    def is_hu(hand_indices, exposed, winning_tile=None):
        """
        核心胡牌判定：面子補完法
        台麻16張麻將需要 5 組面子 + 1 對將。
        胡牌時總共17張牌（16張手牌+1張胡的牌）
        """
        # 如果winning_tile有提供，加到手牌中
        if winning_tile is not None:
            hand_indices = hand_indices + [winning_tile]
        
        pure_hand = [t for t in hand_indices if t < 34]
        exposed_count = len(exposed)
        need_melds = 5 - exposed_count
        
        # 檢查手牌張數：需要滿足 (5 - 已副露組數) * 3 + 2
        if len(pure_hand) != (need_melds * 3 + 2):
            return False

        c = counts34(pure_hand)

        def can_make_melds(cc, melds_left):
            if melds_left == 0: return all(v == 0 for v in cc)
            first = next((i for i, v in enumerate(cc) if v > 0), -1)
            if first == -1: return False
            # 刻子
            if cc[first] >= 3:
                cc[first] -= 3
                if can_make_melds(cc, melds_left - 1): return True
                cc[first] += 3
            # 順子 - 只有數牌才能組順子
            if first < 27 and first % 9 <= 6:
                if cc[first+1] > 0 and cc[first+2] > 0:
                    cc[first] -= 1; cc[first+1] -= 1; cc[first+2] -= 1
                    if can_make_melds(cc, melds_left - 1): return True
                    cc[first] += 1; cc[first+1] += 1; cc[first+2] += 1
            return False

        for i in range(34):
            if c[i] >= 2:
                c[i] -= 2
                if can_make_melds(list(c), need_melds): return True
                c[i] += 2
        return False

    @staticmethod
    def find_one_decomposition_17(pure_hand_17, need_melds):
        """為17張牌找一個分解方式"""
        c = counts34(pure_hand_17)
        def dfs(cc, melds_left, melds):
            if melds_left == 0: return melds if all(v == 0 for v in cc) else None
            first = next((i for i, v in enumerate(cc) if v > 0), -1)
            if first == -1: return None
            if cc[first] >= 3:
                cc[first] -= 3
                res = dfs(cc, melds_left - 1, melds + [("pong", (first, first, first))])
                cc[first] += 3
                if res: return res
            # 順子 - 只有數牌才能組順子
            if first < 27 and first % 9 <= 6 and cc[first+1] > 0 and cc[first+2] > 0:
                cc[first] -= 1; cc[first+1] -= 1; cc[first+2] -= 1
                res = dfs(cc, melds_left - 1, melds + [("chow", (first, first+1, first+2))])
                cc[first] += 1; cc[first+1] += 1; cc[first+2] += 1
                if res: return res
            return None
        for i in range(34):
            if c[i] >= 2:
                c[i] -= 2
                res = dfs(list(c), need_melds, [])
                if res is not None: return i, res
                c[i] += 2
        return None

    @staticmethod
    def calculate_tai_star31_auto(pure_hand, exposed, flowers, is_zi_mo, is_dealer, streak, is_haidilao, is_kong_flower, m_kong, a_kong, round_wind=0, seat_wind=0, winning_tile=None, waiting_count=None, is_first_round=False, is_tenhou=False, is_chihou=False):
        tai = 0; details = []
        all_tiles = list(pure_hand)
        for combo in exposed:
            for t in combo: 
                if t < 34: all_tiles.append(t)
        
        c_all = counts34(all_tiles)

        # 1. 莊家/連莊
        if is_dealer:
            if streak > 0:
                tai += (2 * streak + 1)
                details.append(f"連{streak}拉{streak} (包含莊家台共 {2 * streak + 1}台)")
            else:
                tai += 1
                details.append("莊家 (1台)")

        # 2. 天胡/地胡
        if is_first_round and is_zi_mo and len(exposed) == 0:
            if is_dealer:
                tai += 24; details.append("天胡 (24台)")
            else:
                tai += 16; details.append("地胡 (16台)")
        
        # 3. 事件台
        if is_zi_mo: tai += 1; details.append("自摸 (1台)")
        if len(exposed) == 0: tai += 1; details.append("門清 (1台)")
        if is_haidilao: tai += 1; details.append("海底撈月 (1台)")
        if is_kong_flower: tai += 1; details.append("槓上開花 (1台)")
        
        # 4. 天聽/地聽
        if is_tenhou:
            tai += 8; details.append("天聽 (8台)")
        elif is_chihou:
            tai += 4; details.append("地聽 (4台)")

        # 檢查是否為四喜系列和三元系列
        has_da_si_xi = is_da_si_xi(all_tiles, exposed)
        has_xiao_si_xi = is_xiao_si_xi(all_tiles, exposed)
        has_da_san_yuan = is_da_san_yuan(all_tiles, exposed)
        has_xiao_san_yuan = is_xiao_san_yuan(all_tiles, exposed)
        
        # 檢查是否為字一色
        has_zi_yi_se = is_zi_yi_se(all_tiles)
        
        # 5. 風刻台
        if not (has_da_si_xi or has_xiao_si_xi):
            WIND_NAMES = ['東', '南', '西', '北']
            for w_idx in WINDS:
                if c_all[w_idx] >= 3:
                    wind_pos = w_idx - 27
                    is_round = (wind_pos == round_wind)
                    is_seat = (wind_pos == seat_wind)
                    
                    if is_round or is_seat:
                        if is_round and is_seat:
                            tai += 2; details.append(f"{WIND_NAMES[wind_pos]}風刻 (圈風+門風 2台)")
                        elif is_round:
                            tai += 1; details.append(f"{WIND_NAMES[wind_pos]}風刻 (圈風 1台)")
                        elif is_seat:
                            tai += 1; details.append(f"{WIND_NAMES[wind_pos]}風刻 (門風 1台)")
        
        # 6. 三元牌刻
        if not (has_da_san_yuan or has_xiao_san_yuan):
            for d_idx in DRAGONS:
                if c_all[d_idx] >= 3:
                    tai += 1; details.append(f"{TILE_NAMES[d_idx]}刻 (1台)")

        # 7. 槓台
        if m_kong > 0: tai += m_kong; details.append(f"明槓 ({m_kong}台)")
        if a_kong > 0: tai += (a_kong * 2); details.append(f"暗槓 ({a_kong*2}台)")

                # 8. 暗刻計算
        an_ke_count = count_an_ke(pure_hand, exposed, winning_tile, is_zi_mo)
        
        # 9. 大牌型
        need_m = 5 - len(exposed)
        
        # ========== 暗刻系列檢查 ==========
        # 注意：暗刻系列可以與碰碰胡同時存在
        
        if len(exposed) == 0:  # 必須門清
            # 1. 五暗刻 (8台) - 必須有5個暗刻
            if an_ke_count == 5:
                tai += 8
                details.append("五暗刻 (8台)")
            
            # 2. 四暗刻 (5台) - 有4個暗刻
            elif an_ke_count == 4:
                tai += 5
                
                # 檢查是否為四暗刻單騎
                if not is_zi_mo and winning_tile is not None:
                    hand_counts = counts34(pure_hand)
                    if hand_counts[winning_tile] == 1:
                        details.append("四暗刻單騎 (5台)")
                    else:
                        details.append("四暗刻 (5台)")
                else:
                    details.append("四暗刻 (5台)")
            
            # 3. 三暗刻 (2台) - 有3個暗刻
            elif an_ke_count == 3:
                tai += 2
                details.append("三暗刻 (2台)")

        # 大四喜 (16台)
        if has_da_si_xi:
            tai += 16; details.append("大四喜 (16台)")
        # 小四喜 (8台)
        elif has_xiao_si_xi:
            tai += 8; details.append("小四喜 (8台)")
        
        # 大三元 (8台)
        if has_da_san_yuan:
            tai += 8; details.append("大三元 (8台)")
        # 小三元 (4台)
        elif has_xiao_san_yuan:
            tai += 4; details.append("小三元 (4台)")
        
        # 字一色 (16台)
        if has_zi_yi_se:
            tai += 16; details.append("字一色 (16台)")
        
        # ========== 碰碰胡檢查 ==========
        # 注意：碰碰胡可以與暗刻系列同時存在
        # 移除之前的互斥檢查
        is_peng_peng = is_peng_peng_hu(pure_hand, exposed, need_m)
        if is_peng_peng:
            tai += 4
            details.append("碰碰胡 (4台)")
        
        # 清一色 (8台)
        if not has_zi_yi_se and is_qing_yi_se(all_tiles):
            tai += 8; details.append("清一色 (8台)")
        # 混一色 (4台)
        elif not has_zi_yi_se and is_hun_yi_se(all_tiles):
            tai += 4; details.append("混一色 (4台)")
        
        # 平胡 (2台)
        if not has_zi_yi_se and is_ping_hu(all_tiles, exposed, flowers, is_zi_mo, waiting_count, winning_tile, pure_hand, need_m):
            tai += 2; details.append("平胡 (2台)")
        
        # 全求人 (2台)
        if is_quan_qiu_ren(pure_hand, exposed, is_zi_mo):
            tai += 2; details.append("全求人 (2台)")
        
        # 半求人 (1台)
        if is_ban_qiu_ren(pure_hand, exposed, is_zi_mo):
            tai += 1; details.append("半求人 (1台)")
        
        # 獨聽 (1台)
        if waiting_count is not None:
            if waiting_count == 1:
                tai += 1; details.append("獨聽 (1台)")
        elif winning_tile is not None:
            pure_hand_before_win = list(pure_hand)
            if winning_tile in pure_hand_before_win:
                pure_hand_before_win.remove(winning_tile)
            
            if is_du_ting(pure_hand_before_win, exposed, winning_tile):
                tai += 1; details.append("獨聽 (1台)")
        
        return max(1, tai), details

class MahjongFinalPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Python 16張麻將")
        self.root.geometry("1160x920")
        self.root.configure(bg="#1a472a")
        
        # 骰骰子決定風位（3-18隨機數字）
        dice_number = random.randint(3, 18)
        
        # 決定莊家（東風位）
        # 從莊家（位置0）開始數，數到dice_number的人就是東風
        # 注意：從1開始數，不是從0開始
        east_seat = (dice_number - 1) % 4
        
        # 設定各玩家的風位
        WIND_NAMES = ['東', '南', '西', '北']
        self.seat_winds = [0, 0, 0, 0]  # 初始都為0
        for i in range(4):
            self.seat_winds[(east_seat + i) % 4] = i  # 分配東南西北風位
        
        # 顯示骰子結果和風位分配
        wind_info = "\n".join([f"玩家 {i}: {WIND_NAMES[self.seat_winds[i]]}風" for i in range(4)])
        messagebox.showinfo("骰骰子決定風位", 
                          f"骰子點數: {dice_number}\n\n"
                          f"從莊家（玩家 0）開始數，數到玩家 {east_seat} 為東風\n\n"
                          f"數法：1=玩家0, 2=玩家1, 3=玩家2, 4=玩家3, 5=玩家0, 6=玩家1, 7=玩家2, 8=玩家3...\n\n"
                          f"風位分配:\n{wind_info}\n\n"
                          f"注意：只有對應到自己風位的風刻才有台數！")

        self.deck = [i//4 for i in range(136)]  # 136張牌
        random.shuffle(self.deck)

        self.hands = [[] for _ in range(4)]; self.exposed = [[] for _ in range(4)]
        self.flowers = [[] for _ in range(4)]; self.river = [[] for _ in range(4)]
        self.current_player = 0; self.dealer_index = 0; self.dealer_streak = 0
        self.kong_count = [0]*4; self.ankong_count = [0]*4
        self.kong_flower_event = [False]*4; 
        
        # 海底撈月計數器
        self.last_tile_count = 16  # 當牌堆剩16張時，下一張就是海底撈月
        self.is_last_tile = False  # 是否為最後一張牌
        
        # 風位追蹤系統
        self.round_wind = 0  # 圈風: 0=東, 1=南, 2=西, 3=北
        self.round_number = 1  # 第幾局 (1-4)
        self.winning_tile = None  # 胡的那張牌
        self.is_first_round = True  # 是否為第一輪（用於天胡地胡判定）
        
        # 天聽/地聽標記
        self.tenhou_checked = [False] * 4  # 標記是否已檢查過天聽
        self.chihou_checked = [False] * 4  # 標記是否已檢查過地聽
        self.is_tenhou = [False] * 4  # 是否為天聽
        self.is_chihou = [False] * 4  # 是否為地聽

        for i in range(4):
            for _ in range(16): self._draw(i, False)
        self._draw(0, True)
        
        # 檢查初始手牌是否為天聽/地聽
        self._check_tenhou_chihou()

        self.setup_ui(); self.refresh()
    
    def _check_tenhou_chihou(self):
        """檢查初始手牌是否為天聽/地聽
        
        天聽規則：
        - 莊家發完17張牌後，還沒出牌前就已經聽牌
        - 一旦天聽成立，如果胡牌就算天聽台數
        - 天聽後如果換牌（出牌）則失去天聽資格
        
        地聽規則：
        - 閒家發完16張牌後，還沒摸牌/出牌前就已經聽牌
        - 同樣規則，出牌後失去地聽資格
        """
        for i in range(4):
            if len(self.exposed[i]) == 0:  # 必須門清
                if i == self.dealer_index:
                    # 莊家：檢查17張手牌是否聽牌
                    # 需要移除一張牌測試（因為發完牌是17張）
                    waiting_tiles = count_waiting_tiles(self.hands[i][:-1], self.exposed[i])
                    if len(waiting_tiles) > 0:
                        self.is_tenhou[i] = True
                        self.tenhou_checked[i] = True
                else:
                    # 閒家：檢查16張手牌是否聽牌
                    waiting_tiles = count_waiting_tiles(self.hands[i], self.exposed[i])
                    if len(waiting_tiles) > 0:
                        self.is_chihou[i] = True
                        self.chihou_checked[i] = True

    def _draw(self, p_idx, count_draw=True, is_kong_draw=False):
        if not self.deck:
            messagebox.showinfo("流局", "牌堆已空。"); self.root.destroy(); return
        
        # 檢查是否為海底撈月（牌堆剩16張，抽第17張）
        if len(self.deck) <= self.last_tile_count:
            self.is_last_tile = True
        else:
            self.is_last_tile = False
            
        tile = self.deck.pop()
        self.hands[p_idx].append(tile); self.hands[p_idx].sort()
        self.kong_flower_event[p_idx] = is_kong_draw
        
        # 檢查天聽/地聽（第一次摸牌後）
        if count_draw and self.is_first_round and not self.tenhou_checked[p_idx] and not self.chihou_checked[p_idx]:
            if len(self.exposed[p_idx]) == 0:  # 必須門清
                hand_before_draw = self.hands[p_idx][:-1]  # 最後一張是剛摸的
                waiting_tiles = count_waiting_tiles(hand_before_draw, self.exposed[p_idx])
                if len(waiting_tiles) > 0:
                    if p_idx == self.dealer_index:
                        self.is_tenhou[p_idx] = True
                        self.tenhou_checked[p_idx] = True
                    else:
                        self.is_chihou[p_idx] = True
                        self.chihou_checked[p_idx] = True

    def setup_ui(self):
        self.top_frame = tk.Frame(self.root, bg="#2d5a27"); self.top_frame.pack(fill="x")
        
        # 左側按鈕區域
        btn_frame = tk.Frame(self.top_frame, bg="#2d5a27"); btn_frame.pack(side=tk.LEFT)
        self.hu_btn = tk.Button(btn_frame, text="胡牌", bg="#8b0000", fg="white", font=("微軟正黑體", 12, "bold"), command=lambda: self.on_hu_click(True))
        self.hu_btn.pack(side=tk.LEFT, padx=12, pady=10)
        self.kong_btn = tk.Button(btn_frame, text="槓", bg="#4b0082", fg="white", font=("微軟正黑體", 12, "bold"), command=self.on_kong_click)
        self.kong_btn.pack(side=tk.LEFT, padx=8, pady=10)
        
        # 右側資訊區域
        info_frame = tk.Frame(self.top_frame, bg="#2d5a27"); info_frame.pack(side=tk.RIGHT)
        
        # 剩餘牌數顯示
        self.deck_label = tk.Label(info_frame, text="", fg="#ff9900", bg="#2d5a27", font=("微軟正黑體", 12, "bold"))
        self.deck_label.pack(side=tk.RIGHT, padx=20)
        
        # 風位顯示
        self.wind_label = tk.Label(info_frame, text="", fg="#00ff00", bg="#2d5a27", font=("微軟正黑體", 12))
        self.wind_label.pack(side=tk.RIGHT, padx=10)
        
        # 當前玩家資訊
        self.info_label = tk.Label(info_frame, text="", fg="#ffcc00", bg="#2d5a27", font=("微軟正黑體", 12))
        self.info_label.pack(side=tk.RIGHT, padx=10)
        
        self.canvas = tk.Canvas(self.root, bg="#1a472a", height=180); self.canvas.pack(fill="x")
        WIND_NAMES = ['東', '南', '西', '北']
        self.p_frames = [tk.LabelFrame(self.root, text=f"玩家 {i} ({WIND_NAMES[self.seat_winds[i]]}風)", bg="#2d5a27", fg="white") for i in range(4)]
        for f in self.p_frames: f.pack(fill="x", padx=10, pady=5)

    def refresh(self):
        WIND_NAMES = ['東', '南', '西', '北']
        self.wind_label.config(text=f"【{WIND_NAMES[self.round_wind]}風圈】第{self.round_number}局")
        
        # 更新剩餘牌數顯示
        remaining = len(self.deck)
        deck_text = f"剩餘牌數: {remaining}張"
        if self.is_last_tile:
            deck_text += " 【海底牌】"
        elif remaining <= self.last_tile_count:
            deck_text += " 【接近海底】"
        self.deck_label.config(text=deck_text)
        
        self.canvas.delete("all")
        for p, tiles in enumerate(self.river):
            txt = f"P{p} 棄牌: " + " ".join([TILE_NAMES[t] for t in tiles[-10:]])
            self.canvas.create_text(50, 40 + p*30, text=txt, fill="#ccc", anchor="w")
        for i, frame in enumerate(self.p_frames):
            for w in frame.winfo_children(): w.destroy()
            h_sub = tk.Frame(frame, bg="#2d5a27"); h_sub.pack(side=tk.LEFT)
            for idx, t in enumerate(self.hands[i]):
                st = "normal" if i == self.current_player else "disabled"
                tk.Button(h_sub, text=TILE_NAMES[t], width=4, command=lambda p=i, c=idx: self.on_discard(p, c), state=st).pack(side=tk.LEFT, padx=1)
            i_sub = tk.Frame(frame, bg="#2d5a27"); i_sub.pack(side=tk.RIGHT, padx=10)
            for combo in self.exposed[i]:
                f = tk.Frame(i_sub, bg="#444"); f.pack(side=tk.LEFT, padx=2)
                for x in combo: tk.Label(f, text=TILE_NAMES[x], width=3, bg="#eee").pack(side=tk.LEFT)
        cp = self.current_player
        self.info_label.config(text=f"輪到玩家 {cp} | 手牌 {len([t for t in self.hands[cp] if t < 34])} 張")
        
        # 自摸檢查
        can_hu_self = MJLogic.is_hu(self.hands[cp], self.exposed[cp])
        self.hu_btn.config(state="normal" if can_hu_self else "disabled")
        self.kong_btn.config(state="normal" if self._can_kong_now(cp) else "disabled")

    def _can_kong_now(self, p_idx):
        pure = [t for t in self.hands[p_idx] if t < 34]; c = counts34(pure)
        if any(v == 4 for v in c): return True
        for combo in self.exposed[p_idx]:
            if len(combo) == 3 and combo[0] in pure: return True
        return False

    def on_discard(self, p_idx, t_idx):
        tile = self.hands[p_idx].pop(t_idx); self.river[p_idx].append(tile)
        self.kong_flower_event[p_idx] = False
        self.is_first_round = False  # 有人出牌後就不是第一輪了
        
        # 出牌後失去天聽/地聽資格（因為換牌了）
        self.is_tenhou[p_idx] = False
        self.is_chihou[p_idx] = False
        self.refresh()
        if not self.check_others_reaction(p_idx, tile):
            self.current_player = (p_idx + 1) % 4
            self._draw(self.current_player, True); self.refresh()

    def check_others_reaction(self, s_idx, tile):
        for i in range(4):
            if i == s_idx: continue
            # 檢查是否能胡這張牌（傳入胡的牌）
            if MJLogic.is_hu(self.hands[i], self.exposed[i], tile):
                if messagebox.askyesno("榮胡", f"玩家 {i} 要胡牌嗎？"):
                    self.hands[i].append(tile); self.current_player = i; 
                    self.on_hu_click(False, s_idx, tile); return True
            if self.hands[i].count(tile) == 3:
                if messagebox.askyesno("明槓", f"玩家 {i} 要明槓 {TILE_NAMES[tile]} 嗎？"):
                    for _ in range(3): self.hands[i].remove(tile)
                    self.exposed[i].append([tile]*4); self.kong_count[i] += 1
                    self.current_player = i; self._draw(i, True, True); self.refresh(); return True
            if self.hands[i].count(tile) >= 2:
                if messagebox.askyesno("碰", f"玩家 {i} 要碰 {TILE_NAMES[tile]} 嗎？"):
                    for _ in range(2): self.hands[i].remove(tile)
                    self.exposed[i].append([tile]*3); self.current_player = i; self.refresh(); return True
        next_p = (s_idx + 1) % 4
        if tile < 27:
            h = self.hands[next_p]
            tile_num = tile % 9
            combos = []
            
            if tile_num >= 2 and (tile-2) in h and (tile-1) in h:
                combos.append([tile-2, tile-1, tile])
            
            if tile_num >= 1 and tile_num <= 7 and (tile-1) in h and (tile+1) in h:
                combos.append([tile-1, tile, tile+1])
            
            if tile_num <= 6 and (tile+1) in h and (tile+2) in h:
                combos.append([tile, tile+1, tile+2])
            
            if combos:
                options_str = "\n".join([f"{i+1}. {TILE_NAMES[c[0]]} {TILE_NAMES[c[1]]} {TILE_NAMES[c[2]]}" for i, c in enumerate(combos)])
                result = simpledialog.askinteger(
                    "吃牌", 
                    f"玩家 {next_p} 可以吃 {TILE_NAMES[tile]}\n\n請選擇要吃的組合 (1-{len(combos)})，取消則不吃:\n\n{options_str}",
                    minvalue=1, maxvalue=len(combos)
                )
                if result is not None:
                    choice = combos[result - 1]
                    for t in choice: 
                        if t != tile: self.hands[next_p].remove(t)
                    self.exposed[next_p].append(sorted(choice)); self.current_player = next_p; self.refresh(); return True
        return False

    def on_kong_click(self):
        cp = self.current_player; pure = [t for t in self.hands[cp] if t < 34]; c = counts34(pure)
        target = next((t for t, v in enumerate(c) if v == 4), None)
        if target is not None:
            for _ in range(4): self.hands[cp].remove(target)
            self.exposed[cp].append([target]*4); self.ankong_count[cp] += 1
        else:
            for combo in self.exposed[cp]:
                if len(combo) == 3 and combo[0] in pure:
                    t = combo[0]; self.hands[cp].remove(t); combo.append(t); self.kong_count[cp] += 1; break
        self._draw(cp, True, True); self.refresh()

    def on_hu_click(self, is_zi_mo, shooter=None, winning_tile=None):
        cp = self.current_player
        pure_hand = [t for t in self.hands[cp] if t < 34]
        
        if winning_tile is None:
            if is_zi_mo and pure_hand:
                winning_tile = pure_hand[-1]
            elif not is_zi_mo:
                winning_tile = self.river[shooter][-1] if shooter is not None else None
        
        # 計算聽牌數（用於平胡和獨聽判斷）
        waiting_count = 0
        if winning_tile is not None:
            # 獲取胡牌前的手牌（移除一張胡的牌）
            hand_before_win = list(pure_hand)
            if winning_tile in hand_before_win:
                hand_before_win.remove(winning_tile)  # 只移除第一張
            
            # 計算聽牌數
            waiting = count_waiting_tiles(hand_before_win, self.exposed[cp], winning_tile)
            waiting_count = len(waiting)
        
        # 檢查是否為海底撈月（摸到最後一張牌胡牌）
        is_haidilao = self.is_last_tile and is_zi_mo
        
        # 計算台數（包含門清、風位和平胡判斷）
        tai, details = MJLogic.calculate_tai_star31_auto(
            pure_hand, self.exposed[cp], self.flowers[cp],
            is_zi_mo, cp==self.dealer_index, self.dealer_streak, 
            is_haidilao, self.kong_flower_event[cp], 
            self.kong_count[cp], self.ankong_count[cp],
            self.round_wind, self.seat_winds[cp], 
            winning_tile, waiting_count, self.is_first_round,
            self.is_tenhou[cp], self.is_chihou[cp]
        )
        
        WIND_NAMES = ['東', '南', '西', '北']
        wind_info = f"【{WIND_NAMES[self.round_wind]}風圈】玩家 {cp} ({WIND_NAMES[self.seat_winds[cp]]}風)"
        msg = f"{wind_info} {'自摸' if is_zi_mo else '榮胡'}！\n\n台數明細：\n" + "\n".join(details) + f"\n\n總計: {tai}台"
        messagebox.showinfo("胡牌結算", msg); self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    game = MahjongFinalPro(root)
    root.mainloop()