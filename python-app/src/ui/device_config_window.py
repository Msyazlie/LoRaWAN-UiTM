"""
Device Configuration Window

A tkinter-based Settings GUI for configuring:
- Floors with device assignments
- Macro Sensor DevEUI
- Bluetooth Gateway DevEUI  
- LoRaWAN Gateway ID
- Beacon-to-floor assignments

Author: IoT Security System
Version: 1.0
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os


class DeviceConfigWindow:
    """
    Settings window for configuring IoT devices and floor assignments.
    """
    
    CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "devices.json")
    
    def __init__(self, parent, on_save_callback=None):
        """
        Initialize the configuration window.
        
        Args:
            parent: Parent tkinter window
            on_save_callback: Function to call after saving (to refresh main UI)
        """
        self.parent = parent
        self.on_save_callback = on_save_callback
        self.config_data = self._load_config()
        self.selected_floor_id = None
        
        # Create toplevel window
        self.window = tk.Toplevel(parent)
        self.window.title("⚙️ Device Configuration")
        self.window.geometry("650x700")
        self.window.configure(bg="#1a1a2e")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Color scheme (matching main window)
        self.colors = {
            "bg": "#1a1a2e",
            "card": "#16213e",
            "input_bg": "#0f3460",
            "text": "#eaeaea",
            "accent": "#4ade80",
            "danger": "#ef4444",
            "warning": "#fbbf24"
        }
        
        self._build_ui()
        self._populate_floors()
        
        # Select first floor if exists
        if self.config_data.get("floors"):
            self._select_floor(self.config_data["floors"][0]["id"])
    
    def _load_config(self):
        """Load configuration from devices.json."""
        default_config = {
            "floors": [],
            "beacons": []
        }
        
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Failed to load config: {e}")
        
        return default_config
    
    def _save_config(self):
        """Save configuration to devices.json."""
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(self.config_data, f, indent=2)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")
            return False
    
    def _build_ui(self):
        """Build the configuration UI."""
        
        # --- Header ---
        header = tk.Frame(self.window, bg=self.colors["bg"], pady=15)
        header.pack(fill=tk.X, padx=20)
        
        tk.Label(header, text="⚙️ Device Configuration", 
                font=("Helvetica", 16, "bold"), 
                fg="white", bg=self.colors["bg"]).pack(side=tk.LEFT)
        
        # --- Floor List Section ---
        floor_section = tk.LabelFrame(self.window, text=" Floors ", 
                                      bg=self.colors["card"], fg=self.colors["text"],
                                      font=("Helvetica", 11, "bold"), pady=10, padx=10)
        floor_section.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Floor listbox
        self.floor_listbox = tk.Listbox(floor_section, bg=self.colors["input_bg"], 
                                        fg=self.colors["text"], font=("Consolas", 11),
                                        height=4, selectbackground=self.colors["accent"],
                                        selectforeground="black", borderwidth=0,
                                        highlightthickness=1, highlightcolor=self.colors["accent"])
        self.floor_listbox.pack(fill=tk.X, pady=(0, 10))
        self.floor_listbox.bind('<<ListboxSelect>>', self._on_floor_select)
        
        # Floor buttons
        floor_btn_frame = tk.Frame(floor_section, bg=self.colors["card"])
        floor_btn_frame.pack(fill=tk.X)
        
        btn_add_floor = tk.Button(floor_btn_frame, text="➕ Add Floor", 
                                  bg=self.colors["accent"], fg="black",
                                  font=("Arial", 10, "bold"), cursor="hand2",
                                  command=self._add_floor)
        btn_add_floor.pack(side=tk.LEFT, padx=(0, 5))
        
        btn_del_floor = tk.Button(floor_btn_frame, text="🗑️ Delete Floor", 
                                  bg=self.colors["danger"], fg="white",
                                  font=("Arial", 10, "bold"), cursor="hand2",
                                  command=self._delete_floor)
        btn_del_floor.pack(side=tk.LEFT)
        
        # --- Floor Details Section ---
        self.details_frame = tk.LabelFrame(self.window, text=" Floor Details ", 
                                           bg=self.colors["card"], fg=self.colors["text"],
                                           font=("Helvetica", 11, "bold"), pady=15, padx=15)
        self.details_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
        
        # Floor Name
        tk.Label(self.details_frame, text="Floor Name:", 
                bg=self.colors["card"], fg=self.colors["text"],
                font=("Helvetica", 10)).grid(row=0, column=0, sticky="w", pady=5)
        
        self.entry_floor_name = tk.Entry(self.details_frame, bg=self.colors["input_bg"],
                                         fg=self.colors["text"], font=("Consolas", 11),
                                         insertbackground="white", width=40)
        self.entry_floor_name.grid(row=0, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        # Macro Sensor DevEUI
        tk.Label(self.details_frame, text="Macro Sensor DevEUI:", 
                bg=self.colors["card"], fg=self.colors["text"],
                font=("Helvetica", 10)).grid(row=1, column=0, sticky="w", pady=5)
        
        self.entry_macro_sensor = tk.Entry(self.details_frame, bg=self.colors["input_bg"],
                                           fg=self.colors["text"], font=("Consolas", 11),
                                           insertbackground="white", width=40)
        self.entry_macro_sensor.grid(row=1, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        tk.Label(self.details_frame, text="(e.g., 70b3d5a4d31205cf)", 
                bg=self.colors["card"], fg="#666",
                font=("Helvetica", 9)).grid(row=2, column=1, sticky="w", padx=(10, 0))
        
        # Bluetooth Gateway DevEUI
        tk.Label(self.details_frame, text="Bluetooth Gateway DevEUI:", 
                bg=self.colors["card"], fg=self.colors["text"],
                font=("Helvetica", 10)).grid(row=3, column=0, sticky="w", pady=5)
        
        self.entry_bt_gateway = tk.Entry(self.details_frame, bg=self.colors["input_bg"],
                                         fg=self.colors["text"], font=("Consolas", 11),
                                         insertbackground="white", width=40)
        self.entry_bt_gateway.grid(row=3, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        tk.Label(self.details_frame, text="(e.g., 70b3d5a4d3120591)", 
                bg=self.colors["card"], fg="#666",
                font=("Helvetica", 9)).grid(row=4, column=1, sticky="w", padx=(10, 0))
        
        # LoRaWAN Gateway ID
        tk.Label(self.details_frame, text="LoRaWAN Gateway ID:", 
                bg=self.colors["card"], fg=self.colors["text"],
                font=("Helvetica", 10)).grid(row=5, column=0, sticky="w", pady=5)
        
        self.entry_lora_gateway = tk.Entry(self.details_frame, bg=self.colors["input_bg"],
                                           fg=self.colors["text"], font=("Consolas", 11),
                                           insertbackground="white", width=40)
        self.entry_lora_gateway.grid(row=5, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        tk.Label(self.details_frame, text="(e.g., ac1f09fffe1ea999)", 
                bg=self.colors["card"], fg="#666",
                font=("Helvetica", 9)).grid(row=6, column=1, sticky="w", padx=(10, 0))
        
        # Update Floor button
        btn_update = tk.Button(self.details_frame, text="✔️ Update Floor Details", 
                               bg=self.colors["accent"], fg="black",
                               font=("Arial", 10, "bold"), cursor="hand2",
                               command=self._update_floor_details)
        btn_update.grid(row=7, column=0, columnspan=2, pady=(15, 5), sticky="ew")
        
        # --- Beacon Assignment Section ---
        beacon_section = tk.LabelFrame(self.window, text=" Beacon Assignment ", 
                                       bg=self.colors["card"], fg=self.colors["text"],
                                       font=("Helvetica", 11, "bold"), pady=10, padx=10)
        beacon_section.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Beacon listbox with checkboxes (simulated with text)
        self.beacon_listbox = tk.Listbox(beacon_section, bg=self.colors["input_bg"], 
                                         fg=self.colors["text"], font=("Consolas", 11),
                                         height=4, selectmode=tk.MULTIPLE,
                                         selectbackground=self.colors["accent"],
                                         selectforeground="black", borderwidth=0)
        self.beacon_listbox.pack(fill=tk.X, pady=(0, 10))
        
        # Add beacon entry
        add_beacon_frame = tk.Frame(beacon_section, bg=self.colors["card"])
        add_beacon_frame.pack(fill=tk.X)
        
        tk.Label(add_beacon_frame, text="New Beacon ID:", 
                bg=self.colors["card"], fg=self.colors["text"],
                font=("Helvetica", 10)).pack(side=tk.LEFT)
        
        self.entry_new_beacon = tk.Entry(add_beacon_frame, bg=self.colors["input_bg"],
                                         fg=self.colors["text"], font=("Consolas", 11),
                                         insertbackground="white", width=10)
        self.entry_new_beacon.pack(side=tk.LEFT, padx=5)
        
        tk.Label(add_beacon_frame, text="Name:", 
                bg=self.colors["card"], fg=self.colors["text"],
                font=("Helvetica", 10)).pack(side=tk.LEFT)
        
        self.entry_beacon_name = tk.Entry(add_beacon_frame, bg=self.colors["input_bg"],
                                          fg=self.colors["text"], font=("Consolas", 11),
                                          insertbackground="white", width=15)
        self.entry_beacon_name.pack(side=tk.LEFT, padx=5)
        
        btn_add_beacon = tk.Button(add_beacon_frame, text="➕ Add", 
                                   bg=self.colors["warning"], fg="black",
                                   font=("Arial", 9, "bold"), cursor="hand2",
                                   command=self._add_beacon)
        btn_add_beacon.pack(side=tk.LEFT, padx=5)
        
        btn_del_beacon = tk.Button(add_beacon_frame, text="🗑️ Delete", 
                                   bg=self.colors["danger"], fg="white",
                                   font=("Arial", 9, "bold"), cursor="hand2",
                                   command=self._delete_beacon)
        btn_del_beacon.pack(side=tk.LEFT)
        
        # --- Footer Buttons ---
        footer = tk.Frame(self.window, bg=self.colors["bg"], pady=15)
        footer.pack(fill=tk.X, padx=20)
        
        btn_cancel = tk.Button(footer, text="Cancel", 
                               bg="#4b5563", fg="white",
                               font=("Arial", 11, "bold"), cursor="hand2",
                               width=15, command=self.window.destroy)
        btn_cancel.pack(side=tk.LEFT, ipady=8)
        
        btn_save = tk.Button(footer, text="💾 Save All", 
                             bg=self.colors["accent"], fg="black",
                             font=("Arial", 11, "bold"), cursor="hand2",
                             width=15, command=self._save_and_close)
        btn_save.pack(side=tk.RIGHT, ipady=8)
        
        # Configure grid weights
        self.details_frame.columnconfigure(1, weight=1)
    
    def _populate_floors(self):
        """Populate the floor listbox."""
        self.floor_listbox.delete(0, tk.END)
        for floor in self.config_data.get("floors", []):
            self.floor_listbox.insert(tk.END, f"📍 {floor['name']}")
    
    def _populate_beacons(self):
        """Populate beacon listbox for selected floor."""
        self.beacon_listbox.delete(0, tk.END)
        
        for beacon in self.config_data.get("beacons", []):
            assigned = beacon.get("floor_id") == self.selected_floor_id
            icon = "☑" if assigned else "☐"
            self.beacon_listbox.insert(tk.END, f"{icon} {beacon['id']} - {beacon.get('name', 'Unknown')}")
            
            if assigned:
                idx = self.beacon_listbox.size() - 1
                self.beacon_listbox.selection_set(idx)
    
    def _on_floor_select(self, event):
        """Handle floor selection."""
        selection = self.floor_listbox.curselection()
        if selection:
            idx = selection[0]
            if idx < len(self.config_data.get("floors", [])):
                floor = self.config_data["floors"][idx]
                self._select_floor(floor["id"])
    
    def _select_floor(self, floor_id):
        """Select and display a floor's details."""
        self.selected_floor_id = floor_id
        
        # Find floor data
        floor = None
        for f in self.config_data.get("floors", []):
            if f["id"] == floor_id:
                floor = f
                break
        
        if not floor:
            return
        
        # Clear and populate entries
        self.entry_floor_name.delete(0, tk.END)
        self.entry_floor_name.insert(0, floor.get("name", ""))
        
        self.entry_macro_sensor.delete(0, tk.END)
        self.entry_macro_sensor.insert(0, floor.get("macro_sensor_eui", ""))
        
        self.entry_bt_gateway.delete(0, tk.END)
        self.entry_bt_gateway.insert(0, floor.get("bluetooth_gateway_eui", ""))
        
        self.entry_lora_gateway.delete(0, tk.END)
        self.entry_lora_gateway.insert(0, floor.get("lorawan_gateway_id", ""))
        
        # Populate beacons
        self._populate_beacons()
    
    def _add_floor(self):
        """Add a new floor."""
        # Generate unique ID
        floor_num = len(self.config_data.get("floors", [])) + 1
        new_floor = {
            "id": f"floor_{floor_num}",
            "name": f"Floor {floor_num}",
            "macro_sensor_eui": "70b3d5a4d31205ce",
            "bluetooth_gateway_eui": "",
            "lorawan_gateway_id": ""
        }
        
        if "floors" not in self.config_data:
            self.config_data["floors"] = []
        
        self.config_data["floors"].append(new_floor)
        self._populate_floors()
        
        # Select the new floor
        self.floor_listbox.selection_clear(0, tk.END)
        self.floor_listbox.selection_set(tk.END)
        self._select_floor(new_floor["id"])
    
    def _delete_floor(self):
        """Delete selected floor."""
        if not self.selected_floor_id:
            messagebox.showwarning("Warning", "Please select a floor to delete.")
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this floor?"):
            # Remove floor
            self.config_data["floors"] = [f for f in self.config_data.get("floors", []) 
                                          if f["id"] != self.selected_floor_id]
            
            # Unassign beacons from this floor
            for beacon in self.config_data.get("beacons", []):
                if beacon.get("floor_id") == self.selected_floor_id:
                    beacon["floor_id"] = None
            
            self.selected_floor_id = None
            self._populate_floors()
            
            # Clear details
            self.entry_floor_name.delete(0, tk.END)
            self.entry_macro_sensor.delete(0, tk.END)
            self.entry_bt_gateway.delete(0, tk.END)
            self.entry_lora_gateway.delete(0, tk.END)
            self.beacon_listbox.delete(0, tk.END)
    
    def _update_floor_details(self):
        """Update the selected floor's details from entries."""
        if not self.selected_floor_id:
            messagebox.showwarning("Warning", "Please select a floor first.")
            return
        
        # Find and update floor
        for floor in self.config_data.get("floors", []):
            if floor["id"] == self.selected_floor_id:
                floor["name"] = self.entry_floor_name.get().strip()
                floor["macro_sensor_eui"] = self.entry_macro_sensor.get().strip().lower()
                floor["bluetooth_gateway_eui"] = self.entry_bt_gateway.get().strip().lower()
                floor["lorawan_gateway_id"] = self.entry_lora_gateway.get().strip().lower()
                break
        
        # Update beacon assignments based on selection
        selected_indices = self.beacon_listbox.curselection()
        beacons = self.config_data.get("beacons", [])
        
        for i, beacon in enumerate(beacons):
            if i in selected_indices:
                beacon["floor_id"] = self.selected_floor_id
            elif beacon.get("floor_id") == self.selected_floor_id:
                beacon["floor_id"] = None
        
        self._populate_floors()
        messagebox.showinfo("Success", "Floor details updated!")
    
    def _add_beacon(self):
        """Add a new beacon."""
        beacon_id = self.entry_new_beacon.get().strip().upper()
        beacon_name = self.entry_beacon_name.get().strip() or f"Beacon {beacon_id}"
        
        if not beacon_id:
            messagebox.showwarning("Warning", "Please enter a beacon ID.")
            return
        
        # Check if already exists
        for beacon in self.config_data.get("beacons", []):
            if beacon["id"].upper() == beacon_id:
                messagebox.showwarning("Warning", f"Beacon {beacon_id} already exists.")
                return
        
        if "beacons" not in self.config_data:
            self.config_data["beacons"] = []
        
        self.config_data["beacons"].append({
            "id": beacon_id,
            "name": beacon_name,
            "floor_id": self.selected_floor_id
        })
        
        self.entry_new_beacon.delete(0, tk.END)
        self.entry_beacon_name.delete(0, tk.END)
        self._populate_beacons()
    
    def _delete_beacon(self):
        """Delete selected beacon(s)."""
        selection = self.beacon_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select beacon(s) to delete.")
            return
        
        if messagebox.askyesno("Confirm Delete", "Delete selected beacon(s)?"):
            beacons = self.config_data.get("beacons", [])
            # Remove selected (in reverse order to maintain indices)
            for idx in sorted(selection, reverse=True):
                if idx < len(beacons):
                    del beacons[idx]
            
            self._populate_beacons()
    
    def _save_and_close(self):
        """Save configuration and close window."""
        if self._save_config():
            messagebox.showinfo("Success", "Configuration saved successfully!")
            if self.on_save_callback:
                self.on_save_callback()
            self.window.destroy()


def open_config_window(parent, on_save_callback=None):
    """
    Helper function to open the configuration window.
    
    Args:
        parent: Parent tkinter window
        on_save_callback: Function to call after saving
    """
    DeviceConfigWindow(parent, on_save_callback)
