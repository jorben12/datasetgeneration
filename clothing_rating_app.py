import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import os
import csv
from datetime import datetime
import random
import torch
from torch import nn

class ClothingRatingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Clothing Rating and Outfit Designer")
        self.root.geometry("1000x800")
        
        # Paths
        self.image_folder = os.path.join(os.path.dirname(__file__), "TrainingPictures")
        self.output_folder = os.path.join(os.path.dirname(__file__), "output")
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Load tops and bottoms from separate folders
        self.tops_folder = os.path.join(self.image_folder, "Tops")
        self.bottoms_folder = os.path.join(self.image_folder, "Bottoms")
        
        # Get all clothing images from separate folders
        if os.path.exists(self.tops_folder):
            self.tops = sorted([f for f in os.listdir(self.tops_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        else:
            self.tops = []
        
        if os.path.exists(self.bottoms_folder):
            self.bottoms = sorted([f for f in os.listdir(self.bottoms_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        else:
            self.bottoms = []
        
        self.all_images = self.tops + self.bottoms
        
        # Current state
        self.current_mode = None
        self.current_image = None
        self.current_index = 0
        self.current_outfit = None
        
        # Rating scales
        self.characteristics = [
            ("Casual-Formal", "Casual", "Formal"),
            ("Minimal-Colorful", "Minimal", "Colorful"),
            ("Fitted-Oversized", "Fitted", "Oversized"),
            ("Feminine-Masculine", "Feminine", "Masculine"),
            ("Simple-Ornate", "Simple", "Ornate"),
            ("Cool-Warm", "Cool Weather", "Warm Weather")
        ]
        
        self.weather_scales = [
            ("Temperature", "5", "31"),
            ("Rain", "0", "100"),
            ("Cloud", "0", "100")
        ]
        
        self.scale_values = {}
        self.weather_values = {}
        self.clothing_ratings = {}
        self.selected_outfit = {"top": None, "bottom": None}
        self.randomized_weather = {}
        
        # Show mode selection
        self.show_mode_selection()
    
    def show_mode_selection(self):
        """Show the mode selection screen"""
        self.clear_window()
        
        frame = ttk.Frame(self.root, padding="20")
        frame.pack(expand=True)
        
        title = ttk.Label(frame, text="Clothing Rating and Outfit Designer", 
                         font=("Arial", 20, "bold"))
        title.pack(pady=20)
        
        subtitle = ttk.Label(frame, text="Select a mode:", 
                            font=("Arial", 14))
        subtitle.pack(pady=10)
        
        btn_mode1 = ttk.Button(frame, text="Mode 1: Rate Clothing Items", 
                              command=self.start_mode1, width=30)
        btn_mode1.pack(pady=10)
        
        btn_mode2 = ttk.Button(frame, text="Mode 2: Create Outfits", 
                              command=self.start_mode2, width=30)
        btn_mode2.pack(pady=10)
        
        btn_mode3 = ttk.Button(frame, text="Mode 3: Batch Rate by Name Pattern", 
                              command=self.start_mode3, width=30)
        btn_mode3.pack(pady=10)
        
        btn_mode4 = ttk.Button(frame, text="Mode 4: Evaluate AI Outfit Predictions", 
                              command=self.start_mode4, width=30)
        btn_mode4.pack(pady=10)
        
        btn_view_csv = ttk.Button(frame, text="View CSV Files", 
                                 command=self.view_csv_files, width=30)
        btn_view_csv.pack(pady=10)
    
    def start_mode1(self):
        """Start Mode 1: Rate individual clothing items"""
        self.load_clothing_ratings()
        self.current_mode = 1
        self.current_index = 0
        # Filter to only show unrated items
        unrated_items = [img for img in self.all_images if img not in self.clothing_ratings]
        if not unrated_items:
            messagebox.showinfo("All Rated", "All clothing items have been rated!")
            self.show_mode_selection()
            return
        self.all_images = unrated_items
        random.shuffle(self.all_images)
        self.show_rating_screen()
    
    def start_mode2(self):
        """Start Mode 2: Create outfits"""
        self.load_clothing_ratings()
        self.current_mode = 2
        self.generate_outfit()
        self.show_outfit_screen()
    
    def show_rating_screen(self):
        """Display a single clothing item with rating sliders"""
        if self.current_index >= len(self.all_images):
            messagebox.showinfo("Complete", "All items rated! Data saved to CSV.")
            self.show_mode_selection()
            return
        
        self.clear_window()
        
        # Image display
        image_name = self.all_images[self.current_index]
        
        # Determine which folder the image is in
        if image_name in self.tops:
            image_path = os.path.join(self.tops_folder, image_name)
        else:
            image_path = os.path.join(self.bottoms_folder, image_name)
        
        # Load and display image
        img = Image.open(image_path)
        img.thumbnail((400, 600), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Image frame
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, padx=10)
        
        label = ttk.Label(left_frame, text=f"Item {self.current_index + 1}/{len(self.all_images)}\n{image_name}",
                         font=("Arial", 10))
        label.pack()
        
        img_label = ttk.Label(left_frame, image=photo)
        img_label.image = photo
        img_label.pack()
        
        # Sliders frame
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, padx=20, fill=tk.BOTH, expand=True)
        
        scale_frame = ttk.LabelFrame(right_frame, text="Rate Characteristics (0-15)\n[Type #] [Enter=Next] [Space=Next Item] [R=Reset]", padding="10")
        scale_frame.pack(fill=tk.BOTH, expand=True)
        
        self.scale_values = {}
        self.current_slider_index = 0
        
        # Create entry field for direct input
        entry_frame = ttk.Frame(scale_frame)
        entry_frame.pack(fill=tk.X, pady=5)
        ttk.Label(entry_frame, text="Value:", font=("Arial", 9)).pack(side=tk.LEFT)
        self.value_entry = ttk.Entry(entry_frame, width=5, font=("Arial", 10))
        self.value_entry.pack(side=tk.LEFT, padx=5)
        self.value_entry.bind('<Return>', lambda e: self.set_value_from_entry())
        
        for idx, (char_name, left_label, right_label) in enumerate(self.characteristics):
            frame = ttk.Frame(scale_frame)
            frame.pack(fill=tk.X, pady=10)
            
            left = ttk.Label(frame, text=left_label, width=10, font=("Arial", 9))
            left.pack(side=tk.LEFT)
            
            scale = ttk.Scale(frame, from_=0, to=15, orient=tk.HORIZONTAL, 
                            command=lambda v, k=char_name: self.update_scale_value(k, v))
            
            # Load existing rating if available, otherwise use default 7
            initial_value = 7
            if image_name in self.clothing_ratings:
                existing_rating = self.clothing_ratings[image_name].get(char_name)
                if existing_rating:
                    try:
                        initial_value = int(round(float(existing_rating) * 15))
                    except (ValueError, TypeError):
                        pass
            
            scale.set(initial_value)
            scale.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
            
            right = ttk.Label(frame, text=right_label, width=10, font=("Arial", 9))
            right.pack(side=tk.LEFT)
            
            value_label = ttk.Label(frame, text=str(initial_value), width=3, font=("Arial", 9, "bold"))
            value_label.pack(side=tk.LEFT, padx=5)
            
            # Store with initial value (scale.set doesn't trigger callback)
            self.scale_values[char_name] = {"scale": scale, "label": value_label, "value": initial_value, "index": idx}
        
        # Highlight first slider and update entry field with initial value
        self.highlight_current_slider()
        # Set entry field to show first slider's value
        char_names = list(self.scale_values.keys())
        if char_names:
            first_value = self.scale_values[char_names[0]]["value"]
            self.value_entry.delete(0, tk.END)
            self.value_entry.insert(0, str(first_value))
        
        # Buttons frame
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        btn_next = ttk.Button(button_frame, text="Next Slider [Enter]", 
                             command=self.move_to_next_slider)
        btn_next.pack(side=tk.LEFT, padx=5)
        
        btn_save = ttk.Button(button_frame, text="Next Item [Space]", 
                             command=self.save_and_next_mode1)
        btn_save.pack(side=tk.LEFT, padx=5)
        
        btn_skip = ttk.Button(button_frame, text="Skip", 
                             command=self.skip_item_mode1)
        btn_skip.pack(side=tk.LEFT, padx=5)
        
        btn_back = ttk.Button(button_frame, text="Back to Menu", 
                             command=self.show_mode_selection)
        btn_back.pack(side=tk.LEFT, padx=5)
        
        # Bind keyboard shortcuts
        self.root.bind('<space>', lambda e: self.save_and_next_mode1())
        self.root.bind('<r>', lambda e: self.reset_current_slider())
        self.root.bind('<R>', lambda e: self.reset_current_slider())
        self.root.bind('<Up>', lambda e: self.move_to_prev_slider())
        self.root.bind('<Down>', lambda e: self.move_to_next_slider())
        self.root.bind('<Tab>', lambda e: self.move_to_next_slider())
    
    def skip_item_mode1(self):
        """Skip current item without rating"""
        self.current_index += 1
        self.show_rating_screen()
    
    def highlight_current_slider(self):
        """Highlight the current slider being adjusted"""
        char_names = list(self.scale_values.keys())
        if 0 <= self.current_slider_index < len(char_names):
            current_name = char_names[self.current_slider_index]
            self.scale_values[current_name]["scale"].focus()
    
    def move_to_next_slider(self):
        """Move to next slider (Tab key)"""
        self.current_slider_index = (self.current_slider_index + 1) % len(self.characteristics)
        self.highlight_current_slider()
        # Clear and focus entry field
        self.value_entry.delete(0, tk.END)
        self.value_entry.focus()
    
    def move_to_prev_slider(self):
        """Move to previous slider (Up key)"""
        self.current_slider_index = (self.current_slider_index - 1) % len(self.characteristics)
        self.highlight_current_slider()
    
    def reset_current_slider(self):
        """Reset current slider to middle value (7)"""
        char_names = list(self.scale_values.keys())
        if 0 <= self.current_slider_index < len(char_names):
            current_name = char_names[self.current_slider_index]
            self.scale_values[current_name]["scale"].set(7)
            self.update_scale_value(current_name, 7)
    
    def adjust_current_slider(self, direction):
        """Adjust current slider value with arrow keys"""
        char_names = list(self.scale_values.keys())
        if 0 <= self.current_slider_index < len(char_names):
            current_name = char_names[self.current_slider_index]
            current_val = self.scale_values[current_name]["value"]
            new_val = max(0, min(15, current_val + direction))
            self.scale_values[current_name]["scale"].set(new_val)
            self.update_scale_value(current_name, new_val)
            # Auto-move to next slider when at max (15)
            if new_val == 15 and direction > 0:
                self.move_to_next_slider()
    
    def update_scale_value(self, char_name, value):
        """Update scale value display"""
        self.scale_values[char_name]["value"] = int(float(value))
        self.scale_values[char_name]["label"].config(text=str(int(float(value))))
        # Update entry field to show current value
        self.value_entry.delete(0, tk.END)
        self.value_entry.insert(0, str(int(float(value))))
    
    def set_value_from_entry(self):
        """Set current slider value from entry field and move to next"""
        try:
            val = int(self.value_entry.get())
            val = max(0, min(15, val))  # Clamp between 0-15
            char_names = list(self.scale_values.keys())
            if 0 <= self.current_slider_index < len(char_names):
                current_name = char_names[self.current_slider_index]
                self.scale_values[current_name]["scale"].set(val)
                self.update_scale_value(current_name, val)
                self.move_to_next_slider()
        except ValueError:
            pass
    
    
    def save_and_next_mode1(self):
        """Save normalized ratings (0-1) and move to next item"""
        image_name = self.all_images[self.current_index]
        
        # Prepare row for CSV with normalized values (0 to 1)
        row = {"image": image_name}
        for char_name in self.scale_values:
            val = self.scale_values[char_name]["value"]
            row[char_name] = round(val / 15.0, 4)  # Normalize
        
        # Save to CSV
        csv_path = os.path.join(self.output_folder, "clothing_ratings.csv")
        fieldnames = ["image"] + [name for name, _, _ in self.characteristics]
        
        file_exists = os.path.isfile(csv_path)
        with open(csv_path, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
        
        self.current_index += 1
        self.show_rating_screen()
    
    def load_clothing_ratings(self):
        """Load clothing ratings from CSV to access characteristics"""
        self.clothing_ratings = {}
        csv_path = os.path.join(self.output_folder, "clothing_ratings.csv")
        if os.path.exists(csv_path):
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    image_name = row['image']
                    self.clothing_ratings[image_name] = row
    
    def generate_outfit(self):
        """Generate a random outfit (1 set of 5 tops and 5 bottoms) and logical weather"""
        
        # Filter to only rated items
        rated_tops = [t for t in self.tops if t in self.clothing_ratings]
        rated_bottoms = [b for b in self.bottoms if b in self.clothing_ratings]
        
        num_tops = min(5, len(rated_tops))
        num_bottoms = min(5, len(rated_bottoms))
        
        if num_tops == 0 or num_bottoms == 0:
            messagebox.showwarning("No Rated Items", "Not enough rated clothing items to create an outfit. Please rate items first in Mode 1.")
            self.show_mode_selection()
            return
        
        self.current_outfit = {
            "tops": random.sample(rated_tops, num_tops) if num_tops > 0 else [],
            "bottoms": random.sample(rated_bottoms, num_bottoms) if num_bottoms > 0 else []
        }
        
        # Logical randomized weather
        temp = random.randint(5, 31)
        
        if temp >= 28:
            cloud = random.randint(0, 35)
        elif temp <= 15:
            cloud = random.randint(40, 100)
        else:
            cloud = random.randint(10, 80)
            
        if cloud >= 70:
            rain = random.randint(40, 100)
        elif cloud >= 30:
            rain = random.randint(0, 40)
        else:
            rain = random.randint(0, 5)
        
        self.randomized_weather = {
            "Temperature": temp,
            "Rain": rain,
            "Cloud": cloud
        }
        
        self.selected_outfit = {
            "top": None,
            "bottom": None
        }
    
    def show_outfit_screen(self):
        """Display outfit creation screen"""
        self.clear_window()
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        title = ttk.Label(main_frame, text="Create an Outfit", font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        selected_frame = ttk.LabelFrame(main_frame, text="Selected Outfit", padding="10")
        selected_frame.pack(fill=tk.X, pady=10)
        
        selected_content = ttk.Frame(selected_frame)
        selected_content.pack(fill=tk.BOTH, expand=True)
        
        # Selected top
        top_frame = ttk.Frame(selected_content)
        top_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(top_frame, text="Top:", font=("Arial", 10, "bold")).pack()
        self.selected_top_label = ttk.Label(top_frame, text="(Click to select)", font=("Arial", 9, "italic"))
        self.selected_top_label.pack()
        self.selected_top_info = ttk.Label(top_frame, text="", font=("Arial", 8))
        self.selected_top_info.pack(padx=5, pady=5)
        
        # Selected bottom
        bottom_frame = ttk.Frame(selected_content)
        bottom_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(bottom_frame, text="Bottom:", font=("Arial", 10, "bold")).pack()
        self.selected_bottom_label = ttk.Label(bottom_frame, text="(Click to select)", font=("Arial", 9, "italic"))
        self.selected_bottom_label.pack()
        self.selected_bottom_info = ttk.Label(bottom_frame, text="", font=("Arial", 8))
        self.selected_bottom_info.pack(padx=5, pady=5)
        
        # Weather display
        weather_frame = ttk.Frame(selected_content)
        weather_frame.pack(side=tk.RIGHT, padx=20)
        
        ttk.Label(weather_frame, text="Weather Conditions:", font=("Arial", 10, "bold")).pack()
        for weather_name, min_val, max_val in self.weather_scales:
            w_display = ttk.Frame(weather_frame)
            w_display.pack(fill=tk.X, pady=3)
            ttk.Label(w_display, text=f"{weather_name}: {self.randomized_weather[weather_name]}°" if weather_name == "Temperature" else f"{weather_name}: {self.randomized_weather[weather_name]}%", 
                     font=("Arial", 9)).pack()
        
        title2 = ttk.Label(main_frame, text="Select a top and bottom:", font=("Arial", 10))
        title2.pack(pady=10)
        
        image_frame = ttk.Frame(main_frame)
        image_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        options_frame = ttk.LabelFrame(image_frame, text="Available Items", padding="10")
        options_frame.pack(fill=tk.BOTH, expand=True)
        
        tops_frame = ttk.Frame(options_frame)
        tops_frame.pack(fill=tk.X, pady=5)
        ttk.Label(tops_frame, text="Tops:", font=("Arial", 10, "bold")).pack()
        
        self.outfit_image_refs = {}
        for idx, top in enumerate(self.current_outfit["tops"]):
            self.display_outfit_image(tops_frame, top, "top", idx)
        
        bottoms_frame = ttk.Frame(options_frame)
        bottoms_frame.pack(fill=tk.X, pady=5)
        ttk.Label(bottoms_frame, text="Bottoms:", font=("Arial", 10, "bold")).pack()
        
        for idx, bottom in enumerate(self.current_outfit["bottoms"]):
            self.display_outfit_image(bottoms_frame, bottom, "bottom", idx)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        btn_auto = ttk.Button(button_frame, text="Auto-Select & Rate [A]", 
                             command=self.auto_select_outfit)
        btn_auto.pack(side=tk.LEFT, padx=5)
        
        btn_save = ttk.Button(button_frame, text="Select & Rate Outfit [Enter]", 
                             command=self.save_outfit)
        btn_save.pack(side=tk.LEFT, padx=5)
        
        btn_new = ttk.Button(button_frame, text="Roll New [Space]", 
                            command=lambda: (self.generate_outfit(), self.show_outfit_screen()))
        btn_new.pack(side=tk.LEFT, padx=5)
        
        btn_back = ttk.Button(button_frame, text="Back to Menu", 
                             command=self.show_mode_selection)
        btn_back.pack(side=tk.LEFT, padx=5)
        
        # Bind keyboard shortcuts
        self.root.bind('<a>', lambda e: self.auto_select_outfit())
        self.root.bind('<A>', lambda e: self.auto_select_outfit())
        self.root.bind('<Return>', lambda e: self.save_outfit())
        self.root.bind('<space>', lambda e: (self.generate_outfit(), self.show_outfit_screen()))
    
    def display_outfit_image(self, parent, image_name, clothing_type, idx):
        """Display a clickable outfit image"""
        if clothing_type == "top":
            image_path = os.path.join(self.tops_folder, image_name)
        else:
            image_path = os.path.join(self.bottoms_folder, image_name)
        
        img = Image.open(image_path)
        img.thumbnail((150, 200), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        
        frame = ttk.Frame(parent, relief=tk.RAISED, borderwidth=2)
        frame.pack(side=tk.LEFT, padx=5)
        
        def on_click(e, item=image_name, c_type=clothing_type):
            self.select_outfit_item(item, c_type)
        
        label = tk.Label(frame, image=photo, cursor="hand2")
        label.image = photo
        label.pack()
        label.bind("<Button-1>", on_click)
        
        name_label = ttk.Label(frame, text=image_name[:12] + "...", font=("Arial", 7))
        name_label.pack()
        
        self.outfit_image_refs[image_name] = photo
    
    def get_ui_display_text(self, ratings):
        """Convert normalized CSV ratings (0-1) back to UI scale (0-15) for display"""
        lines = []
        for name, _, _ in self.characteristics[:3]:
            val = ratings.get(name, 'N/A')
            if val != 'N/A':
                try:
                    # Convert 0.0-1.0 back to 0-15 integer for display
                    val = str(int(round(float(val) * 15)))
                except ValueError:
                    pass
            lines.append(f"{name.split('-')[0]}: {val}")
        return "\n".join(lines)
    
    def auto_select_outfit(self):
        """Auto-select the first top and bottom without manual selection"""
        if self.current_outfit["tops"] and self.current_outfit["bottoms"]:
            self.selected_outfit["top"] = self.current_outfit["tops"][0]
            self.selected_outfit["bottom"] = self.current_outfit["bottoms"][0]
            self.show_outfit_rating_screen()
    
    def select_outfit_item(self, image_name, clothing_type):
        """Select a top or bottom for the outfit"""
        self.selected_outfit[clothing_type] = image_name
        
        if clothing_type == "top":
            self.selected_top_label.config(text=image_name)
            if image_name in self.clothing_ratings:
                self.selected_top_info.config(text=self.get_ui_display_text(self.clothing_ratings[image_name]))
            else:
                self.selected_top_info.config(text="No ratings data")
        else:
            self.selected_bottom_label.config(text=image_name)
            if image_name in self.clothing_ratings:
                self.selected_bottom_info.config(text=self.get_ui_display_text(self.clothing_ratings[image_name]))
            else:
                self.selected_bottom_info.config(text="No ratings data")
    
    def save_outfit(self):
        """Trigger rating screen before saving outfit configuration"""
        if not self.selected_outfit["top"] or not self.selected_outfit["bottom"]:
            messagebox.showwarning("Selection Required", "Please select both a top and bottom!")
            return
        
        self.show_outfit_rating_screen()
    
    def show_outfit_rating_screen(self):
        """Display screen to rate the combined outfit with 6 sliders"""
        self.clear_window()
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        title = ttk.Label(main_frame, text="Rate Your Outfit", font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        selected_frame = ttk.LabelFrame(main_frame, text="Your Selected Outfit", padding="10")
        selected_frame.pack(fill=tk.BOTH, expand=False, pady=10)
        
        selected_content = ttk.Frame(selected_frame)
        selected_content.pack(fill=tk.BOTH)
        
        top_name = self.selected_outfit["top"]
        bottom_name = self.selected_outfit["bottom"]
        
        image_frame = ttk.Frame(selected_content)
        image_frame.pack(fill=tk.BOTH)
        
        # Top image
        top_folder = os.path.join(self.image_folder, "Tops")
        top_path = os.path.join(top_folder, top_name)
        if os.path.exists(top_path):
            top_img = Image.open(top_path)
            top_img.thumbnail((120, 150), Image.Resampling.LANCZOS)
            top_photo = ImageTk.PhotoImage(top_img)
            
            top_display = ttk.Frame(image_frame)
            top_display.pack(side=tk.LEFT, padx=20)
            
            ttk.Label(top_display, text="Top:", font=("Arial", 10, "bold")).pack()
            top_img_label = ttk.Label(top_display, image=top_photo)
            top_img_label.image = top_photo
            top_img_label.pack()
            ttk.Label(top_display, text=top_name[:20], font=("Arial", 8), wraplength=120).pack()
        
        # Bottom image
        bottom_folder = os.path.join(self.image_folder, "Bottoms")
        bottom_path = os.path.join(bottom_folder, bottom_name)
        if os.path.exists(bottom_path):
            bottom_img = Image.open(bottom_path)
            bottom_img.thumbnail((120, 150), Image.Resampling.LANCZOS)
            bottom_photo = ImageTk.PhotoImage(bottom_img)
            
            bottom_display = ttk.Frame(image_frame)
            bottom_display.pack(side=tk.LEFT, padx=20)
            
            ttk.Label(bottom_display, text="Bottom:", font=("Arial", 10, "bold")).pack()
            bottom_img_label = ttk.Label(bottom_display, image=bottom_photo)
            bottom_img_label.image = bottom_photo
            bottom_img_label.pack()
            ttk.Label(bottom_display, text=bottom_name[:20], font=("Arial", 8), wraplength=120).pack()
        
        # Weather
        weather_frame = ttk.Frame(selected_content)
        weather_frame.pack(side=tk.RIGHT, padx=20)
        
        ttk.Label(weather_frame, text="Weather:", font=("Arial", 10, "bold")).pack()
        weather_text = f"Temp: {self.randomized_weather['Temperature']}°C\nRain: {self.randomized_weather['Rain']}%\nCloud: {self.randomized_weather['Cloud']}%"
        ttk.Label(weather_frame, text=weather_text, font=("Arial", 9)).pack()
        
        # Outfit rating sliders
        sliders_frame = ttk.LabelFrame(main_frame, text="Rate the Overall Outfit (0-15)", padding="15")
        sliders_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.outfit_scale_values = {}
        
        # Exclude Cool-Warm from outfit rating (only for individual clothing items)
        outfit_criteria = [c for c in self.characteristics if c[0] != "Cool-Warm"] + [("Outfit Match", "Clashing", "Perfect Match")]
        
        for char_name, left_label, right_label in outfit_criteria:
            frame = ttk.Frame(sliders_frame)
            frame.pack(fill=tk.X, pady=8)
            
            left = ttk.Label(frame, text=left_label, width=12, font=("Arial", 9, "bold"))
            left.pack(side=tk.LEFT, padx=5)
            
            scale = ttk.Scale(frame, from_=0, to=15, orient=tk.HORIZONTAL, 
                            command=lambda v, k=char_name: self.update_outfit_scale_value(k, v))
            scale.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
            
            right = ttk.Label(frame, text=right_label, width=12, font=("Arial", 9, "bold"))
            right.pack(side=tk.LEFT, padx=5)
            
            value_label = ttk.Label(frame, text="0", width=3, font=("Arial", 10, "bold"), foreground="blue")
            value_label.pack(side=tk.LEFT, padx=5)
            
            self.outfit_scale_values[char_name] = {"scale": scale, "label": value_label, "value": 0}
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=15)
        
        btn_save = ttk.Button(button_frame, text="Save Data to CSV", 
                             command=self.save_outfit_with_ratings)
        btn_save.pack(side=tk.LEFT, padx=5)
        
        btn_back = ttk.Button(button_frame, text="Go Back & Select Again", 
                             command=self.show_outfit_screen)
        btn_back.pack(side=tk.LEFT, padx=5)
        
        btn_menu = ttk.Button(button_frame, text="Back to Menu", 
                             command=self.show_mode_selection)
        btn_menu.pack(side=tk.LEFT, padx=5)
        
        # Bind keyboard shortcut
        self.root.bind('<Return>', lambda e: self.save_outfit_with_ratings())
    
    def update_outfit_scale_value(self, char_name, value):
        """Update outfit scale value display"""
        self.outfit_scale_values[char_name]["value"] = int(float(value))
        self.outfit_scale_values[char_name]["label"].config(text=str(int(float(value))))
    
    def save_outfit_with_ratings(self):
        """Save fully normalized outfit ratings to CSV"""
        top_name = self.selected_outfit["top"]
        bottom_name = self.selected_outfit["bottom"]
        
        # Get already-normalized characteristic values for the selected items from the CSV
        top_ratings = self.clothing_ratings.get(top_name, {})
        bottom_ratings = self.clothing_ratings.get(bottom_name, {})
        
        # Normalize the outfit sliders (0-15 -> 0.0-1.0)
        norm_casual_formal = round(self.outfit_scale_values["Casual-Formal"]["value"] / 15.0, 4)
        norm_minimal_colorful = round(self.outfit_scale_values["Minimal-Colorful"]["value"] / 15.0, 4)
        norm_fitted_oversized = round(self.outfit_scale_values["Fitted-Oversized"]["value"] / 15.0, 4)
        norm_feminine_masculine = round(self.outfit_scale_values["Feminine-Masculine"]["value"] / 15.0, 4)
        norm_simple_ornate = round(self.outfit_scale_values["Simple-Ornate"]["value"] / 15.0, 4)
        norm_outfit_match = round(self.outfit_scale_values["Outfit Match"]["value"] / 15.0, 4)
        
        # Normalize Weather (Temp: 5-31, Rain/Cloud: 0-100)
        norm_temp = round((self.randomized_weather["Temperature"] - 5) / 26.0, 4)
        norm_rain = round(self.randomized_weather["Rain"] / 100.0, 4)
        norm_cloud = round(self.randomized_weather["Cloud"] / 100.0, 4)

        row = {
            "top_casual_formal": top_ratings.get("Casual-Formal", ""),
            "top_minimal_colorful": top_ratings.get("Minimal-Colorful", ""),
            "top_fitted_oversized": top_ratings.get("Fitted-Oversized", ""),
            "top_feminine_masculine": top_ratings.get("Feminine-Masculine", ""),
            "top_simple_ornate": top_ratings.get("Simple-Ornate", ""),
            "bottom_casual_formal": bottom_ratings.get("Casual-Formal", ""),
            "bottom_minimal_colorful": bottom_ratings.get("Minimal-Colorful", ""),
            "bottom_fitted_oversized": bottom_ratings.get("Fitted-Oversized", ""),
            "bottom_feminine_masculine": bottom_ratings.get("Feminine-Masculine", ""),
            "bottom_simple_ornate": bottom_ratings.get("Simple-Ornate", ""),
            "outfit_casual_formal": norm_casual_formal,
            "outfit_minimal_colorful": norm_minimal_colorful,
            "outfit_fitted_oversized": norm_fitted_oversized,
            "outfit_feminine_masculine": norm_feminine_masculine,
            "outfit_simple_ornate": norm_simple_ornate,
            "outfit_match": norm_outfit_match,
            "temperature": norm_temp,
            "rain": norm_rain,
            "cloud": norm_cloud
        }
        
        csv_path = os.path.join(self.output_folder, "outfit_ratings.csv")
        fieldnames = [
            "top_casual_formal", "top_minimal_colorful", "top_fitted_oversized", "top_feminine_masculine", "top_simple_ornate",
            "bottom_casual_formal", "bottom_minimal_colorful", "bottom_fitted_oversized", "bottom_feminine_masculine", "bottom_simple_ornate",
            "outfit_casual_formal", "outfit_minimal_colorful", "outfit_fitted_oversized", "outfit_feminine_masculine", "outfit_simple_ornate",
            "outfit_match", "temperature", "rain", "cloud"
        ]
        
        file_exists = os.path.isfile(csv_path)
        with open(csv_path, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
        
        messagebox.showinfo("Success", "Normalized numerical outfit data saved successfully!")
        
        self.generate_outfit()
        self.show_outfit_screen()
    
    def view_csv_files(self):
        """Open the output folder with CSV files"""
        os.startfile(self.output_folder)
    
    def clear_window(self):
        """Clear all widgets from the window"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def extract_filename_keywords(self, filename):
        """Extract keywords from filename"""
        # Remove extension and lowercase
        name = filename.rsplit('.', 1)[0].lower()
        # Split by common separators
        keywords = name.replace('_', ' ').replace('-', ' ').split()
        return keywords
    
    def group_images_by_keyword(self):
        """Group unrated images by common keywords in filename"""
        groups = {}
        for img in self.unrated_images:
            keywords = self.extract_filename_keywords(img)
            for keyword in keywords:
                if len(keyword) > 2:  # Skip very short words
                    if keyword not in groups:
                        groups[keyword] = []
                    groups[keyword].append(img)
        # Sort by group size (largest first)
        return dict(sorted(groups.items(), key=lambda x: len(x[1]), reverse=True))
    
    def start_mode3(self):
        """Start Mode 3: Batch rate by name pattern"""
        self.load_clothing_ratings()
        self.current_mode = 3
        self.current_index = 0
        # Filter to only show unrated items
        self.unrated_images = [img for img in self.all_images if img not in self.clothing_ratings]
        if not self.unrated_images:
            messagebox.showinfo("All Rated", "All clothing items have been rated!")
            self.show_mode_selection()
            return
        
        self.keyword_groups = self.group_images_by_keyword()
        self.keyword_list = list(self.keyword_groups.keys())
        self.current_keyword_index = 0
        self.show_batch_keyword_selection()
    
    def show_batch_keyword_selection(self):
        """Show selection of keyword to batch rate"""
        self.clear_window()
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        title = ttk.Label(main_frame, text="Select Category to Batch Rate", font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        # Create listbox of keywords
        list_frame = ttk.LabelFrame(main_frame, text="Categories by Count", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.keyword_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Arial", 10))
        self.keyword_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.keyword_listbox.yview)
        
        for keyword in self.keyword_list:
            count = len(self.keyword_groups[keyword])
            self.keyword_listbox.insert(tk.END, f"{keyword.capitalize()} ({count} items)")
        
        self.keyword_listbox.bind('<Return>', lambda e: self.select_keyword_from_listbox())
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        btn_select = ttk.Button(button_frame, text="Select & Rate Group [Enter]", 
                               command=self.select_keyword_from_listbox)
        btn_select.pack(side=tk.LEFT, padx=5)
        
        btn_back = ttk.Button(button_frame, text="Back to Menu", 
                             command=self.show_mode_selection)
        btn_back.pack(side=tk.LEFT, padx=5)
    
    def select_keyword_from_listbox(self):
        """Select keyword from listbox"""
        selection = self.keyword_listbox.curselection()
        if selection:
            self.current_keyword_index = selection[0]
            self.show_batch_rating_screen()
    
    def show_batch_rating_screen(self):
        """Show batch rating screen for selected keyword"""
        if self.current_keyword_index >= len(self.keyword_list):
            messagebox.showinfo("Complete", "Batch rating complete! Now fine-tune items.")
            self.start_mode1()
            return
        
        self.clear_window()
        
        current_keyword = self.keyword_list[self.current_keyword_index]
        items_in_group = self.keyword_groups[current_keyword]
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        title = ttk.Label(main_frame, text=f"Batch Rate: {current_keyword.upper()}", 
                         font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        info = ttk.Label(main_frame, text=f"Setting ratings for {len(items_in_group)} items with '{current_keyword}' in name", 
                        font=("Arial", 10))
        info.pack(pady=5)
        
        # Show sample images
        preview_frame = ttk.LabelFrame(main_frame, text="Sample Items (first 3)", padding="10")
        preview_frame.pack(fill=tk.X, pady=10)
        
        for idx, item in enumerate(items_in_group[:3]):
            if item in self.tops:
                img_path = os.path.join(self.tops_folder, item)
            else:
                img_path = os.path.join(self.bottoms_folder, item)
            
            if os.path.exists(img_path):
                img = Image.open(img_path)
                img.thumbnail((100, 150), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                img_label = ttk.Label(preview_frame, image=photo, text=item[:15], compound=tk.TOP)
                img_label.image = photo
                img_label.pack(side=tk.LEFT, padx=5)
        
        # Rating sliders
        slider_frame = ttk.LabelFrame(main_frame, text="Set Default Values (0-15)", padding="15")
        slider_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.batch_scale_values = {}
        
        for char_name, left_label, right_label in self.characteristics:
            frame = ttk.Frame(slider_frame)
            frame.pack(fill=tk.X, pady=8)
            
            left = ttk.Label(frame, text=left_label, width=12, font=("Arial", 9, "bold"))
            left.pack(side=tk.LEFT, padx=5)
            
            scale = ttk.Scale(frame, from_=0, to=15, orient=tk.HORIZONTAL, 
                            command=lambda v, k=char_name: self.update_batch_scale_value(k, v))
            scale.set(7)
            scale.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
            
            right = ttk.Label(frame, text=right_label, width=12, font=("Arial", 9, "bold"))
            right.pack(side=tk.LEFT, padx=5)
            
            value_label = ttk.Label(frame, text="7", width=3, font=("Arial", 10, "bold"), foreground="blue")
            value_label.pack(side=tk.LEFT, padx=5)
            
            self.batch_scale_values[char_name] = {"scale": scale, "label": value_label, "value": 7}
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=15)
        
        btn_apply = ttk.Button(button_frame, text="Apply to All & Fine-Tune", 
                              command=self.apply_batch_and_finetune)
        btn_apply.pack(side=tk.LEFT, padx=5)
        
        btn_skip = ttk.Button(button_frame, text="Skip This Group", 
                             command=self.skip_batch_group)
        btn_skip.pack(side=tk.LEFT, padx=5)
        
        btn_back = ttk.Button(button_frame, text="Back to Menu", 
                             command=self.show_mode_selection)
        btn_back.pack(side=tk.LEFT, padx=5)
    
    def update_batch_scale_value(self, char_name, value):
        """Update batch scale value display"""
        self.batch_scale_values[char_name]["value"] = int(float(value))
        self.batch_scale_values[char_name]["label"].config(text=str(int(float(value))))
    
    def apply_batch_and_finetune(self):
        """Apply batch ratings to all items in group, then fine-tune each"""
        current_keyword = self.keyword_list[self.current_keyword_index]
        items_in_group = self.keyword_groups[current_keyword]
        
        # Save batch ratings for all items
        csv_path = os.path.join(self.output_folder, "clothing_ratings.csv")
        fieldnames = ["image"] + [name for name, _, _ in self.characteristics]
        
        file_exists = os.path.isfile(csv_path)
        with open(csv_path, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            
            for item in items_in_group:
                row = {"image": item}
                for char_name in self.batch_scale_values:
                    val = self.batch_scale_values[char_name]["value"]
                    row[char_name] = round(val / 15.0, 4)  # Normalize
                writer.writerow(row)
            csvfile.flush()  # Ensure data is written to disk
        
        # Now set up fine-tuning mode
        self.finetune_items = items_in_group
        self.finetune_index = 0
        # Reload to get newly added ratings
        self.clothing_ratings = {}  # Clear first
        csv_path = os.path.join(self.output_folder, "clothing_ratings.csv")
        if os.path.exists(csv_path):
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    image_name = row['image']
                    self.clothing_ratings[image_name] = row
        
        self.current_mode = 1
        self.all_images = self.finetune_items
        self.current_index = 0
        
        messagebox.showinfo("Batch Applied", f"Applied ratings to {len(items_in_group)} items. Now fine-tune each one.")
        self.show_rating_screen()
    
    def skip_batch_group(self):
        """Skip current batch group and move to next"""
        self.current_keyword_index += 1
        self.show_batch_rating_screen()
    
    def start_mode4(self):
        """Start Mode 4: Evaluate AI outfit predictions"""
        self.load_clothing_ratings()
        
        # Check if model exists
        model_path = os.path.join(os.path.dirname(__file__), "outfit_model.pth")
        if not os.path.exists(model_path):
            messagebox.showerror("Model Not Found", "outfit_model.pth not found. Train the model first.")
            return
        
        # Load model
        try:
            self.ai_model = outfit_chooser()
            self.ai_model.load_state_dict(torch.load(model_path))
            self.ai_model.eval()
        except Exception as e:
            messagebox.showerror("Model Error", f"Failed to load model: {e}")
            return
        
        self.current_mode = 4
        self.generate_ai_outfit()
        self.show_ai_outfit_evaluation()
    
    def generate_ai_outfit(self):
        """Generate a random outfit and use AI to predict its rating"""
        self.load_clothing_ratings()
        
        # Get rated items only
        rated_tops = [t for t in self.tops if t in self.clothing_ratings]
        rated_bottoms = [b for b in self.bottoms if b in self.clothing_ratings]
        
        if not rated_tops or not rated_bottoms:
            messagebox.showwarning("No Rated Items", "Need rated items to generate outfits.")
            self.show_mode_selection()
            return
        
        # Select random items
        top = random.choice(rated_tops)
        bottom = random.choice(rated_bottoms)
        
        # Generate random weather
        temp = random.randint(5, 31)
        if temp >= 28:
            cloud = random.randint(0, 35)
        elif temp <= 15:
            cloud = random.randint(40, 100)
        else:
            cloud = random.randint(10, 80)
        if cloud >= 70:
            rain = random.randint(40, 100)
        elif cloud >= 30:
            rain = random.randint(0, 40)
        else:
            rain = random.randint(0, 5)
        
        # Get ratings from CSV
        top_ratings = self.clothing_ratings[top]
        bottom_ratings = self.clothing_ratings[bottom]
        
        # Create input tensor for model
        features = [
            float(top_ratings.get("Casual-Formal", 0.5)),
            float(top_ratings.get("Minimal-Colorful", 0.5)),
            float(top_ratings.get("Fitted-Oversized", 0.5)),
            float(top_ratings.get("Feminine-Masculine", 0.5)),
            float(top_ratings.get("Simple-Ornate", 0.5)),
            float(bottom_ratings.get("Casual-Formal", 0.5)),
            float(bottom_ratings.get("Minimal-Colorful", 0.5)),
            float(bottom_ratings.get("Fitted-Oversized", 0.5)),
            float(bottom_ratings.get("Feminine-Masculine", 0.5)),
            float(bottom_ratings.get("Simple-Ornate", 0.5)),
            (temp - 5) / 26.0,  # Normalize temperature
            rain / 100.0,
            cloud / 100.0
        ]
        
        input_tensor = torch.tensor([features], dtype=torch.float32)
        
        with torch.no_grad():
            predictions = self.ai_model(input_tensor)[0]
        
        self.current_ai_outfit = {
            "top": top,
            "bottom": bottom,
            "temperature": temp,
            "rain": rain,
            "cloud": cloud,
            "predictions": predictions.tolist()
        }
    
    def show_ai_outfit_evaluation(self):
        """Display AI-generated outfit for evaluation"""
        self.clear_window()
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        title = ttk.Label(main_frame, text="Evaluate AI Outfit Prediction", font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        # Display outfit images
        image_frame = ttk.LabelFrame(main_frame, text="AI-Generated Outfit", padding="10")
        image_frame.pack(fill=tk.X, pady=10)
        
        top_name = self.current_ai_outfit["top"]
        bottom_name = self.current_ai_outfit["bottom"]
        
        # Top image
        top_path = os.path.join(self.tops_folder, top_name)
        if os.path.exists(top_path):
            top_img = Image.open(top_path)
            top_img.thumbnail((120, 150), Image.Resampling.LANCZOS)
            top_photo = ImageTk.PhotoImage(top_img)
            
            top_display = ttk.Frame(image_frame)
            top_display.pack(side=tk.LEFT, padx=20)
            ttk.Label(top_display, text="Top:", font=("Arial", 10, "bold")).pack()
            top_img_label = ttk.Label(top_display, image=top_photo)
            top_img_label.image = top_photo
            top_img_label.pack()
        
        # Bottom image
        bottom_path = os.path.join(self.bottoms_folder, bottom_name)
        if os.path.exists(bottom_path):
            bottom_img = Image.open(bottom_path)
            bottom_img.thumbnail((120, 150), Image.Resampling.LANCZOS)
            bottom_photo = ImageTk.PhotoImage(bottom_img)
            
            bottom_display = ttk.Frame(image_frame)
            bottom_display.pack(side=tk.LEFT, padx=20)
            ttk.Label(bottom_display, text="Bottom:", font=("Arial", 10, "bold")).pack()
            bottom_img_label = ttk.Label(bottom_display, image=bottom_photo)
            bottom_img_label.image = bottom_photo
            bottom_img_label.pack()
        
        # Weather
        weather_frame = ttk.Frame(image_frame)
        weather_frame.pack(side=tk.RIGHT, padx=20)
        ttk.Label(weather_frame, text="Weather:", font=("Arial", 10, "bold")).pack()
        weather_text = f"Temp: {self.current_ai_outfit['temperature']}°C\nRain: {self.current_ai_outfit['rain']}%\nCloud: {self.current_ai_outfit['cloud']}%"
        ttk.Label(weather_frame, text=weather_text, font=("Arial", 9)).pack()
        
        # AI Predictions (non-editable display)
        pred_frame = ttk.LabelFrame(main_frame, text="AI Predictions (0-15 scale)", padding="15")
        pred_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        outfit_criteria = [c for c in self.characteristics if c[0] != "Cool-Warm"] + [("Outfit Match", "Clashing", "Perfect Match")]
        
        self.ai_pred_labels = {}
        for idx, (char_name, left_label, right_label) in enumerate(outfit_criteria):
            frame = ttk.Frame(pred_frame)
            frame.pack(fill=tk.X, pady=8)
            
            left = ttk.Label(frame, text=left_label, width=12, font=("Arial", 9, "bold"))
            left.pack(side=tk.LEFT, padx=5)
            
            # Show AI prediction as denormalized value (0-15)
            pred_val = self.current_ai_outfit["predictions"][idx]
            pred_display = int(round(pred_val * 15))
            
            pred_label = ttk.Label(frame, text=f"{pred_display}/15", width=8, font=("Arial", 10, "bold"), foreground="blue")
            pred_label.pack(side=tk.LEFT, padx=10)
            
            right = ttk.Label(frame, text=right_label, width=12, font=("Arial", 9, "bold"))
            right.pack(side=tk.LEFT, padx=5)
            
            self.ai_pred_labels[char_name] = pred_label
        
        # Feedback buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=15)
        
        btn_yes = ttk.Button(button_frame, text="✓ Good Prediction (Yes)", 
                            command=self.ai_feedback_yes)
        btn_yes.pack(side=tk.LEFT, padx=5)
        
        btn_no = ttk.Button(button_frame, text="✗ Bad Prediction (No)", 
                           command=self.ai_feedback_no)
        btn_no.pack(side=tk.LEFT, padx=5)
        
        btn_next = ttk.Button(button_frame, text="Next Outfit", 
                             command=self.ai_next_outfit)
        btn_next.pack(side=tk.LEFT, padx=5)
        
        btn_back = ttk.Button(button_frame, text="Back to Menu", 
                             command=self.show_mode_selection)
        btn_back.pack(side=tk.LEFT, padx=5)
    
    def ai_feedback_yes(self):
        """User confirmed AI prediction was good"""
        self.save_ai_feedback(1)
        messagebox.showinfo("Feedback Recorded", "Good! This helps train the model.")
        self.ai_next_outfit()
    
    def ai_feedback_no(self):
        """User says AI prediction was bad"""
        self.save_ai_feedback(0)
        messagebox.showinfo("Feedback Recorded", "Noted. The model will learn from this.")
        self.ai_next_outfit()
    
    def save_ai_feedback(self, feedback):
        """Save AI prediction feedback to CSV"""
        csv_path = os.path.join(self.output_folder, "user_feedback.csv")
        
        # Prepare row with outfit parameters and predictions
        row = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "top": self.current_ai_outfit["top"],
            "bottom": self.current_ai_outfit["bottom"],
            "temperature": self.current_ai_outfit["temperature"],
            "rain": self.current_ai_outfit["rain"],
            "cloud": self.current_ai_outfit["cloud"],
            "pred_casual_formal": round(self.current_ai_outfit["predictions"][0], 4),
            "pred_minimal_colorful": round(self.current_ai_outfit["predictions"][1], 4),
            "pred_fitted_oversized": round(self.current_ai_outfit["predictions"][2], 4),
            "pred_feminine_masculine": round(self.current_ai_outfit["predictions"][3], 4),
            "pred_simple_ornate": round(self.current_ai_outfit["predictions"][4], 4),
            "pred_outfit_match": round(self.current_ai_outfit["predictions"][5], 4),
            "feedback": feedback
        }
        
        fieldnames = [
            "timestamp", "top", "bottom", "temperature", "rain", "cloud",
            "pred_casual_formal", "pred_minimal_colorful", "pred_fitted_oversized",
            "pred_feminine_masculine", "pred_simple_ornate", "pred_outfit_match", "feedback"
        ]
        
        file_exists = os.path.isfile(csv_path)
        with open(csv_path, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
    
    
    def ai_next_outfit(self):
        """Generate and show next AI outfit"""
        self.generate_ai_outfit()
        self.show_ai_outfit_evaluation()


class outfit_chooser(nn.Module):
    """Neural network model for outfit prediction"""
    def __init__(self):
        super(outfit_chooser, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(13, 64),
            nn.LeakyReLU(0.075),
            nn.Linear(64, 32),
            nn.LeakyReLU(0.015),
            nn.Linear(32, 6),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.network(x)

def main():
    root = tk.Tk()
    app = ClothingRatingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
