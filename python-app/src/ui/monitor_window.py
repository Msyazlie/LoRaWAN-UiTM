import tkinter as tk
from tkinter import ttk
from src.config import settings
from src.ui.device_config_window import open_config_window
import time


class MonitorWindow:
    """
    Multi-beacon monitoring window with Treeview display.
    Shows all tracked beacons with individual status.
    """
    
    def __init__(self, root, on_manual_alarm, alarm_rules=None):
        self.root = root
        self.root.title("Multi-Beacon Monitor & Alarm System")
        self.root.geometry("700x500")
        self.root.configure(bg="#1a1a2e")
        
        self.on_manual_alarm = on_manual_alarm
        self.alarm_rules = alarm_rules
        self.last_update = 0

        # Color scheme
        self.colors = {
            "bg": "#1a1a2e",
            "card": "#16213e",
            "text": "#eaeaea",
            "safe": "#4ade80",
            "weak": "#fbbf24",
            "alarm": "#ef4444",
            "lost": "#6b7280"
        }

        # Styles
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", 
                       background=self.colors["card"], 
                       foreground=self.colors["text"],
                       fieldbackground=self.colors["card"],
                       font=("Consolas", 11),
                       rowheight=30)
        style.configure("Treeview.Heading", 
                       font=("Helvetica", 11, "bold"),
                       background="#0f3460",
                       foreground="white")
        style.map("Treeview", background=[("selected", "#0f3460")])

        # --- Header ---
        header = tk.Frame(root, bg=self.colors["bg"], pady=10)
        header.pack(fill=tk.X, padx=20)
        
        tk.Label(header, text="📡 Multi-Beacon Tracking System", 
                font=("Helvetica", 18, "bold"), 
                fg="white", bg=self.colors["bg"]).pack(side=tk.LEFT)
        
        # Settings button
        btn_settings = tk.Button(header, text="⚙️ Settings", 
                                 bg="#4b5563", fg="white",
                                 font=("Arial", 10, "bold"),
                                 cursor="hand2",
                                 command=self._open_settings)
        btn_settings.pack(side=tk.RIGHT, padx=(10, 0))
        
        self.lbl_mqtt_status = tk.Label(header, text="● MQTT: Connecting...", 
                                        fg="#fbbf24", bg=self.colors["bg"],
                                        font=("Consolas", 10))
        self.lbl_mqtt_status.pack(side=tk.RIGHT)

        # --- Threshold Info ---
        info_frame = tk.Frame(root, bg=self.colors["card"], pady=5)
        info_frame.pack(fill=tk.X, padx=20, pady=(10, 0))
        
        tk.Label(info_frame, 
                text=f"🟢 Safe Zone (Silent): RSSI > {settings.SAFE_RSSI_THRESHOLD} dBm  |  🔴 Alarm Zone (Active): RSSI < {settings.ALARM_RSSI_THRESHOLD} dBm",
                font=("Consolas", 9), fg="#888", bg=self.colors["card"]).pack()

        # --- Beacon Table ---
        table_frame = tk.Frame(root, bg=self.colors["bg"])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Treeview
        columns = ("status", "id", "name", "rssi", "last_seen")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        
        # Column headings
        self.tree.heading("status", text="Status")
        self.tree.heading("id", text="Beacon ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("rssi", text="RSSI")
        self.tree.heading("last_seen", text="Last Seen")
        
        # Column widths
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("id", width=100, anchor="center")
        self.tree.column("name", width=180, anchor="w")
        self.tree.column("rssi", width=100, anchor="center")
        self.tree.column("last_seen", width=120, anchor="center")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Summary Panel ---
        summary_frame = tk.Frame(root, bg=self.colors["card"], pady=15)
        summary_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.lbl_summary = tk.Label(summary_frame, 
                                    text="Tracking 0 beacons | Waiting for data...", 
                                    font=("Helvetica", 12),
                                    fg=self.colors["text"], 
                                    bg=self.colors["card"])
        self.lbl_summary.pack()

        # --- Controls ---
        btn_frame = tk.Frame(root, bg=self.colors["bg"], pady=10)
        btn_frame.pack(fill=tk.X, padx=20)
        
        btn_alarm = tk.Button(btn_frame, 
                             text="🔔 TRIGGER ALARM", 
                             bg="#dc2626", fg="white", 
                             font=("Arial", 11, "bold"),
                             activebackground="#b91c1c",
                             cursor="hand2",
                             command=self.manual_trigger)
        btn_alarm.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, padx=5)
        
        btn_silence = tk.Button(btn_frame, 
                               text="🔇 SILENCE ALL", 
                               bg="#059669", fg="white", 
                               font=("Arial", 11, "bold"),
                               activebackground="#047857",
                               cursor="hand2",
                               command=self.silence_all)
        btn_silence.pack(side=tk.RIGHT, fill=tk.X, expand=True, ipady=10, padx=5)

        # Initialize table with watchlist
        self._init_beacon_table()

    def _init_beacon_table(self):
        """Initialize table with beacons from watchlist."""
        try:
            watchlist = settings.load_watchlist()
            for beacon_id, info in watchlist.items():
                self.tree.insert("", tk.END, iid=beacon_id, values=(
                    "⚫ WAITING",
                    beacon_id,
                    info.get("name", f"Beacon {beacon_id}"),
                    "-- dBm",
                    "Never"
                ))
        except Exception as e:
            print(f"Failed to init beacon table: {e}")

    def set_mqtt_connected(self, connected):
        if connected:
            self.lbl_mqtt_status.config(text="● MQTT: Connected", fg=self.colors["safe"])
        else:
            self.lbl_mqtt_status.config(text="● MQTT: Disconnected", fg=self.colors["alarm"])

    def update_beacon_states(self, beacon_states):
        """
        Update the table with current beacon states.
        
        Args:
            beacon_states: List of dicts with beacon state info from AlarmRules
        """
        self.last_update = time.time()
        
        safe_count = 0
        alarm_count = 0
        lost_count = 0
        
        for state in beacon_states:
            beacon_id = state.get("id", "")
            name = state.get("name", f"Beacon {beacon_id}")
            rssi = state.get("rssi", 0)
            status = state.get("state", "UNKNOWN")
            last_seen = state.get("last_seen", 0)
            
            # Status icon and color
            if status == "SAFE":
                status_text = "🟢 SAFE"
                safe_count += 1
            elif status == "WEAK":
                status_text = "🟡 WEAK"
            elif status == "ALARM":
                status_text = "🔴 ALARM"
                alarm_count += 1
            elif status == "LOST":
                status_text = "⚫ LOST"
                lost_count += 1
            else:
                status_text = "⚪ WAITING"
            
            # Format last seen
            if last_seen > 0:
                time_str = time.strftime('%H:%M:%S', time.localtime(last_seen))
            else:
                time_str = "Never"
            
            # Format RSSI
            rssi_text = f"{rssi} dBm" if rssi != 0 else "-- dBm"
            
            # Update or insert row
            try:
                if self.tree.exists(beacon_id):
                    self.tree.item(beacon_id, values=(
                        status_text, beacon_id, name, rssi_text, time_str
                    ))
                else:
                    self.tree.insert("", tk.END, iid=beacon_id, values=(
                        status_text, beacon_id, name, rssi_text, time_str
                    ))
            except Exception as e:
                print(f"Error updating beacon {beacon_id}: {e}")
        
        # Update summary
        total = len(beacon_states)
        if alarm_count > 0:
            summary = f"🔴 {alarm_count} ALARM | Tracking {total} beacons"
            self.lbl_summary.config(fg=self.colors["alarm"])
        elif lost_count > 0:
            summary = f"⚫ {lost_count} LOST | Tracking {total} beacons"
            self.lbl_summary.config(fg=self.colors["lost"])
        elif safe_count > 0:
            summary = f"✅ All {safe_count} beacons SAFE"
            self.lbl_summary.config(fg=self.colors["safe"])
        else:
            summary = f"Tracking {total} beacons | Waiting for data..."
            self.lbl_summary.config(fg=self.colors["text"])
        
        self.lbl_summary.config(text=summary)

    def update_watchdog(self):
        """Called periodically to refresh beacon states."""
        if self.alarm_rules:
            states = self.alarm_rules.get_all_states()
            self.update_beacon_states(states)

    def manual_trigger(self):
        """Trigger alarm manually."""
        self.on_manual_alarm()
    
    def silence_all(self):
        """Silence all alarms."""
        print("🔇 Silence all requested")
        # TODO: Could call alarm_rules.send_silence_command() for each beacon
    
    def _open_settings(self):
        """Open the device configuration window."""
        open_config_window(self.root, self._on_config_saved)
    
    def _on_config_saved(self):
        """Callback when configuration is saved."""
        print("🔄 Configuration saved, refreshing...")
        # Refresh beacon table with new configuration
        self.tree.delete(*self.tree.get_children())
        self._init_beacon_table()
