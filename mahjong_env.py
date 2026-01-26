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
    for t in all_tiles:
        if t < 9: suits[0] = True
        elif t < 18: suits[1] = True
        elif t < 27: suits[2] = True
        elif t < 34: return False  # 有字牌就不是清一色
    return suits.count(True) == 1

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
    
    # 7. 檢查是否為單吊
    if is_dan_diao(pure_hand, winning_tile, exposed):
        return False
    
    # 8. 檢查手牌是否全部是順子（包含將牌）
    if pure_hand is not None and need_melds is not None:
        # 使用分解來檢查是否全是順子
        hand_for_decomposition = list(pure_hand)
        if winning_tile is not None:
            hand_for_decomposition.append(winning_tile)
        
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

def is_quan_qiu_ren(hand_tiles, exposed):
    """全求人: 手牌只剩一張(胡的那張)，全靠吃碰槓"""
    pure_hand = [t for t in hand_tiles if t < 34]
    return len(pure_hand) == 1 and len(exposed) == 5

def count_waiting_tiles(hand, exposed):
    """計算聽幾張牌 (用於獨聽判定)"""
    waiting = []
    for test_tile in range(34):
        # 檢查加入這張牌是否能胡
        if MJLogic.is_hu(hand, exposed, test_tile):
            waiting.append(test_tile)
    return waiting

