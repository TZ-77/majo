import tkinter as tk
from tkinter import messagebox
import random

# --- 基礎資料定義 ---
TILE_NAMES = [
    '1萬','2萬','3萬','4萬','5萬','6萬','7萬','8萬','9萬',
    '1筒','2筒','3筒','4筒','5筒','6筒','7筒','8筒','9筒',
    '1條','2條','3條','4條','5條','6條','7條','8條','9條',
    '東','南','西','北','中','發','白',
    '春','夏','秋','冬','梅','蘭','竹','菊'
]

class MJLogic:
    @staticmethod
    def is_hu(hand_indices, exposed_count):
        """16張麻將胡牌判定：手牌數量 + 副露組數*3 必須等於 17"""
        pure_hand = [t for t in hand_indices if t < 34]
        if (len(pure_hand) + exposed_count * 3) != 17:
            return False
            
        counts = [0] * 34
        for idx in pure_hand:
            counts[idx] += 1
            
        def can_decompose(c):
            first = next((i for i, v in enumerate(c) if v > 0), -1)
            if first == -1: return True
            # 1. 嘗試組成刻子
            if c[first] >= 3:
                c[first] -= 3
                if can_decompose(c): return True
                c[first] += 3
            # 2. 嘗試組成順子
            if first < 27 and first % 9 <= 6:
                if c[first+1] > 0 and c[first+2] > 0:
                    c[first] -= 1; c[first+1] -= 1; c[first+2] -= 1
                    if can_decompose(c): return True
                    c[first] += 1; c[first+1] += 1; c[first+2] += 1
            return False

        for i in range(34):
            if counts[i] >= 2:
                counts[i] -= 2
                if can_decompose(list(counts)): return True
                counts[i] += 2
        return False

    @staticmethod
    def calculate_tai(hand, exposed, flowers, is_zi_mo, is_dealer=False):
        """
        對照台灣 16 張麻將規則計算台數
        """
        # 合併所有牌進行分析
        all_tiles = hand + [t for combo in exposed for t in combo]
        counts = [0] * 34
        for t in all_tiles: counts[t] += 1
        
        tai = 0
        details = []

        # --- 基礎/環境台 ---
        if is_zi_mo:
            tai += 1; details.append("自摸 (1台)")
        if is_dealer:
            tai += 1; details.append("莊家 (1台)")
        if len(flowers) > 0:
            tai += len(flowers); details.append(f"花牌 ({len(flowers)}台)")
        if len(flowers) == 8:
            tai += 8; details.append("八仙過海 (8台)")

        # --- 字牌系列 (大四喜、大三元等) ---
        # 四喜判斷
        winds = [counts[27], counts[28], counts[29], counts[30]] # 東南西北
        if all(w >= 3 for w in winds):
            tai += 16; details.append("大四喜 (16台)")
        elif sum(1 for w in winds if w >= 3) == 3 and any(w >= 2 for w in winds):
            tai += 8; details.append("小四喜 (8台)")

        # 三元判斷
        dragons = [counts[31], counts[32], counts[33]] # 中發白
        if all(d >= 3 for d in dragons):
            tai += 8; details.append("大三元 (8台)")
        elif sum(1 for d in dragons if d >= 3) == 2 and any(d >= 2 for d in dragons):
            tai += 4; details.append("小三元 (4台)")

        # --- 顏色系列 ---
        has_wan = any(counts[0:9])
        has_tong = any(counts[9:18])
        has_tiao = any(counts[18:27])
        has_zi = any(counts[27:34])
        color_types = sum([has_wan, has_tong, has_tiao])

        if color_types == 0 and has_zi:
            tai += 16; details.append("字一色 (16台)")
        elif color_types == 1:
            if not has_zi:
                tai += 10; details.append("清一色 (10台)")
            else:
                tai += 4; details.append("混一色 (4台)")

        # --- 組合系列 ---
        hand_counts = [0] * 34
        for t in hand: hand_counts[t] += 1
        
        # 刻子統計
        triplets_in_hand = sum(1 for c in hand_counts if c >= 3)
        triplets_exposed = sum(1 for combo in exposed if combo[0] == combo[1])
        total_triplets = triplets_in_hand + triplets_exposed

        if total_triplets == 5:
            tai += 4; details.append("碰碰胡 (4台)")

        # 暗刻判定
        if triplets_in_hand == 5:
            tai += 8; details.append("五暗刻 (8台)")
        elif triplets_in_hand == 4:
            tai += 5; details.append("四暗刻 (5台)")
        elif triplets_in_hand == 3:
            tai += 2; details.append("三暗刻 (2台)")

        # 特殊
        if len(exposed) == 0:
            if not is_zi_mo:
                tai += 1; details.append("門清 (1台)")
            if len(flowers) == 0 and not has_zi and total_triplets == 0:
                # 簡易平胡判斷：無花無字無刻
                tai += 2; details.append("平胡 (2台)")

        if len(hand) == 2 and not is_zi_mo:
            tai += 2; details.append("全求人 (2台)")

        return max(1, tai), details

class MahjongFinalPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Python 16張麻將")
        self.root.geometry("1100x900")
        self.root.configure(bg="#1a472a")

        # 核心數據
        # 34種牌各4張 + 8張花牌
        self.deck = [i//4 for i in range(136)] + list(range(34, 42))
        random.shuffle(self.deck)
        
        self.hands = [[] for _ in range(4)]
        self.exposed = [[] for _ in range(4)] 
        self.flowers = [[] for _ in range(4)] 
        self.river = [[] for _ in range(4)]   
        self.current_player = 0
        
        # 初始發牌 (16張)
        for i in range(4):
            for _ in range(16): self._draw(i)
        self._draw(0) # 莊家抽第17張
        
        self.setup_ui()
        self.refresh()

    def _draw(self, p_idx):
        if not self.deck: 
            messagebox.showinfo("流局", "牌堆已空，遊戲結束。")
            self.root.destroy()
            return
        tile = self.deck.pop()
        if tile >= 34: # 花牌自動補花
            self.flowers[p_idx].append(tile)
            self._draw(p_idx)
        else:
            self.hands[p_idx].append(tile)
            self.hands[p_idx].sort()

    def setup_ui(self):
        self.top_frame = tk.Frame(self.root, bg="#2d5a27")
        self.top_frame.pack(fill="x")
        
        self.hu_btn = tk.Button(self.top_frame, text="胡牌/自摸", bg="#8b0000", fg="white", 
                                font=("微軟正黑體", 12, "bold"), state="disabled", command=self.on_hu_click)
        self.hu_btn.pack(side=tk.LEFT, padx=20, pady=10)
        
        self.info_label = tk.Label(self.top_frame, text="遊戲開始", fg="#ffcc00", bg="#2d5a27", font=("微軟正黑體", 12))
        self.info_label.pack(side=tk.RIGHT, padx=20)

        # 河道區 (簡單視覺化)
        self.canvas = tk.Canvas(self.root, bg="#1a472a", height=300, highlightthickness=0)
        self.canvas.pack(fill="x", padx=20, pady=10)

        # 玩家區
        self.p_frames = []
        for i in range(4):
            f = tk.LabelFrame(self.root, text=f" 玩家 {i} {'(莊家)' if i==0 else ''}", bg="#2d5a27", fg="white", font=("微軟正黑體", 10))
            f.pack(fill="x", padx=10, pady=5)
            self.p_frames.append(f)

    def draw_river(self):
        self.canvas.delete("all")
        # 簡化顯示：只顯示最後出的幾張牌在中央
        x_offset = 50
        self.canvas.create_text(x_offset, 50, text="棄牌區:", fill="white", font=("微軟正黑體", 10))
        for p, tiles in enumerate(self.river):
            last_tiles = tiles[-8:] # 只顯示最後8張
            txt = f"P{p}: " + " ".join([TILE_NAMES[t] for t in last_tiles])
            self.canvas.create_text(x_offset + 10, 80 + p*30, text=txt, fill="#ccc", anchor="w")

    def refresh(self):
        self.draw_river()
        for i, frame in enumerate(self.p_frames):
            for w in frame.winfo_children(): w.destroy()
            
            # 手牌容器
            hand_sub = tk.Frame(frame, bg="#2d5a27")
            hand_sub.pack(side=tk.LEFT, pady=5)
            
            for idx, t in enumerate(self.hands[i]):
                # 只有當前玩家可以點擊自己的牌
                btn_state = "normal" if i == self.current_player else "disabled"
                btn_bg = "#eee" if i == self.current_player else "#777"
                
                btn = tk.Button(hand_sub, text=TILE_NAMES[t], width=4, bg=btn_bg,
                               font=("Arial", 10, "bold"),
                               command=lambda p=i, c=idx: self.on_discard(p, c))
                btn.config(state=btn_state)
                btn.pack(side=tk.LEFT, padx=1)

            # 副露與花牌顯示
            info_sub = tk.Frame(frame, bg="#2d5a27")
            info_sub.pack(side=tk.RIGHT, padx=10)
            
            # 顯示副露 (吃碰的牌)
            for combo in self.exposed[i]:
                lbl_txt = "".join([TILE_NAMES[x] for x in combo])
                tk.Label(info_sub, text=f"【{lbl_txt}】", bg="#1e371f", fg="#00ff00", font=("微軟正黑體", 9, "bold")).pack(side=tk.LEFT, padx=2)
            
            # 顯示花牌
            if self.flowers[i]:
                f_txt = " ".join([TILE_NAMES[x] for x in self.flowers[i]])
                tk.Label(info_sub, text=f"花: {f_txt}", bg="#2d5a27", fg="#ff7f50", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

        # 自摸檢查
        cp = self.current_player
        if MJLogic.is_hu(self.hands[cp], len(self.exposed[cp])):
            self.hu_btn.config(state="normal", bg="red")
            self.info_label.config(text=f"玩家 {cp} 可以胡牌了！")
        else:
            self.hu_btn.config(state="disabled", bg="#8b0000")

    def on_discard(self, p_idx, t_idx):
        tile = self.hands[p_idx].pop(t_idx)
        self.river[p_idx].append(tile)
        self.info_label.config(text=f"玩家 {p_idx} 打出 {TILE_NAMES[tile]}")
        self.refresh()
        
        # 檢查他人是否可胡、碰、吃
        if not self.check_others_reaction(p_idx, tile):
            # 無人動作，輪到下一家抽牌
            self.current_player = (p_idx + 1) % 4
            self._draw(self.current_player)
            self.refresh()

    def check_others_reaction(self, shooter_idx, tile):
        # 1. 榮胡檢查 (優先順序最高)
        for i in range(4):
            if i == shooter_idx: continue
            if MJLogic.is_hu(self.hands[i] + [tile], len(self.exposed[i])):
                if messagebox.askyesno("榮胡！", f"玩家 {i} 要胡 玩家 {shooter_idx} 的 {TILE_NAMES[tile]} 嗎？"):
                    self.hands[i].append(tile)
                    self.current_player = i
                    self.on_hu_click(is_zi_mo=False)
                    return True

        # 2. 碰牌檢查
        for i in range(4):
            if i == shooter_idx: continue
            if self.hands[i].count(tile) >= 2:
                if messagebox.askyesno("碰", f"玩家 {i} 要碰 【{TILE_NAMES[tile]}】 嗎？"):
                    # 執行碰
                    for _ in range(2): self.hands[i].remove(tile)
                    self.exposed[i].append([tile, tile, tile])
                    self.river[shooter_idx].pop()
                    self.current_player = i
                    self.refresh()
                    return True

        # 3. 吃牌檢查 (僅限下家)
        next_p = (shooter_idx + 1) % 4
        if tile < 27: # 只有萬筒條可以吃
            h_set = set(self.hands[next_p])
            eat_combos = []
            if {tile-2, tile-1}.issubset(h_set) and (tile-2)//9 == tile//9: eat_combos.append([tile-2, tile-1])
            if {tile-1, tile+1}.issubset(h_set) and (tile-1)//9 == tile//9: eat_combos.append([tile-1, tile+1])
            if {tile+1, tile+2}.issubset(h_set) and (tile+2)//9 == tile//9: eat_combos.append([tile+1, tile+2])
            
            if eat_combos:
                if messagebox.askyesno("吃", f"玩家 {next_p} 要吃 【{TILE_NAMES[tile]}】 嗎？"):
                    combo = eat_combos[0] # 簡化：取第一種吃法
                    for t in combo: self.hands[next_p].remove(t)
                    self.exposed[next_p].append(sorted(combo + [tile]))
                    self.river[shooter_idx].pop()
                    self.current_player = next_p
                    self.refresh()
                    return True
        return False

    def on_hu_click(self, is_zi_mo=True):
        cp = self.current_player
        is_dealer = (cp == 0) # 莊家判定
        
        tai, details = MJLogic.calculate_tai(
            self.hands[cp], 
            self.exposed[cp], 
            self.flowers[cp], 
            is_zi_mo, 
            is_dealer
        )
        
        detail_msg = "\n".join(details)
        msg = f"玩家 {cp} 胡牌！\n類型：{'自摸' if is_zi_mo else '榮胡'}\n\n【台數明細】\n{detail_msg}\n\n總計：{tai} 台"
        
        messagebox.showinfo("胡牌結算", msg)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    game = MahjongFinalPro(root)
    root.mainloop()