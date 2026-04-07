import numpy as np
import matplotlib.pyplot as plt
import string

class BattleShipSolver:
    def __init__(self, mapsize = 10):
        self.mapsize = mapsize
        
        self.ship_length  = {
            "Carrier": 5,
            "Battleship": 4,
            "Destroyer": 3,
            "Submarine": 3,
            "Patrol Boat": 2
        }
        self.ship_count = {
            "Carrier": 1,
            "Battleship": 1,
            "Destroyer": 1,
            "Submarine": 1,
            "Patrol Boat": 1
        }

        self.map = np.full((mapsize, mapsize), "Unknown", dtype=object)
        self.text_matrix = [[None for _ in range(mapsize)] for _ in range(mapsize)]

        self.fig, self.ax = plt.subplots(figsize=(10, 7))
        plt.subplots_adjust(left=0.05, right=0.6, top=0.85, bottom=0.1)

        countmap = np.zeros((self.mapsize, self.mapsize), dtype=float)
        self.im = self.ax.imshow(countmap, aspect = "equal")

        for i in range(self.mapsize):
            for j in range(self.mapsize):
                self.text_matrix[i][j] = self.ax.text(j, i, "", ha = "center", va = "center", color = "w")

        self._setup_axes()
        self._setup_table()

        self.fig.canvas.mpl_connect('button_press_event', self.onclick)

        self.update_display()
        plt.show()

    def _setup_axes(self):
        self.ax.set_xticks(np.arange(self.mapsize))
        self.ax.set_yticks(np.arange(self.mapsize))
        self.ax.set_xticklabels(string.ascii_uppercase[:self.mapsize])
        self.ax.set_yticklabels(range(1, self.mapsize + 1))
        # self.ax.grid(which='both', color='gray', linestyle='-', linewidth=1)
        self.ax.set_aspect('equal')

    def _setup_table(self):
        table_data = [[name, count, length] for name, count in self.ship_count.items() for length in [self.ship_length.get(name)]]
        self.the_table = self.ax.table(cellText=table_data,
                            colLabels=["Ship Type", "Count", "Length"],
                            loc='right',
                            cellLoc='center', bbox=[1.25, 0.3, 0.5, 0.5])
        self.the_table.auto_set_font_size(False)
        self.the_table.set_fontsize(9)

    def check_probabilities(self, length):
        counter = np.zeros((self.mapsize, self.mapsize), dtype=float)

        current_hits = np.where(self.map == "Hit")

        has_open_hits = len(current_hits[0]) > 0

        for i in range(self.mapsize):
            for j in range(self.mapsize):

                if j + length <= self.mapsize:
                    segement_coords = [(i, j+k) for k in range(length)]
                    segment_values = [self.map[i][j+k] for k in range(length)]

                    if "Water" not in segment_values and "Sunk" not in segment_values:
                        num_hits_in_segment = segment_values.count("Hit")

                        if has_open_hits:
                            if num_hits_in_segment > 0:
                                weight = 100 * num_hits_in_segment
                            else:
                                weight = 1
                        
                        else:
                            weight = 1

                        for r, c in segement_coords:
                            counter[r][c] += weight

                if i + length <= self.mapsize:
                    segement_coords = [(i+k, j) for k in range(length)]
                    segment_values = [self.map[i+k][j] for k in range(length)]

                    if "Water" not in segment_values and "Sunk" not in segment_values:
                        num_hits_in_segment = segment_values.count("Hit")

                        if has_open_hits:
                            if num_hits_in_segment > 0:
                                weight = 100 * num_hits_in_segment
                            else:
                                weight = 1
                        
                        else:
                            weight = 1

                        for r, c in segement_coords:
                            counter[r][c] += weight
        return counter
    
    def sink_ship(self, r, c):
        destroyed_ship_pos = [(r, c)]
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

        for dy, dx in directions:
            for step in range(1, self.mapsize):
                ny, nx = r + dy * step, c + dx * step

                if 0 <= ny < self.mapsize and 0 <= nx < self.mapsize and self.map[ny][nx] == "Hit":
                    destroyed_ship_pos.append((ny, nx))
                else:
                    break

        ship_len = len(destroyed_ship_pos)
        found_name = next((n for n, l in self.ship_length.items() if l == ship_len and self.ship_count[n] > 0), None)

        if found_name:
            for pr, pc in destroyed_ship_pos:
                self.map[pr][pc] = "Sunk"
                for dr in range(-1, 2):
                    for dc in range(-1, 2):
                        ar, ac = pr + dr, pc + dc
                        if 0 <= ar < self.mapsize and 0 <= ac < self.mapsize and (ar, ac) not in destroyed_ship_pos:
                            self.map[ar][ac] = "Water"
    
            self.ship_count[found_name] -= 1
            print(f"{found_name} sunk! Remaining: {sum(self.ship_count.values())} ships.")

    def update_display(self):
        # 1. Heatmap berechnen (Die eigentliche Logik des Solvers)
        countmap = np.zeros((self.mapsize, self.mapsize), dtype=float)
        for name, count in self.ship_count.items():
            if count > 0:
                countmap += self.check_probabilities(self.ship_length[name])

        # Heatmap an die Anzeige senden
        self.im.set_data(countmap)
        # Farbskala anpassen, damit sie nicht bei 0 stagniert
        max_val = np.max(countmap) if np.max(countmap) > 0 else 1
        self.im.set_clim(vmin=0, vmax=max_val)

        # 2. Tabelle updaten
        new_table_data = [[name, count, self.ship_length[name]] for name, count in self.ship_count.items()]
        for row_idx, row_data in enumerate(new_table_data):
            for col_idx, cell_data in enumerate(row_data):
                # +1 wegen Header-Row
                self.the_table._cells[(row_idx + 1, col_idx)].get_text().set_text(str(cell_data))

        # 3. Marker updaten (Nur Hit oder Water anzeigen)
        marker_map = {
            "Unknown": "", 
            "Hit": "x", 
            "Water": "o",
            "Sunk": "#"
        }

        for i in range(self.mapsize):
            for j in range(self.mapsize):
                state = self.map[i][j]
                self.text_matrix[i][j].set_text(marker_map.get(state, ""))

        self.fig.canvas.draw_idle()

    def onclick(self, event):
        if event.xdata is not None and event.ydata is not None:
            row, col = round(event.ydata), round(event.xdata)
            if not (0 <= row < self.mapsize and 0 <= col < self.mapsize):
                return
            if self.map[row][col] == "Unknown":
                if event.button == 1: # water
                    self.map[row][col] = "Water"
                elif event.button == 2: # hit sunk
                    self.map[row][col] = "Hit"
                    self.sink_ship(row, col)
                elif event.button == 3: # hit
                    self.map[row][col] = "Hit"
                self.update_display()

if __name__ == "__main__":
    solver = BattleShipSolver(mapsize=10)