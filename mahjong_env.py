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

# --- 核心邏輯類別 ---
class MJLogic:
    @staticmethod
    def is_hu(hand_indices, exposed_count):
        """
        16張麻將胡牌判定：手牌數量 + 副露組數*3 必須等於 17
        """
        # 排除花牌
        pure_hand = [t for t in hand_indices if t < 34]
        # 總張數檢查 (隱藏手牌 + 已吃碰的牌)
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

        # 嘗試每一張牌當「將」
        for i in range(34):
            if counts[i] >= 2:
                counts[i] -= 2
                if can_decompose(list(counts)): return True
                counts[i] += 2
        return False

    @staticmethod
    def calculate_tai(hand, exposed, flowers, is_zi_mo):
        """台數簡單計算"""
        tai = 0
        if is_zi_mo: tai += 1  # 自摸 1 台
        tai += len(flowers)    # 每張花 1 台
        
        # 碰碰胡判定 (手牌全刻子)
        all_pure = [t for t in hand if t < 34]
        counts = [0] * 34
        for t in all_pure: counts[t] += 1
        # 刻子數 = 副露中的刻子 + 手牌中的刻子
        triplets = sum(1 for c in counts if c >= 3) + sum(1 for combo in exposed if combo[0] == combo[1])
        if triplets == 5: tai += 4 # 碰碰胡 4 台
        
        return max(1, tai)

