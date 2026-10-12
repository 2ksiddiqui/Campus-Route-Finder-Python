
import heapq
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG = "#0B1220"
PANEL = "#131F32"
CARD = "#1C2C44"
INPUT = "#263852"
BLUE = "#3B82F6"
BLUE_HOVER = "#2563EB"
TEXT = "#F8FAFC"
MUTED = "#A3B4CA"
LINE = "#51627B"
GREEN = "#22C55E"
RED = "#EF4444"

BUILDINGS = [
    "Library", "Student Center", "Engineering Hall",
    "Science Building", "Recreation Center"
]

PATHS = [
    ("Library", "Student Center", 0.3),
    ("Library", "Science Building", 0.5),
    ("Student Center", "Engineering Hall", 0.4),
    ("Student Center", "Recreation Center", 0.6),
    ("Science Building", "Engineering Hall", 0.3),
    ("Science Building", "Recreation Center", 0.5),
    ("Engineering Hall", "Recreation Center", 0.4),
]

POSITIONS = {
    "Library": (120, 130),
    "Student Center": (350, 100),
    "Engineering Hall": (570, 210),
    "Science Building": (250, 330),
    "Recreation Center": (520, 390),
}


class CampusRouteFinder(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Campus Route Finder 2.0 | Python Edition")
        self.geometry("1250x820")
        self.minsize(950, 670)
        self.configure(fg_color=BG)

        self.graph = {name: [] for name in BUILDINGS}
        for first, second, distance in PATHS:
            self.graph[first].append((second, distance))
            self.graph[second].append((first, distance))

        self.route = []
        self.history = []
        self.hovered = None
        self.start_var = tk.StringVar(value="Library")
        self.end_var = tk.StringVar(value="Science Building")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.update_suggestions)

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.build_header()
        self.build_sidebar()
        self.build_map()
        self.build_results()
        self.update_suggestions()
        self.after(100, self.draw_map)

    def heading(self, parent, text, size=17):
        return ctk.CTkLabel(
            parent, text=text, text_color=TEXT,
            font=ctk.CTkFont(size=size, weight="bold")
        )

    def action_button(self, parent, text, command, primary=False):
        return ctk.CTkButton(
            parent, text=text, command=command, height=39,
            corner_radius=11, fg_color=BLUE if primary else INPUT,
            hover_color=BLUE_HOVER if primary else "#354B68",
            text_color=TEXT, font=ctk.CTkFont(size=13, weight="bold")
        )

    def build_header(self):
        header = ctk.CTkFrame(self, fg_color=BG, corner_radius=0, height=95)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20)
        header.grid_propagate(False)
        ctk.CTkLabel(
            header, text="◈  CAMPUS ROUTE FINDER 2.0",
            font=ctk.CTkFont(size=27, weight="bold"), text_color=TEXT
        ).pack(pady=(13, 2))
        ctk.CTkLabel(
            header, text="Smart campus navigation  •  Powered by Dijkstra's algorithm",
            font=ctk.CTkFont(size=12), text_color=MUTED
        ).pack()

    def build_sidebar(self):
        sidebar = ctk.CTkScrollableFrame(
            self, width=254, fg_color=PANEL, corner_radius=15,
            scrollbar_button_color="#344862"
        )
        sidebar.grid(row=1, column=0, sticky="nsew", padx=(18, 8), pady=(0, 10))
        sidebar.grid_columnconfigure(0, weight=1)

        self.heading(sidebar, "PLAN YOUR ROUTE", 19).pack(anchor="w", pady=(15, 17))
        ctk.CTkLabel(sidebar, text="SEARCH BUILDINGS", text_color=MUTED,
                     font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        self.search_entry = ctk.CTkEntry(
            sidebar, textvariable=self.search_var, height=39,
            placeholder_text="Type a building name...",
            fg_color=INPUT, border_width=0, corner_radius=10
        )
        self.search_entry.pack(fill="x", pady=(5, 6))
        self.suggestions = ctk.CTkFrame(sidebar, fg_color=PANEL)
        self.suggestions.pack(fill="x")
        self.action_button(sidebar, "Search Building", self.search_building).pack(
            fill="x", pady=(7, 22))

        ctk.CTkLabel(sidebar, text="STARTING LOCATION", text_color=MUTED,
                     font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        self.start_menu = ctk.CTkOptionMenu(
            sidebar, variable=self.start_var, values=BUILDINGS, height=39,
            fg_color=INPUT, button_color="#354B68",
            button_hover_color="#446083", corner_radius=10,
            dropdown_fg_color=PANEL, dropdown_hover_color=BLUE
        )
        self.start_menu.pack(fill="x", pady=(7, 18))

        ctk.CTkLabel(sidebar, text="DESTINATION", text_color=MUTED,
                     font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        self.end_menu = ctk.CTkOptionMenu(
            sidebar, variable=self.end_var, values=BUILDINGS, height=39,
            fg_color=INPUT, button_color="#354B68",
            button_hover_color="#446083", corner_radius=10,
            dropdown_fg_color=PANEL, dropdown_hover_color=BLUE
        )
        self.end_menu.pack(fill="x", pady=(7, 14))

        buttons = [
            ("⇅  Swap Locations", self.swap_locations, False),
            ("➜  Find Shortest Route", self.find_route, True),
            ("Reset", self.reset, False),
            ("Compare Routes", self.compare_routes, False),
            ("Clear History", self.clear_history, False),
            ("Export Route", self.export_route, False),
        ]
        for title, command, primary in buttons:
            self.action_button(sidebar, title, command, primary).pack(
                fill="x", pady=5)
        ctk.CTkLabel(
            sidebar, text="5 buildings  •  7 walking paths",
            text_color=MUTED, font=ctk.CTkFont(size=11)
        ).pack(pady=(18, 10))

    def build_map(self):
        frame = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=15)
        frame.grid(row=1, column=1, sticky="nsew", padx=(8, 18), pady=(0, 10))
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=20, pady=(14, 8))
        self.heading(top, "Interactive Campus Map", 17).pack(side="left")
        ctk.CTkLabel(top, text="HOVER + CLICK", text_color="#93C5FD",
                     fg_color=INPUT, corner_radius=9, width=110,
                     height=27, font=ctk.CTkFont(size=10, weight="bold")).pack(side="right")
        self.canvas = tk.Canvas(frame, bg=PANEL, highlightthickness=0, cursor="arrow")
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.canvas.bind("<Configure>", self.draw_map)
        self.canvas.bind("<Motion>", self.on_hover)
        self.canvas.bind("<Leave>", self.on_leave)
        self.canvas.bind("<Button-1>", self.on_map_click)
        self.hitboxes = {}

    def build_results(self):
        results = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=15, height=205)
        results.grid(row=2, column=0, columnspan=2, sticky="ew",
                     padx=18, pady=(0, 18))
        results.grid_propagate(False)
        results.grid_columnconfigure(0, weight=1)
        results.grid_columnconfigure(1, weight=1)

        top = ctk.CTkFrame(results, fg_color="transparent")
        top.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(12, 2))
        self.heading(top, "YOUR ROUTE SUMMARY", 17).pack(side="left")
        self.route_label = ctk.CTkLabel(
            results, text="Select two buildings to find the shortest route",
            text_color=TEXT, font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        self.route_label.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20)

        distance_card = ctk.CTkFrame(results, fg_color=CARD, corner_radius=10)
        distance_card.grid(row=2, column=0, sticky="ew", padx=(20, 7), pady=7)
        time_card = ctk.CTkFrame(results, fg_color=CARD, corner_radius=10)
        time_card.grid(row=2, column=1, sticky="ew", padx=(7, 20), pady=7)
        self.distance_label = ctk.CTkLabel(
            distance_card, text="DISTANCE    --", text_color=TEXT,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.distance_label.pack(pady=8)
        self.time_label = ctk.CTkLabel(
            time_card, text="WALKING TIME    --", text_color=TEXT,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.time_label.pack(pady=8)
        self.details = ctk.CTkLabel(
            results, text="Route breakdown and recent searches will appear here.",
            text_color=MUTED, anchor="w", justify="left",
            font=ctk.CTkFont(size=11)
        )
        self.details.grid(row=3, column=0, columnspan=2, sticky="ew", padx=20)
        self.history_label = ctk.CTkLabel(
            results, text="RECENT ROUTES: None yet", text_color=MUTED,
            anchor="w", font=ctk.CTkFont(size=11)
        )
        self.history_label.grid(row=4, column=0, columnspan=2, sticky="ew", padx=20)

    def update_suggestions(self, *_):
        if not hasattr(self, "suggestions"):
            return
        for widget in self.suggestions.winfo_children():
            widget.destroy()
        query = self.search_var.get().strip().lower()
        if not query:
            return
        for name in BUILDINGS:
            if query in name.lower():
                ctk.CTkButton(
                    self.suggestions, text=name, height=29, anchor="w",
                    fg_color=INPUT, hover_color="#354B68",
                    command=lambda n=name: self.choose_suggestion(n)
                ).pack(fill="x", pady=2)

    def choose_suggestion(self, name):
        self.end_var.set(name)
        self.search_var.set("")

    def search_building(self):
        query = self.search_var.get().strip().lower()
        if not query:
            messagebox.showinfo("Search", "Enter a building name first.")
            return
        match = next((name for name in BUILDINGS if query in name.lower()), None)
        if match:
            self.choose_suggestion(match)
            messagebox.showinfo("Building Found", f"Destination selected: {match}")
        else:
            messagebox.showwarning("Not Found", "No matching campus building found.")

    def swap_locations(self):
        first, second = self.start_var.get(), self.end_var.get()
        self.start_var.set(second)
        self.end_var.set(first)

    def shortest_path(self, start, end):
        distances = {name: float("inf") for name in BUILDINGS}
        previous = {}
        distances[start] = 0.0
        queue = [(0.0, start)]
        while queue:
            distance, current = heapq.heappop(queue)
            if distance > distances[current]:
                continue
            if current == end:
                break
            for neighbor, weight in self.graph[current]:
                new_distance = distance + weight
                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    previous[neighbor] = current
                    heapq.heappush(queue, (new_distance, neighbor))
        if distances[end] == float("inf"):
            return [], float("inf")
        route = []
        current = end
        while current is not None:
            route.append(current)
            current = previous.get(current)
        route.reverse()
        return route, distances[end]

    def find_route(self):
        start, end = self.start_var.get(), self.end_var.get()
        if start == end:
            messagebox.showwarning("Same Location", "Choose two different buildings.")
            return
        route, distance = self.shortest_path(start, end)
        if not route:
            messagebox.showerror("No Route", "These buildings are not connected.")
            return
        self.route = route
        self.history.append((route[:], distance))
        minutes = distance / 3 * 60
        self.route_label.configure(text="  →  ".join(route))
        self.distance_label.configure(text=f"DISTANCE    {distance:.2f} miles")
        self.time_label.configure(text=f"WALKING TIME    {minutes:.0f} minutes")
        breakdown = []
        for first, second in zip(route, route[1:]):
            segment = next(w for neighbor, w in self.graph[first] if neighbor == second)
            breakdown.append(f"{first} → {second}: {segment:.2f} mi")
        self.details.configure(text="ROUTE BREAKDOWN:  " + "   |   ".join(breakdown))
        self.update_history()
        self.draw_map()

    def update_history(self):
        if not self.history:
            self.history_label.configure(text="RECENT ROUTES: None yet")
            return
        recent = [" → ".join(route) for route, _ in self.history[-3:]]
        self.history_label.configure(text="RECENT ROUTES: " + "   |   ".join(recent))

    def reset(self):
        self.start_var.set("Library")
        self.end_var.set("Science Building")
        self.search_var.set("")
        self.route = []
        self.route_label.configure(text="Select two buildings to find the shortest route")
        self.distance_label.configure(text="DISTANCE    --")
        self.time_label.configure(text="WALKING TIME    --")
        self.details.configure(text="Route breakdown and recent searches will appear here.")
        self.draw_map()

    def clear_history(self):
        self.history.clear()
        self.update_history()
        messagebox.showinfo("History", "Route history cleared.")

    def compare_routes(self):
        if len(self.history) < 2:
            messagebox.showinfo("Compare Routes", "Find at least two routes first.")
            return
        (route1, distance1), (route2, distance2) = self.history[-2:]
        if abs(distance1 - distance2) < 1e-9:
            result = "Both routes have the same distance."
        elif distance1 < distance2:
            result = "Route 1 is shorter!"
        else:
            result = "Route 2 is shorter!"
        messagebox.showinfo(
            "Route Comparison",
            f"ROUTE 1: {' → '.join(route1)}\n"
            f"Distance: {distance1:.2f} mi | Time: {distance1 / 3 * 60:.0f} min\n\n"
            f"ROUTE 2: {' → '.join(route2)}\n"
            f"Distance: {distance2:.2f} mi | Time: {distance2 / 3 * 60:.0f} min\n\n{result}"
        )

    def export_route(self):
        if not self.route:
            messagebox.showinfo("Export Route", "Find a route before exporting.")
            return
        filename = filedialog.asksaveasfilename(
            title="Export Campus Route", defaultextension=".txt",
            initialfile="campus_route.txt",
            filetypes=[("Text files", "*.txt")]
        )
        if not filename:
            return
        route, distance = self.route, self.history[-1][1]
        try:
            with open(filename, "w", encoding="utf-8") as file:
                file.write("CAMPUS ROUTE FINDER 2.0\n")
                file.write("=" * 35 + "\n")
                file.write("Route: " + " -> ".join(route) + "\n")
                file.write(f"Distance: {distance:.2f} miles\n")
                file.write(f"Walking Time: {distance / 3 * 60:.0f} minutes\n")
                file.write("Algorithm: Dijkstra's Shortest Path\n\n")
                file.write("ROUTE BREAKDOWN\n")
                for first, second in zip(route, route[1:]):
                    weight = next(w for neighbor, w in self.graph[first] if neighbor == second)
                    file.write(f"{first} -> {second}: {weight:.2f} mi\n")
            messagebox.showinfo("Export Complete", "Route saved successfully!")
        except OSError as error:
            messagebox.showerror("Export Error", str(error))

    def map_transform(self):
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        scale = min((width - 35) / 720, (height - 35) / 490)
        scale = max(scale, 0.1)
        x_offset = (width - 690 * scale) / 2
        y_offset = (height - 480 * scale) / 2
        return scale, x_offset, y_offset

    def draw_map(self, _event=None):
        if not hasattr(self, "canvas"):
            return
        self.canvas.delete("all")
        scale, ox, oy = self.map_transform()
        self.hitboxes = {}
        active_edges = {
            frozenset((a, b)) for a, b in zip(self.route, self.route[1:])
        }
        for first, second, _ in PATHS:
            x1, y1 = POSITIONS[first]
            x2, y2 = POSITIONS[second]
            active = frozenset((first, second)) in active_edges
            self.canvas.create_line(
                ox + x1 * scale, oy + y1 * scale,
                ox + x2 * scale, oy + y2 * scale,
                fill=BLUE if active else LINE,
                width=5 if active else 2.5, capstyle=tk.ROUND
            )

        for name in BUILDINGS:
            x, y = POSITIONS[name]
            cx, cy = ox + x * scale, oy + y * scale
            half_w, half_h = 77 * scale, 29 * scale
            x1, y1, x2, y2 = cx-half_w, cy-half_h, cx+half_w, cy+half_h
            self.hitboxes[name] = (x1, y1, x2, y2)
            active = name in self.route
            fill = BLUE if active else ("#375B8E" if self.hovered == name else CARD)
            self.rounded_rect(x1, y1, x2, y2, 13 * scale,
                              fill=fill, outline="#7293BD" if active else LINE, width=2)
            self.canvas.create_text(
                cx, cy, text=name, fill=TEXT,
                font=("Segoe UI", max(8, int(12 * scale)), "bold")
            )
            if self.route and name in (self.route[0], self.route[-1]):
                is_start = name == self.route[0]
                tag = "START" if is_start else "END"
                color = GREEN if is_start else RED
                self.rounded_rect(cx - 31*scale, y1 - 30*scale,
                                  cx + 31*scale, y1 - 7*scale,
                                  7*scale, fill=color, outline=color)
                self.canvas.create_text(
                    cx, y1 - 18.5*scale, text=tag, fill="white",
                    font=("Segoe UI", max(7, int(10*scale)), "bold")
                )

    def rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        r = min(radius, (x2-x1)/2, (y2-y1)/2)
        points = [
            x1+r,y1, x2-r,y1, x2,y1, x2,y1+r,
            x2,y2-r, x2,y2, x2-r,y2, x1+r,y2,
            x1,y2, x1,y2-r, x1,y1+r, x1,y1
        ]
        self.canvas.create_polygon(points, smooth=True, splinesteps=12, **kwargs)

    def building_at(self, x, y):
        for name, (x1, y1, x2, y2) in self.hitboxes.items():
            if x1 <= x <= x2 and y1 <= y <= y2:
                return name
        return None

    def on_hover(self, event):
        building = self.building_at(event.x, event.y)
        self.canvas.configure(cursor="hand2" if building else "arrow")
        if building != self.hovered:
            self.hovered = building
            self.draw_map()

    def on_leave(self, _event):
        if self.hovered is not None:
            self.hovered = None
            self.draw_map()

    def on_map_click(self, event):
        building = self.building_at(event.x, event.y)
        if building:
            self.end_var.set(building)
            messagebox.showinfo("Destination Selected", f"Destination: {building}")


if __name__ == "__main__":
    app = CampusRouteFinder()
    app.mainloop()

        

    



        



                     








    