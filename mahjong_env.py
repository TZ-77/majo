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
# FLOWERS = range(34, 42); FLOWERS_SEASONS = {34, 35, 36, 37}; FLOWERS_PLANTS = {38, 39, 40, 41}  # 暫時停用花牌

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

def is_ping_hu(all_tiles, exposed, flowers=None):
    """平胡: 無字牌、無刻子(全順子+將)"""
    # if flowers: return False  # 有花不是平胡 (暫時停用花牌)
    for t in all_tiles:
        if t >= 27: return False  # 有字牌不是平胡
    # 檢查副露是否有碰/槓
    for combo in exposed:
        if len(combo) >= 3 and combo[0] == combo[1]:
            return False  # 有碰子/槓不是平胡
    return True

def is_quan_qiu_ren(hand_tiles, exposed):
    """全求人: 手牌只剩一張(胡的那張)，全靠吃碰槓"""
    pure_hand = [t for t in hand_tiles if t < 34]
    return len(pure_hand) == 1 and len(exposed) == 5

def count_waiting_tiles(hand, exposed):
    """計算聽幾張牌 (用於獨聽判定)"""
    waiting = []
    for test_tile in range(34):
        test_hand = hand + [test_tile]
        if MJLogic.is_hu(test_hand, exposed):
            waiting.append(test_tile)
    return waiting

def is_dan_diao(hand, winning_tile, exposed):
    """單吊: 胡牌那張剛好是將牌"""
    pure_hand = [t for t in hand if t < 34]
    need_melds = 5 - len(exposed)
    if len(pure_hand) != need_melds * 3 + 2:
        return False
    # 移除胡牌後剩餘應可組成完整面子
    test_hand = list(pure_hand)
    test_hand.remove(winning_tile)
    c = counts34(test_hand)
    
    def can_make_all_melds(cc, melds_left):
        if melds_left == 0: return all(v == 0 for v in cc)
        first = next((i for i, v in enumerate(cc) if v > 0), -1)
        if first == -1: return False
        if cc[first] >= 3:
            cc[first] -= 3
            if can_make_all_melds(cc, melds_left - 1): return True
            cc[first] += 3
        if first < 27 and first % 9 <= 6 and cc[first+1] > 0 and cc[first+2] > 0:
            cc[first] -= 1; cc[first+1] -= 1; cc[first+2] -= 1
            if can_make_all_melds(cc, melds_left - 1): return True
            cc[first] += 1; cc[first+1] += 1; cc[first+2] += 1
        return False
    
    # 檢查移除胡牌後能否組成 (need_melds-1)*3 + 2-1 = need_melds*3 + 1 - 3 = 不對
    # 單吊: 手牌去掉一張後剩 need_melds*3+1，若能組 need_melds 組面子且剩一張=胡牌
    if pure_hand.count(winning_tile) == 2:
        # 這張是將的一部分
        test_c = counts34(pure_hand)
        test_c[winning_tile] -= 2
        if can_make_all_melds(list(test_c), need_melds):
            return True
    return False

