# 🔔 LoRaWAN UiTM - Indoor Asset Tracking & Perimeter Alarm System

A comprehensive LoRaWAN-based indoor asset tracking and perimeter alarm system developed at **Universiti Teknologi MARA (UiTM)**. This system monitors Bluetooth beacons via a LoRaWAN network and triggers physical alarms when assets move outside designated safe zones.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![LoRaWAN](https://img.shields.io/badge/LoRaWAN-ChirpStack-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Hardware Requirements](#hardware-requirements)
- [Software Requirements](#software-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## 🎯 Overview

This system provides real-time asset tracking using:

- **Bluetooth Beacons** (Lansitec B002) attached to assets
- **Bluetooth Gateway** to detect beacon signals
- **Macro Sensor** with built-in buzzer for physical alarms
- **LoRaWAN Network** for long-range, low-power communication
- **ChirpStack** as the network server
- **Python Application** for alarm logic and GUI monitoring

### Use Cases

- Laboratory equipment anti-theft protection
- High-value asset perimeter monitoring
- Multi-floor building asset tracking
- Real-time proximity-based alarm systems

---

## ✨ Features

| Feature                        | Description                                                    |
| ------------------------------ | -------------------------------------------------------------- |
| 🎯 **Real-time Tracking**      | Monitor multiple beacons simultaneously with live RSSI updates |
| 🔔 **Physical Alarm**          | Trigger buzzer on Macro Sensor when beacon leaves safe zone    |
| 📊 **GUI Dashboard**           | Tkinter-based monitor showing beacon states and alarm status   |
| 🔧 **Configurable Thresholds** | Adjustable RSSI thresholds and debounce timing                 |
| 📡 **MQTT Integration**        | Seamless integration with ChirpStack via MQTT                  |
| 🐳 **Docker Support**          | Pre-configured ChirpStack Docker deployment                    |

---

## 🏗️ Architecture

```
┌─────────────────┐     BLE      ┌──────────────────┐
│  Bluetooth      │ ──────────►  │  Bluetooth       │
│  Beacons (B002) │              │  Gateway         │
└─────────────────┘              └────────┬─────────┘
                                          │ LoRaWAN
                                          ▼
┌─────────────────┐              ┌──────────────────┐
│  Macro Sensor   │ ◄─────────── │  LoRaWAN Gateway │
│  (Alarm Buzzer) │   Downlink   │  (RAK WisGate)   │
└─────────────────┘              └────────┬─────────┘
                                          │ UDP/TCP
                                          ▼
                                 ┌──────────────────┐
                                 │  ChirpStack      │
                                 │  Network Server  │
                                 └────────┬─────────┘
                                          │ MQTT
                                          ▼
                                 ┌──────────────────┐
                                 │  Python App      │
                                 │  (Alarm Logic)   │
                                 └──────────────────┘
```

---

## 🔧 Hardware Requirements

| Device            | Model         | Purpose                                   |
| ----------------- | ------------- | ----------------------------------------- |
| Bluetooth Beacon  | Lansitec B002 | Asset tags (attach to items)              |
| Bluetooth Gateway | Lansitec      | Detects beacons, sends data via LoRaWAN   |
| Macro Sensor      | Lansitec      | Physical alarm with buzzer                |
| LoRaWAN Gateway   | RAK WisGate   | Bridge between devices and network server |

---

## 💻 Software Requirements

- **Python** 3.8 or higher
- **Docker & Docker Compose** (for ChirpStack)
- **MQTT Broker** (included in ChirpStack Docker)
- **Git** (for version control)

### Python Dependencies

```
paho-mqtt
```

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Msyazlie/LoRaWAN-UiTM.git
cd LoRaWAN-UiTM
```

### 2. Start ChirpStack (Docker)

```bash
cd chirpstack-docker
docker-compose up -d
```

Access ChirpStack web UI at: `http://localhost:8080`

### 3. Install Python Dependencies

```bash
cd python-app
pip install -r requirements.txt
```

### 4. Configure Devices in ChirpStack

1. Create an Application in ChirpStack
2. Add your devices (Bluetooth Gateway, Macro Sensor)
3. Configure device profiles with correct codecs
4. Enable **Class C** for Macro Sensor (required for downlinks)

---

## ⚙️ Configuration

### Beacon Watchlist (`beacons.json`)

Define which beacons to track:

```json
{
  "beacons": [
    { "id": "64B0", "name": "Asset Tag #1" },
    { "id": "64AF", "name": "Asset Tag #2" },
    { "id": "64AE", "name": "Asset Tag #3" }
  ]
}
```

### Application Settings (`src/config/settings.py`)

| Setting                | Default            | Description                       |
| ---------------------- | ------------------ | --------------------------------- |
| `BROKER_ADDRESS`       | `127.0.0.1`        | MQTT broker address               |
| `BROKER_PORT`          | `1883`             | MQTT broker port                  |
| `SAFE_RSSI_THRESHOLD`  | `-80` dBm          | Above = Safe Zone                 |
| `ALARM_RSSI_THRESHOLD` | `-85` dBm          | Below = Alarm Zone                |
| `DEBOUNCE_SECONDS`     | `5`                | Weak signal duration before alarm |
| `MAX_SILENCE_DURATION` | `120`              | No signal duration before alarm   |
| `ALARM_TARGET_EUI`     | `70b3d5a4d31205cf` | DevEUI of Macro Sensor            |

### RSSI Threshold Guide

```
Signal Strength (RSSI)        Zone              Action
─────────────────────────────────────────────────────────
     > -80 dBm       →    🟢 SAFE ZONE     →    No alarm
-85 to -80 dBm       →    🟡 BUFFER ZONE   →    Monitoring
     < -85 dBm       →    🔴 ALARM ZONE    →    Trigger alarm
```

---

## 🖥️ Usage

### Start the Application

```bash
cd python-app
python main.py
```

### Application Startup Output

```
============================================================
🔔 Proximity Alarm System
============================================================
   RSSI Threshold: -80 dBm
   > -80 → ALARM (beacon detected far)
   ≤ -80 → SAFE (beacon detected nearby)
============================================================

📋 Tracking 3 beacons:
   • 64B0: Asset Tag #1
   • 64AF: Asset Tag #2
   • 64AE: Asset Tag #3

🎯 System Ready. Monitoring for beacons...
============================================================
```

### GUI Monitor

The application launches a GUI window showing:

- **Beacon List**: All tracked beacons with real-time RSSI values
- **Zone Status**: Current zone (SAFE/BUFFER/ALARM) for each beacon
- **Last Seen**: Timestamp of last beacon detection
- **MQTT Status**: Connection status indicator
- **Manual Alarm**: Button to manually trigger alarm for testing

---

## 📁 Project Structure

```
LoRaWAN-UiTM/
├── 📂 chirpstack-docker/       # ChirpStack Docker deployment
│   ├── docker-compose.yml      # Docker services configuration
│   └── configuration/          # ChirpStack config files
│
├── 📂 python-app/              # Main Python application
│   ├── main.py                 # Application entry point
│   ├── beacons.json            # Beacon watchlist
│   ├── settings.py             # Legacy settings (deprecated)
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile              # Container build file
│   │
│   ├── 📂 src/
│   │   ├── 📂 config/          # Configuration management
│   │   │   └── settings.py     # Main settings file
│   │   │
│   │   ├── 📂 logic/           # Business logic
│   │   │   └── alarm_rules.py  # Alarm trigger/silence logic
│   │   │
│   │   ├── 📂 services/        # External services
│   │   │   ├── mqtt_client.py  # MQTT client wrapper
│   │   │   └── decoder.py      # Payload decoder
│   │   │
│   │   └── 📂 ui/              # User interface
│   │       └── monitor_window.py # Tkinter GUI
│   │
│   └── 📂 decoders/            # Device-specific decoders
│
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

---

## 🔍 Troubleshooting

### Common Issues

| Problem                  | Solution                                                    |
| ------------------------ | ----------------------------------------------------------- |
| **MQTT not connecting**  | Verify ChirpStack is running and MQTT broker is accessible  |
| **No beacon data**       | Check if Bluetooth Gateway is registered in ChirpStack      |
| **Alarm not triggering** | Ensure Macro Sensor is in Class C mode and FPort is correct |
| **Wrong RSSI readings**  | Adjust thresholds based on your environment                 |

### Debug Commands

```bash
# Check Docker containers
docker-compose ps

# View ChirpStack logs
docker-compose logs -f chirpstack

# Test MQTT connection
mosquitto_sub -h localhost -t "application/#" -v
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is developed for educational and research purposes at **Universiti Teknologi MARA (UiTM)**.

---

## 👨‍💻 Author

**Msyazlie** - [GitHub Profile](https://github.com/Msyazlie)

---

<p align="center">
  <i>Developed with ❤️ at UiTM</i>
</p>
