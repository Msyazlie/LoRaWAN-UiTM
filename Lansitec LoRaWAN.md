# Lansitec LoRaWAN Bluetooth Proximity Gateway - Downlink Commands

This document outlines the downlink message structures for the Lansitec LoRaWAN Bluetooth Proximity Gateway.

**Note:**
* **RSSI Calculation:** For signed integer RSSI fields (e.g., Asset RSSI Threshold), the value is calculated as `Decimal Value - 256 = dBm`.
* **Time Units:** Pay attention to specific units (e.g., 5s vs 30s) for different interval settings.

---

## 1. LoRa Configuration (Type 0x8)
**Description:** NS can use this message to configure LoRa parameters.

| Byte | Field | Bits | Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Type** | 7-4 | `0x8` | Message type. |
| | **ADR** | 3 | `0` or `1` | `0`: OFF (Keep ADR off), `1`: ON. |
| | **RFU** | 2-0 | `0x0` | Reserved for future usage. |
| **2** | **DR** | 7-4 | `0-3` | Data Rate (DR0–DR3). |
| | **RFU** | 3-0 | `0` | Reserved for future usage. |
| **3** | **Mode** | 7-5 | `1-7` | Band mode (cannot be changed currently). |
| | **Power** | 4-0 | `0-20` | Configure transmit power (unit: dBm). |

---

## 2. Gateway Configuration (Type 0x9)
**Description:** NS can use this message to configure Gateway parameters.

| Byte | Field | Bits | Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Type** | 7-4 | `0x9` | Message type. |
| | **SwitchEN** | 3 | `0` or `1` | **SocketSync Only.** `1`: Enable, `0`: Disable. If disabled, the switch cannot be used to shut down the device. |
| | **RFU** | 2-0 | `0x0` | Reserved. |
| **2-3** | **POS** | 15-0 | `0-65535` | Position report interval. **Unit: 5s**. Default: `0x0006` (30s). Big Endian. |
| **4** | **HB** | 7-0 | `1-255` | Heartbeat message period. **Unit: 30s**. Default: `0x0A` (5 mins). |

---

## 3. Command Request (Type 0xA)
**Description:** Request the gateway to execute instructions (Reboot, Start/Stop BLE, Search, etc.).

| Byte | Field | Bits | Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Type** | 7-4 | `0xA` | Message type. |
| | **Command** | 3-0 | `0x2`-`0xD` | Specific command (see table below). |
| **2** | **MSGID** | 7-0 | `0-255` | Sequence number for ACK. Gateway responds with this ID. |
| **3+** | **Value** | - | Var | Parameter value specific to the command. |

### Command List (Byte 1, Bits 3-0)

| Cmd | Name | Byte 3+ Description |
| :--- | :--- | :--- |
| **0x2** | Register | **Value:** N/A (Byte 3 is RFU). <br>Request gateway to send register and alarm config messages. |
| **0x3** | Reboot | **Value:** N/A (Byte 3 is RFU). <br>Reboot the gateway. |
| **0x4** | Stop BLE | **Value:** N/A (Byte 3 is RFU). <br>Stop continuous Bluetooth receiving. |
| **0x5** | Start BLE | **Value:** N/A (Byte 3 is RFU). <br>Start continuous Bluetooth receiving. |
| **0x6** | Change Start Time | **Value (1 Byte):** Signed Int (-127 to 127). <br>Advance (negative) or delay (positive) receiving start time. |
| **0x7** | Change Duration | **Value (1 Byte):** New duration (seconds). <br>Default is 8s. |
| **0x8** | Set Beacon QTY | **Value (1 Byte):** `1-255`. <br>Max beacons reported per interval. Value = Limit / 2. (e.g., Set `5` for limit of `10`). Default `0xFE` (508 beacons). |
| **0xC** | Beacon Search | **Value (2 Bytes):** `Minor` value (Short). <br>Find specific beacon by Minor ID; emits 60s audible/light alarm. |
| **0xD** | Asset RSSI Thresh | **Value (1 Byte):** Signed Int. <br>Set asset beacon receive threshold. (e.g., `0xBA` = 186; 186-256 = -70dBm). |

---

## 4. Separate Alarm Configuration (Type 0xB)
**Description:** Configure alarm parameters separately.

| Byte | Field | Bits | Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Type** | 7-4 | `0xB` | Message type. |
| | **RFU** | 3-0 | `0x0` | Reserved. |
| **2** | **MSGID** | 7-0 | `0-255` | Sequence number for ACK. |
| **3** | **Param Type** | 7-0 | `0x00`-`0x06` | The specific parameter to change (see table below). |
| **4+** | **Value** | - | Var | The new value for the parameter. |

### Alarm Parameter Types (Byte 3)

| Type | Parameter | Value Format | Description |
| :--- | :--- | :--- | :--- |
| **0x00** | Alarm RSSI Threshold | 1 Byte (Signed) | Trigger alarm when RSSI >= this value. Default: -65dBm. |
| **0x01** | Buzzer Volume | 1 Byte | `0` (silent) to `4` (loudest). |
| **0x02** | Buzzer Duration | 1 Byte | **Unit: 10s**. Default: `0x03` (30s). `0` = Mute. |
| **0x03** | Alarm Beacon QTY | 1 Byte | Max quantity of beacons triggering alarm to report. Default: `0xFF`. |
| **0x04** | Alarm Receiving Time | 1 Byte | **Unit: 1s**. Delay before first alarm beacon list report. Default: 14s. |
| **0x05** | Report Interval | **2 Bytes** | **Unit: 5s**. Interval for reporting alarm beacon info. Default: `0x0006` (30s). |
| **0x06** | Silent Button | 1 Byte | `0`: Disable, `1`: Enable. Allows button to turn off audible alarm. |