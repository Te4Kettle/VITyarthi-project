"""
Project: VIT-Yarthi Student Grade Management System
Author: Anadi Rathore
Description: 
    A GUI-based application to manage student marks. 
    Features include:
    - CRUD operations (Add, Update, Delete)
    - Data visualization (Bar and Line charts)
    - CSV and PDF reporting
    - Auto-repair for corrupted JSON data files
    - Dark/Light mode toggle
"""

import json
import csv
import os
import math
import tempfile
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# plotting libraries
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# pdf generation libraries
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader
from PIL import Image

# --- Configuration Constants ---
LOGO_PATH = "/mnt/data/e0504538-8166-45e2-8ff5-de5ab1ec01e9.png"
DATA_FILE = "students.json"

# --- Helper Functions ---

def get_grade_letter(marks):
    """
    Returns the grade letter based on the specific ranges requested.
    Input should be a float.
    """
    try:
        val = float(marks)
    except (ValueError, TypeError):
        return 'N'  # Return N if data is garbage

    if val >= 90: return 'S'
    if val >= 80: return 'A'
    if val >= 70: return 'B'
    if val >= 60: return 'C'
    if val >= 50: return 'D'
    if val >= 40: return 'E'
    return 'N'  # Fail grade


# --- Data Management Class ---

class StudentBackend:
    """
    Handles all the file I/O operations. 
    It saves data to JSON and exports to CSV.
    """
    def __init__(self, filename=DATA_FILE):
        self.filename = filename
        self.students = {}  # Dictionary format: { "ROLL": {"name": "X", "marks": 90} }
        self.load_data()

    def load_data(self):
        """
        Loads data from the disk. 
        Includes 'Auto-Repair' logic for corrupted or old-format JSON files.
        """
        if not os.path.exists(self.filename):
            self.students = {}
            return

        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            # If the file is totally broken, start fresh
            self.students = {}
            return

        # Sanitize / Repair logic
        clean_data = {}
        for roll, info in raw_data.items():
            clean_roll = str(roll).upper().strip()
            
            # Check if it's the new dictionary format or old simple format
            if isinstance(info, dict):
                clean_name = str(info.get('name', 'UNKNOWN')).upper()
                try:
                    clean_marks = float(info.get('marks', 0))
                except ValueError:
                    clean_marks = 0.0
            else:
                # Attempt to rescue data from old format (Roll -> Marks)
                clean_name = "UNKNOWN"
                try:
                    clean_marks = float(info)
                except ValueError:
                    clean_marks = 0.0
            
            clean_data[clean_roll] = {"name": clean_name, "marks": clean_marks}

        self.students = clean_data
        
        # Save the repaired version back immediately to fix the file
        self.save_data()

    def save_data(self):
        """Saves current state to JSON."""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.students, f, indent=4, ensure_ascii=False)
        except IOError:
            print("Error: Could not save data to disk.")

    def upsert_student(self, roll, name, marks):
        """Adds or Updates a student."""
        self.students[str(roll).upper()] = {
            "name": str(name).upper(), 
            "marks": float(marks)
        }
        self.save_data()

    def remove_student(self, roll):
        """Deletes a student if they exist."""
        roll = str(roll).upper()
        if roll in self.students:
            del self.students[roll]
            self.save_data()

    def get_sorted_list(self, sort_by='Roll'):
        """Returns the dictionary sorted based on the user's choice."""
        items = self.students.items()
        
        if sort_by == 'Name':
            return dict(sorted(items, key=lambda x: x[1]['name']))
        elif sort_by == 'Marks':
            return dict(sorted(items, key=lambda x: x[1]['marks'], reverse=True))
        else:
            # Default to Roll number (try to sort numerically if possible)
            def roll_sorter(item):
                try: 
                    return int(item[0]) 
                except: 
                    return item[0]
            return dict(sorted(items, key=roll_sorter))

    def search_students(self, query):
        """Returns a set of Roll numbers matching the query."""
        if not query:
            return set(self.students.keys())
        
        q = query.lower()
        results = set()
        for roll, data in self.students.items():
            if q in roll.lower() or q in data['name'].lower():
                results.add(roll)
        return results

    def get_statistics(self):
        """Calculates basic class stats."""
        if not self.students:
            return {"total": 0, "max": 0, "min": 0, "avg": 0}
        
        mark_list = [s['marks'] for s in self.students.values()]
        return {
            "total": len(mark_list),
            "max": max(mark_list),
            "min": min(mark_list),
            "avg": sum(mark_list) / len(mark_list)
        }

    def export_to_csv(self, filepath):
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Rank", "Roll Number", "Name", "Marks", "Grade"])
                
                # Sort by marks for the CSV ranking
                ranked_students = sorted(self.students.items(), key=lambda x: x[1]['marks'], reverse=True)
                
                for rank, (roll, data) in enumerate(ranked_students, 1):
                    writer.writerow([
                        rank, 
                        roll, 
                        data['name'], 
                        data['marks'], 
                        get_grade_letter(data['marks'])
                    ])
            return True
        except Exception as e:
            return str(e)