class MahjongFinalPro:
    def __init__(self, root):
        self.root = root
        self.root.title("豪華版麻將 - 吃碰與胡牌結算系統")
        self.root.geometry("1100x950")
        self.root.configure(bg="#1a472a")

        # 核心數據
        self.deck = [i//4 for i in range(136)] + list(range(34, 42))
        random.shuffle(self.deck)
        self.hands = [[] for _ in range(4)]
        self.exposed = [[] for _ in range(4)] 
        self.flowers = [[] for _ in range(4)] 
        self.river = [[] for _ in range(4)]   
        self.current_player = 0
        
        # 初始發牌與自動補花
        for i in range(4):
            for _ in range(16): self._draw(i)
        self._draw(0) # 莊家第17張
        
        self.setup_ui()
        self.refresh()

    def _draw(self, p_idx):
        if not self.deck: return
        tile = self.deck.pop()
        if tile >= 34: 
            self.flowers[p_idx].append(tile)
            self._draw(p_idx)
        else:
            self.hands[p_idx].append(tile)
            self.hands[p_idx].sort()

    def setup_ui(self):
        # 頂部控制
        self.top_frame = tk.Frame(self.root, bg="#2d5a27")
        self.top_frame.pack(fill="x")
        
        self.hu_btn = tk.Button(self.top_frame, text="胡牌結算", bg="#8b0000", fg="white", 
                               font=("微軟正黑體", 12, "bold"), state="disabled", command=self.on_hu_click)
        self.hu_btn.pack(side=tk.LEFT, padx=20, pady=5)
        
        self.log_label = tk.Label(self.top_frame, text="遊戲開始", fg="#ffcc00", bg="#2d5a27", font=("微軟正黑體", 10))
        self.log_label.pack(side=tk.RIGHT, padx=20)

        # 中央河道
        self.canvas = tk.Canvas(self.root, bg="#1a472a", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=20, pady=10)

        # 玩家區
        self.p_frames = []
        for i in range(4):
            f = tk.LabelFrame(self.root, text=f" 玩家 {i} {'(你)' if i==0 else ''}", bg="#2d5a27", fg="white", font=("微軟正黑體", 10))
            f.pack(fill="x", padx=10, pady=2)
            self.p_frames.append(f)

    def draw_river(self):
        self.canvas.delete("all")
        centers = [(450, 500, 0, -32), (650, 350, 32, 0), (450, 150, 0, 32), (250, 350, -32, 0)]
        for p, tiles in enumerate(self.river):
            x, y, dx, dy = centers[p]
            for i, t in enumerate(tiles):
                r, c = divmod(i, 6)
                rx, ry = x + c*dx + r*(30 if dx==0 else 0), y + c*dy + r*(30 if dy==0 else 0)
                self.canvas.create_rectangle(rx-14, ry-18, rx+14, ry+18, fill="white", outline="#333")
                self.canvas.create_text(rx, ry, text=TILE_NAMES[t], font=("Arial", 8, "bold"))

    def refresh(self):
        self.draw_river()
        for i, frame in enumerate(self.p_frames):
            for w in frame.winfo_children(): w.destroy()
            
            # 手牌
            hand_sub = tk.Frame(frame, bg="#2d5a27")
            hand_sub.pack(side=tk.LEFT)
            for idx, t in enumerate(self.hands[i]):
                btn = tk.Button(hand_sub, text=TILE_NAMES[t], width=4, font=("Arial", 10, "bold"),
                               command=lambda p=i, c=idx: self.on_discard(p, c))
                if i != self.current_player: btn.config(state="disabled", bg="#555")
                btn.pack(side=tk.LEFT, padx=1)

            # 副露與花
            info_frame = tk.Frame(frame, bg="#2d5a27")
            info_frame.pack(side=tk.RIGHT, padx=10)
            for combo in self.exposed[i]:
                lbl_txt = "-".join([TILE_NAMES[x] for x in combo])
                tk.Label(info_frame, text=f"[{lbl_txt}]", bg="#1e371f", fg="#00ff00", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=2)
            f_txt = " ".join([TILE_NAMES[x] for x in self.flowers[i]])
            tk.Label(info_frame, text=f"花: {f_txt}", bg="#2d5a27", fg="#ff7f50", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

        # 檢查當前玩家是否可胡 (自摸)
        cp = self.current_player
        if MJLogic.is_hu(self.hands[cp], len(self.exposed[cp])):
            self.hu_btn.config(state="normal", bg="red")
            self.log_label.config(text=f"玩家 {cp} 可胡牌 (自摸)！")
        else:
            self.hu_btn.config(state="disabled", bg="#8b0000")

    def on_discard(self, p_idx, t_idx):
        tile = self.hands[p_idx].pop(t_idx)
        self.river[p_idx].append(tile)
        self.log_label.config(text=f"玩家 {p_idx} 打出 {TILE_NAMES[tile]}")
        self.refresh()
        
        # 檢查他人胡、碰、吃
        if not self.check_others_reaction(p_idx, tile):
            # 無人動作，換下一家摸牌
            self.current_player = (p_idx + 1) % 4
            self._draw(self.current_player)
            self.refresh()

    def check_others_reaction(self, shooter_idx, tile):
        # 1. 優先檢查所有人 胡 (榮胡)
        for i in range(4):
            if i == shooter_idx: continue
            if MJLogic.is_hu(self.hands[i] + [tile], len(self.exposed[i])):
                if messagebox.askyesno("榮胡！", f"玩家 {i} 要胡 玩家 {shooter_idx} 的 {TILE_NAMES[tile]} 嗎？"):
                    self.hands[i].append(tile)
                    self.current_player = i
                    self.on_hu_click(is_zi_mo=False)
                    return True

        # 2. 檢查碰
        for i in range(4):
            if i == shooter_idx: continue
            if self.hands[i].count(tile) >= 2:
                if messagebox.askyesno("碰！", f"玩家 {i} 要碰 【{TILE_NAMES[tile]}】 嗎？"):
                    self.execute_move(i, shooter_idx, tile, "PONG")
                    return True

        # 3. 檢查吃 (下家)
        next_p = (shooter_idx + 1) % 4
        eat_opts = []
        if tile < 27:
            h_set = set(self.hands[next_p])
            if {tile-2, tile-1}.issubset(h_set) and (tile-2)//9 == tile//9: eat_opts.append([tile-2, tile-1])
            if {tile-1, tile+1}.issubset(h_set) and (tile-1)//9 == tile//9 and (tile+1)//9 == tile//9: eat_opts.append([tile-1, tile+1])
            if {tile+1, tile+2}.issubset(h_set) and (tile+2)//9 == tile//9: eat_opts.append([tile+1, tile+2])
        
        if eat_opts:
            if messagebox.askyesno("吃！", f"玩家 {next_p} 要吃 【{TILE_NAMES[tile]}】 嗎？"):
                self.execute_move(next_p, shooter_idx, tile, "EAT", eat_opts[0])
                return True
        return False

    def execute_move(self, p_idx, shooter_idx, tile, move_type, combo_parts=None):
        if move_type == "PONG":
            for _ in range(2): self.hands[p_idx].remove(tile)
            self.exposed[p_idx].append([tile, tile, tile])
        elif move_type == "EAT":
            for t in combo_parts: self.hands[p_idx].remove(t)
            self.exposed[p_idx].append(sorted(combo_parts + [tile]))
        
        self.river[shooter_idx].pop() 
        self.current_player = p_idx
        self.refresh()

    def on_hu_click(self, is_zi_mo=True):
        cp = self.current_player
        if MJLogic.is_hu(self.hands[cp], len(self.exposed[cp])):
            tai = MJLogic.calculate_tai(self.hands[cp], self.exposed[cp], self.flowers[cp], is_zi_mo)
            msg = f"玩家 {cp} 胡牌！\n類型：{'自摸' if is_zi_mo else '榮胡'}\n總台數：{tai} 台"
            messagebox.showinfo("胡牌結算", msg)
            self.root.destroy()
        else:
            messagebox.showerror("錯誤", "牌型不符合胡牌條件！")

if __name__ == "__main__":
    root = tk.Tk()
    game = MahjongFinalPro(root)
    root.mainloop()