def is_dan_diao(hand, winning_tile, exposed):
    """單吊: 胡牌那張剛好是將牌"""
    if winning_tile is None:
        return False
    
    # 單吊的定義：只聽一張牌，且那張牌是將牌
    # 先檢查是否只聽一張
    waiting = count_waiting_tiles(hand, exposed)
    if len(waiting) != 1:
        return False
    
    # 檢查是否只聽將牌
    if waiting[0] != winning_tile:
        return False
    
    # 單吊的特徵：將牌在手中只有一張（加上胡的那張變成兩張）
    pure_hand = [t for t in hand if t < 34]
    if pure_hand.count(winning_tile) == 1:
        return True
    
    return False

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
            # 順子
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
    def calculate_tai_star31_auto(pure_hand, exposed, flowers, is_zi_mo, is_dealer, streak, is_haidilao, is_kong_flower, m_kong, a_kong, round_wind=0, seat_wind=0, winning_tile=None, waiting_count=None, is_first_round=False):
        tai = 0; details = []
        all_tiles = list(pure_hand)
        for combo in exposed:
            for t in combo: 
                if t < 34: all_tiles.append(t)
        
        # pure_hand 已經包含 winning_tile (共17張)，不需要再加
        # all_tiles = pure_hand + exposed = 全部牌
        
        c_all = counts34(all_tiles)

        # 1. 莊家/連莊 (暫時註解)
        # if is_dealer:
        #     tai += 1; details.append("莊家 (1台)")
        #     if streak > 0:
        #         add = 2 * streak  # 連N拉N = 2N台
        #         tai += add; details.append(f"連{streak}拉{streak} ({add}台)")
        
        # 2. 天胡/地胡 (16台) - 第一輪自摸胡
        if is_first_round and is_zi_mo and len(exposed) == 0:
            if is_dealer:
                tai += 16; details.append("天胡 (16台)")
            else:
                tai += 16; details.append("地胡 (16台)")
        
        # 3. 事件台
        if is_zi_mo: tai += 1; details.append("自摸 (1台)")
        if len(exposed) == 0: tai += 1; details.append("門清 (1台)")
        if is_haidilao: tai += 1; details.append("海底撈月 (1台)")
        if is_kong_flower: tai += 1; details.append("槓上開花 (1台)")

        # 檢查是否為四喜系列和三元系列
        has_da_si_xi = is_da_si_xi(all_tiles, exposed)
        has_xiao_si_xi = is_xiao_si_xi(all_tiles, exposed)
        has_da_san_yuan = is_da_san_yuan(all_tiles, exposed)
        has_xiao_san_yuan = is_xiao_san_yuan(all_tiles, exposed)
        
        # 3. 風刻台 - 只有對應風位才有台數，但如果是四喜系列則不算
        if not (has_da_si_xi or has_xiao_si_xi):
            WIND_NAMES = ['東', '南', '西', '北']
            for w_idx in WINDS:
                if c_all[w_idx] >= 3:
                    wind_pos = w_idx - 27  # 0=東, 1=南, 2=西, 3=北
                    is_round = (wind_pos == round_wind)
                    is_seat = (wind_pos == seat_wind)
                    
                    if is_round or is_seat:
                        if is_round and is_seat:
                            tai += 2; details.append(f"{WIND_NAMES[wind_pos]}風刻 (圈風+門風 2台)")
                        elif is_round:
                            tai += 1; details.append(f"{WIND_NAMES[wind_pos]}風刻 (圈風 1台)")
                        elif is_seat:
                            tai += 1; details.append(f"{WIND_NAMES[wind_pos]}風刻 (門風 1台)")
        
        # 4. 三元牌刻 - 如果是三元系列則不單獨計算
        if not (has_da_san_yuan or has_xiao_san_yuan):
            for d_idx in DRAGONS:
                if c_all[d_idx] >= 3:
                    tai += 1; details.append(f"{TILE_NAMES[d_idx]}刻 (1台)")

        # 5. 槓台
        if m_kong > 0: tai += m_kong; details.append(f"明槓 ({m_kong}台)")
        if a_kong > 0: tai += (a_kong * 2); details.append(f"暗槓 ({a_kong*2}台)")

        # 6. 大牌型 - 檢查順序很重要
        need_m = 5 - len(exposed)
        
        # pure_hand 已經是17張牌，直接用於分解
        hand_for_decomposition = list(pure_hand)
        
        deco = MJLogic.find_one_decomposition_17(hand_for_decomposition, need_m)
        
        # 大四喜 (16台) - 最高優先級
        if has_da_si_xi:
            tai += 16; details.append("大四喜 (16台)")
        # 小四喜 (8台) - 次高優先級，且不是大四喜
        elif has_xiao_si_xi:
            tai += 8; details.append("小四喜 (8台)")
        
        # 大三元 (8台)
        if has_da_san_yuan:
            tai += 8; details.append("大三元 (8台)")
        # 小三元 (4台) - 且不是大三元
        elif has_xiao_san_yuan:
            tai += 4; details.append("小三元 (4台)")
        
        # 碰碰胡 (4台) - 如果不是四喜系列
        if deco:
            if all(m[0] == "pong" for m in deco[1]) and not any(len(x)==3 and x[0]!=x[1] for x in exposed):
                tai += 4; details.append("碰碰胡 (4台)")
        
        # 清一色 (8台)
        if is_qing_yi_se(all_tiles):
            tai += 8; details.append("清一色 (8台)")
        # 混一色 (4台) - 清一色和混一色互斥
        elif is_hun_yi_se(all_tiles):
            tai += 4; details.append("混一色 (4台)")
        
        # 平胡 (2台) - 嚴格判斷（包含單吊檢查）
        if is_ping_hu(all_tiles, exposed, flowers, is_zi_mo, waiting_count, winning_tile, pure_hand, need_m):
            tai += 2; details.append("平胡 (2台)")
        
        # 全求人 (2台)
        if is_quan_qiu_ren(pure_hand, exposed):
            tai += 2; details.append("全求人 (2台)")
        
        # 獨聽 (1台) - 只聽一張
        if waiting_count is not None:
            if waiting_count == 1:
                tai += 1; details.append("獨聽 (1台)")
        
        # 單吊 (1台) - 需要用胡牌前的手牌 (16張) 來判斷
        if winning_tile is not None:
            pure_hand_before_win = list(pure_hand)
            if winning_tile in pure_hand_before_win:
                pure_hand_before_win.remove(winning_tile)  # 移除一張 winning_tile
            if is_dan_diao(pure_hand_before_win, winning_tile, exposed):
                tai += 1; details.append("單吊 (1台)")
        
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

        self.deck = [i//4 for i in range(136)]
        random.shuffle(self.deck)

        self.hands = [[] for _ in range(4)]; self.exposed = [[] for _ in range(4)]
        self.flowers = [[] for _ in range(4)]; self.river = [[] for _ in range(4)]
        self.current_player = 0; self.dealer_index = 0; self.dealer_streak = 0
        self.kong_count = [0]*4; self.ankong_count = [0]*4
        self.kong_flower_event = [False]*4; self.last_draw_was_last_tile = False
        
        # 風位追蹤系統
        self.round_wind = 0  # 圈風: 0=東, 1=南, 2=西, 3=北
        self.round_number = 1  # 第幾局 (1-4)
        self.winning_tile = None  # 胡的那張牌
        self.is_first_round = True  # 是否為第一輪（用於天胡地胡判定）

        for i in range(4):
            for _ in range(16): self._draw(i, False)
        self._draw(0, True)

        self.setup_ui(); self.refresh()

    def _draw(self, p_idx, count_draw=True, is_kong_draw=False):
        if not self.deck:
            messagebox.showinfo("流局", "牌堆已空。"); self.root.destroy(); return
        self.last_draw_was_last_tile = (len(self.deck) == 1)
        tile = self.deck.pop()
        self.hands[p_idx].append(tile); self.hands[p_idx].sort()
        self.kong_flower_event[p_idx] = is_kong_draw

    def setup_ui(self):
        self.top_frame = tk.Frame(self.root, bg="#2d5a27"); self.top_frame.pack(fill="x")
        self.hu_btn = tk.Button(self.top_frame, text="胡牌", bg="#8b0000", fg="white", font=("微軟正黑體", 12, "bold"), command=lambda: self.on_hu_click(True))
        self.hu_btn.pack(side=tk.LEFT, padx=12, pady=10)
        self.kong_btn = tk.Button(self.top_frame, text="槓", bg="#4b0082", fg="white", font=("微軟正黑體", 12, "bold"), command=self.on_kong_click)
        self.kong_btn.pack(side=tk.LEFT, padx=8, pady=10)
        self.info_label = tk.Label(self.top_frame, text="", fg="#ffcc00", bg="#2d5a27", font=("微軟正黑體", 12))
        self.info_label.pack(side=tk.RIGHT, padx=20)
        # 風位顯示
        self.wind_label = tk.Label(self.top_frame, text="", fg="#00ff00", bg="#2d5a27", font=("微軟正黑體", 12))
        self.wind_label.pack(side=tk.RIGHT, padx=10)
        self.canvas = tk.Canvas(self.root, bg="#1a472a", height=180); self.canvas.pack(fill="x")
        WIND_NAMES = ['東', '南', '西', '北']
        self.p_frames = [tk.LabelFrame(self.root, text=f"玩家 {i} ({WIND_NAMES[self.seat_winds[i]]}風)", bg="#2d5a27", fg="white") for i in range(4)]
        for f in self.p_frames: f.pack(fill="x", padx=10, pady=5)

    def refresh(self):
        WIND_NAMES = ['東', '南', '西', '北']
        self.wind_label.config(text=f"【{WIND_NAMES[self.round_wind]}風圈】第{self.round_number}局")
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
                    self.hands[i].append(tile); self.current_player = i; self.on_hu_click(False, s_idx, tile); return True
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
            # 只移除一張 winning_tile，而不是所有相同的牌
            hand_before_win = list(pure_hand)
            if winning_tile in hand_before_win:
                hand_before_win.remove(winning_tile)  # 只移除第一個
            waiting = count_waiting_tiles(hand_before_win, self.exposed[cp])
            waiting_count = len(waiting)
        
        # 計算台數（包含門清、風位和平胡判斷）
        tai, details = MJLogic.calculate_tai_star31_auto(
            pure_hand, self.exposed[cp], self.flowers[cp],
            is_zi_mo, cp==self.dealer_index, self.dealer_streak, 
            self.last_draw_was_last_tile, self.kong_flower_event[cp], 
            self.kong_count[cp], self.ankong_count[cp],
            self.round_wind, self.seat_winds[cp], 
            winning_tile, waiting_count, self.is_first_round
        )
        
        WIND_NAMES = ['東', '南', '西', '北']
        wind_info = f"【{WIND_NAMES[self.round_wind]}風圈】玩家 {cp} ({WIND_NAMES[self.seat_winds[cp]]}風)"
        msg = f"{wind_info} {'自摸' if is_zi_mo else '榮胡'}！\n\n台數明細：\n" + "\n".join(details) + f"\n\n總計: {tai}台"
        messagebox.showinfo("胡牌結算", msg); self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    game = MahjongFinalPro(root)
    root.mainloop()