# --- Main Application GUI ---

class GradeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VIT-Yarthi Student Grade Management System")
        self.root.geometry("1200x800")
        
        # Initialize Backend
        self.db = StudentBackend()
        
        # App State
        self.is_dark_mode = True  # Default to dark mode because it looks cooler
        self.chart_bars = []      # To store bar objects for hover effects
        self.chart_points = []    # To store line points for hover effects
        
        # Setup the UI
        self.setup_styles()
        self.create_widgets()
        
        # Load initial data
        self.refresh_dashboard()

    def setup_styles(self):
        """Defines the colors and fonts for the app."""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.apply_theme_colors()

    def apply_theme_colors(self):
        """Switches colors based on is_dark_mode."""
        if self.is_dark_mode:
            self.bg_color = '#121212'
            self.fg_color = '#ffffff'
            self.entry_bg = '#1e1e1e'
            self.btn_bg = '#333333'
            self.tree_bg = '#2d2d2d'
        else:
            self.bg_color = '#f0f0f0'
            self.fg_color = '#000000'
            self.entry_bg = '#ffffff'
            self.btn_bg = '#e0e0e0'
            self.tree_bg = '#ffffff'

        self.root.configure(bg=self.bg_color)
        
        # Configure TTK styles
        self.style.configure('TFrame', background=self.bg_color)
        self.style.configure('TLabel', background=self.bg_color, foreground=self.fg_color, font=('Segoe UI', 10))
        self.style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'))
        self.style.configure('TButton', background=self.btn_bg, foreground=self.fg_color, borderwidth=1)
        self.style.map('TButton', background=[('active', '#0078d7')]) # Blue highlight on hover
        
        self.style.configure('Treeview', 
                             background=self.tree_bg, 
                             foreground=self.fg_color, 
                             fieldbackground=self.tree_bg,
                             rowheight=25)
        self.style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'))
        
        # Redraw charts if they exist
        if hasattr(self, 'fig_line'):
            self.refresh_charts()

    def create_widgets(self):
        # Header Section
        header_frame = ttk.Frame(self.root)
        header_frame.pack(side='top', fill='x', padx=10, pady=10)
        ttk.Label(header_frame, text="VIT-Yarthi Grade Manager", style='Title.TLabel').pack(side='left')
        
        # --- Left Panel (Inputs) ---
        left_panel = tk.Frame(self.root, bg=self.bg_color, width=300)
        left_panel.pack(side='left', fill='y', padx=10, pady=10)
        
        # Input Fields
        ttk.Label(left_panel, text="Roll Number:").pack(anchor='w', pady=(5,0))
        self.var_roll = tk.StringVar()
        self.var_roll.trace("w", lambda *args: self.var_roll.set(self.var_roll.get().upper())) # Auto-Upper
        ttk.Entry(left_panel, textvariable=self.var_roll).pack(fill='x', pady=5)
        
        ttk.Label(left_panel, text="Name:").pack(anchor='w', pady=(5,0))
        self.var_name = tk.StringVar()
        self.var_name.trace("w", lambda *args: self.var_name.set(self.var_name.get().upper()))
        ttk.Entry(left_panel, textvariable=self.var_name).pack(fill='x', pady=5)
        
        ttk.Label(left_panel, text="Marks (0-100):").pack(anchor='w', pady=(5,0))
        self.var_marks = tk.StringVar()
        ttk.Entry(left_panel, textvariable=self.var_marks).pack(fill='x', pady=5)
        
        # Buttons
        btn_frame = tk.Frame(left_panel, bg=self.bg_color)
        btn_frame.pack(fill='x', pady=15)
        
        ttk.Button(btn_frame, text="Add / Update", command=self.action_add_update).pack(fill='x', pady=2)
        ttk.Button(btn_frame, text="Delete Student", command=self.action_delete).pack(fill='x', pady=2)
        ttk.Button(btn_frame, text="Clear Fields", command=self.clear_inputs).pack(fill='x', pady=2)
        
        # Search & Sort
        ttk.Separator(left_panel, orient='horizontal').pack(fill='x', pady=15)
        
        ttk.Label(left_panel, text="Search:").pack(anchor='w')
        self.var_search = tk.StringVar()
        self.var_search.trace("w", lambda *a: self.refresh_table()) # Live search
        ttk.Entry(left_panel, textvariable=self.var_search).pack(fill='x', pady=5)
        
        ttk.Label(left_panel, text="Sort By:").pack(anchor='w', pady=(5,0))
        self.var_sort = tk.StringVar(value='Roll')
        sort_menu = ttk.OptionMenu(left_panel, self.var_sort, 'Roll', 'Roll', 'Name', 'Marks', 
                                   command=lambda _: self.refresh_dashboard())
        sort_menu.pack(fill='x', pady=5)
        
        # Utility Buttons
        ttk.Separator(left_panel, orient='horizontal').pack(fill='x', pady=15)
        ttk.Button(left_panel, text="Export CSV", command=self.action_export_csv).pack(fill='x', pady=2)
        ttk.Button(left_panel, text="Generate PDF Report", command=self.action_generate_pdf).pack(fill='x', pady=2)
        ttk.Button(left_panel, text="Toggle Dark/Light", command=self.toggle_theme).pack(fill='x', pady=10)
        
        # Stats Display
        self.lbl_stats = ttk.Label(left_panel, text="Loading stats...", justify='left')
        self.lbl_stats.pack(side='bottom', anchor='w', pady=20)

        # --- Right Panel (Table + Charts) ---
        right_panel = tk.Frame(self.root, bg=self.bg_color)
        right_panel.pack(side='right', fill='both', expand=True, padx=10, pady=10)
        
        # Treeview (Table)
        columns = ('Roll', 'Name', 'Marks', 'Grade')
        self.tree = ttk.Treeview(right_panel, columns=columns, show='headings', height=6)
        
        for col in columns:
            self.tree.heading(col, text=col)
            width = 200 if col == 'Name' else 100
            self.tree.column(col, width=width, anchor='center')
            
        self.tree.pack(fill='x', pady=(0, 10))
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        
        # Charts Area
        chart_frame = tk.Frame(right_panel, bg=self.bg_color)
        chart_frame.pack(fill='both', expand=True)
        
        # Set up Matplotlib Figures
        self.setup_charts(chart_frame)

    def setup_charts(self, parent_frame):
        # Line Chart (Top)
        self.fig_line, self.ax_line = plt.subplots(figsize=(8, 2.5), dpi=100)
        self.canvas_line = FigureCanvasTkAgg(self.fig_line, master=parent_frame)
        self.canvas_line.get_tk_widget().pack(fill='both', expand=True, pady=(0, 5))
        
        # Bar Chart (Bottom)
        self.fig_bar, self.ax_bar = plt.subplots(figsize=(8, 2.5), dpi=100)
        self.canvas_bar = FigureCanvasTkAgg(self.fig_bar, master=parent_frame)
        self.canvas_bar.get_tk_widget().pack(fill='both', expand=True)

        # Connect Hover Events
        self.canvas_bar.mpl_connect("motion_notify_event", self.on_bar_hover)
        self.canvas_line.mpl_connect("motion_notify_event", self.on_line_hover)
        
        # Create the tooltip annotation (hidden by default)
        self.tooltip = self.ax_bar.annotate(
            "", xy=(0,0), xytext=(15, 15), textcoords="offset points",
            bbox=dict(boxstyle="round", fc="w"), arrowprops=dict(arrowstyle="->")
        )
        self.tooltip.set_visible(False)
        
        # Tooltip for line chart
        self.tooltip_line = self.ax_line.annotate(
            "", xy=(0,0), xytext=(15, 15), textcoords="offset points",
            bbox=dict(boxstyle="round", fc="w"), arrowprops=dict(arrowstyle="->")
        )
        self.tooltip_line.set_visible(False)

    # --- Logic & Actions ---

    def action_add_update(self):
        roll = self.var_roll.get().strip()
        name = self.var_name.get().strip()
        marks_str = self.var_marks.get().strip()
        
        if not roll or not name:
            messagebox.showwarning("Missing Info", "Please enter both Roll Number and Name.")
            return
            
        try:
            marks = float(marks_str)
            if not (0 <= marks <= 100): raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Marks", "Marks must be a number between 0 and 100.")
            return

        self.db.upsert_student(roll, name, marks)
        self.clear_inputs()
        self.refresh_dashboard()

    def action_delete(self):
        roll = self.var_roll.get().strip()
        if not roll:
            messagebox.showwarning("Wait...", "Please enter or select a Roll Number to delete.")
            return
            
        if messagebox.askyesno("Confirm", f"Are you sure you want to delete {roll}?"):
            self.db.remove_student(roll)
            self.clear_inputs()
            self.refresh_dashboard()

    def action_export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if path:
            result = self.db.export_to_csv(path)
            if result is True:
                messagebox.showinfo("Success", f"Data exported to {path}")
            else:
                messagebox.showerror("Error", f"Failed to export CSV: {result}")

    def on_tree_select(self, event):
        selected_items = self.tree.selection()
        if selected_items:
            values = self.tree.item(selected_items[0], "values")
            # Populate fields for editing
            self.var_roll.set(values[0])
            self.var_name.set(values[1])
            self.var_marks.set(values[2])

    def clear_inputs(self):
        self.var_roll.set("")
        self.var_name.set("")
        self.var_marks.set("")
        # Deselect tree item
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme_colors()
        self.refresh_dashboard()

    # --- Dashboard Updates (The heavy lifting) ---

    def refresh_dashboard(self):
        self.refresh_table()
        self.refresh_stats()
        self.refresh_charts()

    def refresh_table(self):
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Filter and Sort
        search_hits = self.db.search_students(self.var_search.get())
        sorted_data = self.db.get_sorted_list(self.var_sort.get())
        
        for roll, data in sorted_data.items():
            if roll in search_hits:
                self.tree.insert("", "end", values=(
                    roll, 
                    data['name'], 
                    data['marks'], 
                    get_grade_letter(data['marks'])
                ))

    def refresh_stats(self):
        s = self.db.get_statistics()
        text = (
            f"Total Students: {s['total']}\n"
            f"Highest Score: {s['max']}\n"
            f"Lowest Score: {s['min']}\n"
            f"Class Average: {s['avg']:.2f}\n\n"
            f"Author: Anadi Rathore"
        )
        self.lbl_stats.config(text=text)

    def refresh_charts(self):
        # Gather data in the correct sorted order
        sorted_data = self.db.get_sorted_list(self.var_sort.get())
        rolls = list(sorted_data.keys())
        names = [d['name'] for d in sorted_data.values()]
        marks = [d['marks'] for d in sorted_data.values()]
        
        # Define colors based on theme
        bg = '#121212' if self.is_dark_mode else '#ffffff'
        fg = 'white' if self.is_dark_mode else 'black'
        bar_color = '#ffa726' if self.is_dark_mode else '#ff9800'
        line_color = '#29b6f6' if self.is_dark_mode else '#039be5'

        # --- Draw Bar Chart ---
        self.ax_bar.clear()
        self.fig_bar.patch.set_facecolor(bg)
        self.ax_bar.set_facecolor(bg)
        self.ax_bar.tick_params(colors=fg)
        for spine in self.ax_bar.spines.values(): spine.set_color(fg)
        self.ax_bar.yaxis.label.set_color(fg)
        self.ax_bar.xaxis.label.set_color(fg)
        self.ax_bar.title.set_color(fg)

        if marks:
            x_pos = range(len(rolls))
            bars = self.ax_bar.bar(x_pos, marks, color=bar_color, width=0.6)
            
            # X-axis Labels (Roll + Name)
            labels = [f"{r}\n{n}" for r, n in zip(rolls, names)]
            self.ax_bar.set_xticks(x_pos)
            self.ax_bar.set_xticklabels(labels, rotation=0, fontsize=8)
            
            # Store bars for hover
            self.chart_bars = list(zip(bars, rolls, names, marks))
            
            # Add value on top of bars
            for rect in bars:
                h = rect.get_height()
                self.ax_bar.text(rect.get_x() + rect.get_width()/2., h + 1,
                                 f'{int(h)}', ha='center', va='bottom', color=fg, fontsize=8)
        
        self.ax_bar.set_title("Performance Overview (Bar Chart)")
        self.ax_bar.set_ylim(0, 110)
        self.canvas_bar.draw()

        # --- Draw Line Chart ---
        self.ax_line.clear()
        self.fig_line.patch.set_facecolor(bg)
        self.ax_line.set_facecolor(bg)
        self.ax_line.tick_params(colors=fg)
        for spine in self.ax_line.spines.values(): spine.set_color(fg)
        self.ax_line.yaxis.label.set_color(fg)
        self.ax_line.xaxis.label.set_color(fg)
        self.ax_line.title.set_color(fg)

        self.chart_points = []
        if marks:
            x_vals = range(len(marks))
            self.ax_line.plot(x_vals, marks, marker='o', color=line_color, linewidth=2)
            
            # Store points for hover detection
            for i, (r, n, m) in enumerate(zip(rolls, names, marks)):
                self.chart_points.append((i, m, r, n))

            self.ax_line.set_xticks(x_vals)
            self.ax_line.set_xticklabels(range(1, len(marks)+1)) # Just rank numbers
        
        self.ax_line.set_title("Marks Trend (Line Chart)")
        self.ax_line.set_ylim(0, 110)
        self.canvas_line.draw()

    # --- Hover Logic ---

    def on_bar_hover(self, event):
        """Shows a tooltip when hovering over a bar."""
        if event.inaxes != self.ax_bar:
            self.tooltip.set_visible(False)
            self.canvas_bar.draw_idle()
            return

        found = False
        for bar, roll, name, mark in self.chart_bars:
            if bar.contains(event)[0]:
                self.tooltip.xy = (bar.get_x() + bar.get_width() / 2, bar.get_height())
                text = f"{roll}: {name}\nMarks: {mark}"
                self.tooltip.set_text(text)
                self.tooltip.set_visible(True)
                self.canvas_bar.draw_idle()
                found = True
                break
        
        if not found and self.tooltip.get_visible():
            self.tooltip.set_visible(False)
            self.canvas_bar.draw_idle()

    def on_line_hover(self, event):
        """Shows a tooltip when hovering near a line point."""
        if event.inaxes != self.ax_line:
            self.tooltip_line.set_visible(False)
            self.canvas_line.draw_idle()
            return

        found = False
        # Simple proximity check
        for x, y, roll, name in self.chart_points:
            # We need to transform data coords to display coords to check distance pixels
            # But simpler approach: check if event.xdata is close to integer x
            if event.xdata is not None and abs(event.xdata - x) < 0.2 and abs(event.ydata - y) < 5:
                self.tooltip_line.xy = (x, y)
                self.tooltip_line.set_text(f"{roll}\n{y}")
                self.tooltip_line.set_visible(True)
                self.canvas_line.draw_idle()
                found = True
                break
        
        if not found and self.tooltip_line.get_visible():
            self.tooltip_line.set_visible(False)
            self.canvas_line.draw_idle()

    # --- PDF Generation ---

    def action_generate_pdf(self):
        save_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
        if not save_path:
            return

        # 1. Save charts as temporary images
        tmp_dir = tempfile.gettempdir()
        line_chart_path = os.path.join(tmp_dir, "temp_line.png")
        bar_chart_path = os.path.join(tmp_dir, "temp_bar.png")
        
        # Save with white background for PDF readability
        self.fig_line.savefig(line_chart_path, facecolor='white')
        self.fig_bar.savefig(bar_chart_path, facecolor='white')

        # 2. Setup PDF Canvas
        c = pdf_canvas.Canvas(save_path, pagesize=A4)
        width, height = A4
        
        # --- Page 1: Report & Table ---
        
        # Title
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, height - 50, "VIT-Yarthi Student Report")
        
        # Logo (Try/Except in case file is missing)
        try:
            if os.path.exists(LOGO_PATH):
                logo = ImageReader(LOGO_PATH)
                c.drawImage(logo, width - 120, height - 70, width=80, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass # Skip logo if it fails

        # Stats Block
        stats = self.db.get_statistics()
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 90, f"Total Students: {stats['total']}")
        c.drawString(50, height - 110, f"Class Average: {stats['avg']:.2f}")
        c.drawString(200, height - 90, f"Highest: {stats['max']}")
        c.drawString(200, height - 110, f"Lowest: {stats['min']}")

        # Table Header
        y_pos = height - 150
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, y_pos, "Rank")
        c.drawString(80, y_pos, "Roll Number")
        c.drawString(180, y_pos, "Name")
        c.drawString(380, y_pos, "Marks")
        c.drawString(450, y_pos, "Grade")
        c.line(40, y_pos - 5, 500, y_pos - 5)
        y_pos -= 25

        # Table Data
        c.setFont("Helvetica", 10)
        sorted_students = sorted(self.db.students.items(), key=lambda x: x[1]['marks'], reverse=True)
        
        for rank, (roll, data) in enumerate(sorted_students, 1):
            if y_pos < 50: # New Page if we run out of space
                c.showPage()
                y_pos = height - 50
            
            c.drawString(40, y_pos, str(rank))
            c.drawString(80, y_pos, str(roll))
            # Truncate long names
            name_display = data['name'][:30] + "..." if len(data['name']) > 30 else data['name']
            c.drawString(180, y_pos, name_display)
            c.drawString(380, y_pos, str(data['marks']))
            c.drawString(450, y_pos, get_grade_letter(data['marks']))
            y_pos -= 20

        c.showPage() # End of text page

        # --- Page 2: Charts ---
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "Visual Analysis")
        
        try:
            c.drawImage(ImageReader(line_chart_path), 50, height/2 + 20, width=500, height=300)
            c.drawImage(ImageReader(bar_chart_path), 50, 50, width=500, height=300)
        except Exception as e:
            c.drawString(50, height/2, f"Error loading charts: {e}")

        c.save()
        messagebox.showinfo("Done", "PDF Report generated successfully!")

if __name__ == "__main__":
    root = tk.Tk()
    # Optional: Set window icon if you have an .ico file
    # root.iconbitmap('icon.ico') 
    app = GradeApp(root)
    root.mainloop()