class MJLogic:
    @staticmethod
    def is_hu(hand_indices, exposed):
        """
        核心胡牌判定：面子補完法
        16張麻將需要 5 組面子 + 1 對將。
        暗牌張數必須剛好符合剩餘所需的結構：(5 - 已副露組數) * 3 + 2
        """
        pure_hand = [t for t in hand_indices if t < 34]
        exposed_count = len(exposed)
        need_melds = 5 - exposed_count
        
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
    def calculate_tai_star31_auto(pure_hand, exposed, flowers, is_zi_mo, is_dealer, streak, is_haidilao, is_kong_flower, m_kong, a_kong, round_wind=0, seat_wind=0, winning_tile=None):
        tai = 0; details = []
        all_tiles = list(pure_hand)
        for combo in exposed:
            for t in combo: 
                if t < 34: all_tiles.append(t)
        c_all = counts34(all_tiles)

        # 1. 莊家/連莊
        if is_dealer:
            tai += 1; details.append("莊家 (1台)")
            if streak > 0:
                add = 2 * streak + 1
                tai += add; details.append(f"連{streak}拉{streak} ({add}台)")
        
        # 2. 事件台
        if is_zi_mo: tai += 1; details.append("自摸 (1台)")
        if len(exposed) == 0: tai += 1; details.append("門清 (1台)")
        if is_haidilao: tai += 1; details.append("海底撈月 (1台)")
        if is_kong_flower: tai += 1; details.append("槓上開花 (1台)")

        # 3. 風刻台 - 圈風與門風
        WIND_NAMES = ['東', '南', '西', '北']
        for w_idx in WINDS:
            if c_all[w_idx] >= 3:
                wind_pos = w_idx - 27  # 0=東, 1=南, 2=西, 3=北
                is_round = (wind_pos == round_wind)
                is_seat = (wind_pos == seat_wind)
                if is_round and is_seat:
                    tai += 2; details.append(f"{WIND_NAMES[wind_pos]}風刻 (圈風+門風 2台)")
                elif is_round:
                    tai += 1; details.append(f"{WIND_NAMES[wind_pos]}風刻 (圈風 1台)")
                elif is_seat:
                    tai += 1; details.append(f"{WIND_NAMES[wind_pos]}風刻 (門風 1台)")
                else:
                    tai += 1; details.append(f"{WIND_NAMES[wind_pos]}風刻 (1台)")
        
        # 4. 三元牌刻
        for d_idx in DRAGONS:
            if c_all[d_idx] >= 3:
                tai += 1; details.append(f"{TILE_NAMES[d_idx]}刻 (1台)")

        # 5. 花牌台 (暫時停用)
        # if flowers:
        #     for f_idx in flowers:
        #         tai += 1; details.append(f"{TILE_NAMES[f_idx]} (1台)")
        #     f_set = set(flowers)
        #     if FLOWERS_SEASONS.issubset(f_set): tai += 2; details.append("春夏秋冬 (2台)")
        #     if FLOWERS_PLANTS.issubset(f_set): tai += 2; details.append("梅蘭竹菊 (2台)")

        # 6. 槓台
        if m_kong > 0: tai += m_kong; details.append(f"明槓 ({m_kong}台)")
        if a_kong > 0: tai += (a_kong * 2); details.append(f"暗槓 ({a_kong*2}台)")

        # 7. 大牌型
        need_m = 5 - len(exposed)
        deco = MJLogic.find_one_decomposition_17(pure_hand, need_m)
        
        # 碰碰胡 (4台)
        if deco:
            if all(m[0] == "pong" for m in deco[1]) and not any(len(x)==3 and x[0]!=x[1] for x in exposed):
                tai += 4; details.append("碰碰胡 (4台)")
        
        # 清一色 (8台)
        if is_qing_yi_se(all_tiles):
            tai += 8; details.append("清一色 (8台)")
        # 混一色 (4台) - 清一色和混一色互斥
        elif is_hun_yi_se(all_tiles):
            tai += 4; details.append("混一色 (4台)")
        
        # 平胡 (2台) - 無字無花全順子
        if is_ping_hu(all_tiles, exposed, flowers):
            # 還需確認暗牌也都是順子
            if deco:
                all_chow = all(m[0] == "chow" for m in deco[1])
                exposed_all_chow = all(len(x)==3 and x[0]!=x[1] for x in exposed) if exposed else True
                if all_chow and exposed_all_chow:
                    tai += 2; details.append("平胡 (2台)")
        
        # 全求人 (2台)
        if is_quan_qiu_ren(pure_hand, exposed):
            tai += 2; details.append("全求人 (2台)")
        
        # 獨聽 (1台) - 只聽一張
        # 需要在胡牌前計算聽牌，這裡用近似判斷
        hand_before_win = [t for t in pure_hand if t != winning_tile] if winning_tile is not None else pure_hand
        if winning_tile is not None:
            waiting = count_waiting_tiles(hand_before_win, exposed)
            if len(waiting) == 1:
                tai += 1; details.append("獨聽 (1台)")
        
        # 單吊 (1台)
        if winning_tile is not None and is_dan_diao(pure_hand, winning_tile, exposed):
            tai += 1; details.append("單吊 (1台)")
        
        return max(1, tai), details

class MahjongFinalPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Python 16張麻將")
        self.root.geometry("1160x920")
        self.root.configure(bg="#1a472a")

        self.deck = [i//4 for i in range(136)]  # + list(range(34, 42))  # 暫時停用花牌
        random.shuffle(self.deck)

        self.hands = [[] for _ in range(4)]; self.exposed = [[] for _ in range(4)]
        self.flowers = [[] for _ in range(4)]; self.river = [[] for _ in range(4)]
        self.current_player = 0; self.dealer_index = 0; self.dealer_streak = 0
        self.kong_count = [0]*4; self.ankong_count = [0]*4
        self.kong_flower_event = [False]*4; self.last_draw_was_last_tile = False
        
        # 風位追蹤系統
        self.round_wind = 0  # 圈風: 0=東, 1=南, 2=西, 3=北
        self.round_number = 1  # 第幾局 (1-4)
        self.seat_winds = [0, 1, 2, 3]  # 各玩家門風: P0=東, P1=南, P2=西, P3=北
        self.winning_tile = None  # 胡的那張牌

        for i in range(4):
            for _ in range(16): self._draw(i, False)
        self._draw(0, True)

        self.setup_ui(); self.refresh()

    def _draw(self, p_idx, count_draw=True, is_kong_draw=False):
        if not self.deck:
            messagebox.showinfo("流局", "牌堆已空。"); self.root.destroy(); return
        self.last_draw_was_last_tile = (len(self.deck) == 1)
        tile = self.deck.pop()
        # 暫時停用花牌處理
        # if tile >= 34:
        #     self.flowers[p_idx].append(tile); self._draw(p_idx, False, is_kong_draw)
        #     return
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
            # 暫時停用花牌顯示
            # if self.flowers[i]:
            #     f_txt = " ".join([TILE_NAMES[x] for x in self.flowers[i]])
            #     tk.Label(i_sub, text=f"花: {f_txt}", bg="#2d5a27", fg="#ff7f50", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        cp = self.current_player
        self.info_label.config(text=f"輪到玩家 {cp} | 手牌 {len([t for t in self.hands[cp] if t < 34])} 張")
        self.hu_btn.config(state="normal" if MJLogic.is_hu(self.hands[cp], self.exposed[cp]) else "disabled")
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
        self.refresh()
        if not self.check_others_reaction(p_idx, tile):
            self.current_player = (p_idx + 1) % 4
            self._draw(self.current_player, True); self.refresh()

    def check_others_reaction(self, s_idx, tile):
        for i in range(4):
            if i == s_idx: continue
            if MJLogic.is_hu(self.hands[i] + [tile], self.exposed[i]):
                if messagebox.askyesno("榮胡", f"玩家 {i} 要胡牌嗎？"):
                    self.hands[i].append(tile); self.current_player = i; self.on_hu_click(False, s_idx); return True
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
            h = self.hands[next_p]  # 用原始手牌列表，不是 set
            tile_suit = tile // 9  # 牌的花色 (0=萬, 1=筒, 2=條)
            tile_num = tile % 9    # 牌的數字 (0-8 對應 1-9)
            combos = []
            
            # 檢查 tile 作為順子最後一張 (tile-2, tile-1, tile) - 需要 tile 是 3 或更大
            if tile_num >= 2 and (tile-2) in h and (tile-1) in h:
                combos.append([tile-2, tile-1, tile])
            
            # 檢查 tile 作為順子中間一張 (tile-1, tile, tile+1) - 需要 tile 是 2~8
            if tile_num >= 1 and tile_num <= 7 and (tile-1) in h and (tile+1) in h:
                combos.append([tile-1, tile, tile+1])
            
            # 檢查 tile 作為順子第一張 (tile, tile+1, tile+2) - 需要 tile 是 7 或更小
            if tile_num <= 6 and (tile+1) in h and (tile+2) in h:
                combos.append([tile, tile+1, tile+2])
            
            if combos:
                # 直接顯示吃牌選項，讓玩家選擇（取消則不吃）
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
        # 取得胡的那張牌 (自摸時是最後摸的牌，榮胡時是別人打的牌)
        pure_hand = [t for t in self.hands[cp] if t < 34]
        if winning_tile is None and pure_hand:
            winning_tile = pure_hand[-1]  # 假設最後一張是胡的牌
        
        tai, details = MJLogic.calculate_tai_star31_auto(
            pure_hand, self.exposed[cp], self.flowers[cp],
            is_zi_mo, cp==self.dealer_index, self.dealer_streak, 
            self.last_draw_was_last_tile, self.kong_flower_event[cp], self.kong_count[cp], self.ankong_count[cp],
            self.round_wind, self.seat_winds[cp], winning_tile
        )
        WIND_NAMES = ['東', '南', '西', '北']
        wind_info = f"【{WIND_NAMES[self.round_wind]}風圈】玩家 {cp} ({WIND_NAMES[self.seat_winds[cp]]}風)"
        msg = f"{wind_info} {'自摸' if is_zi_mo else '榮胡'}！\n\n台數明細：\n" + "\n".join(details) + f"\n\n總計: {tai}台"
        messagebox.showinfo("胡牌結算", msg); self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk(); game = MahjongFinalPro(root); root.mainloop()