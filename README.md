# ⚡ Ratio Smart Charging Control (HACS)

This integration provides **Dynamic Load Balancing** for Ratio Electric EV Chargers using Home Assistant. It acts as the "brain" on top of a Modbus connection, ensuring your car charges as fast as possible without tripping your main fuse.

---

## ✨ Features
* **⚡ Fast-Down Response:** Instant current reduction when household power usage spikes (e.g., using a kettle or oven).
* **📈 Stepped Slow-Up:** Increases charging current in gentle increments after stability is detected to prevent oscillation.
* **🎯 Smart Calculation:** Automatically determines the available room based on the busiest phase (3-phase support).
* **📝 Human Readable Status:** Translates raw Modbus codes into clear text like "Charging", "Finished", or "Stand-by".

---

## 🛠 Prerequisites (Very Important!)
Before installing this HACS integration, you must have a working **Modbus connection** to your Ratio charger. This integration is designed for setups using a Serial/USB RS485 adapter.

### Modbus Configuration
Add the following to your `configuration.yaml`. 
> [!IMPORTANT]  
> Ensure the `port` matches your specific USB-to-RS485 stick ID.

```yaml
modbus:
  - name: modbus_ratio
    type: serial
    method: rtu
    port: "/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A5069RR4-if00-port0"
    baudrate: 9600
    stopbits: 1
    bytesize: 8
    parity: N
    timeout: 5
    sensors:
      - name: "Ratio Firmware Version"
        address: 16388
        slave: 127
        input_type: input
        data_type: uint32
      - name: "Ratio User Max Current"
        address: 16390
        slave: 127
        input_type: input
        data_type: uint32
        scale: 0.1
        precision: 1
        unit_of_measurement: A
        device_class: current
      - name: "Ratio Error Code"
        address: 16392
        slave: 127
        input_type: input
        data_type: uint32
      - name: "Ratio Socket Lock State"
        address: 16394
        slave: 127
        input_type: input
        data_type: uint32
      - name: "Ratio Charging State"
        unique_id: ratio_charging_state
        address: 16396
        slave: 127
        input_type: input
        data_type: uint32
      - name: "Ratio Current Limit"
        address: 16398
        slave: 127
        input_type: input
        data_type: uint32
        scale: 0.1
        unit_of_measurement: A
        device_class: current
      - name: "Ratio Current L1"
        unique_id: current_l1
        address: 16400
        slave: 127
        input_type: input
        data_type: uint32
        scale: 0.1
        precision: 1
        unit_of_measurement: A
        device_class: current
      - name: "Ratio Current L2"
        unique_id: current_l2
        address: 16402
        slave: 127
        input_type: input
        data_type: uint32
        scale: 0.1
        precision: 1
        unit_of_measurement: A
        device_class: current
      - name: "Ratio Current L3"
        unique_id: current_l3
        address: 16404
        slave: 127
        input_type: input
        data_type: uint32
        scale: 0.1
        precision: 1
        unit_of_measurement: A
        device_class: current
      - name: "Ratio Voltage L1"
        address: 16406
        slave: 127
        input_type: input
        data_type: uint32
        scale: 0.1
        unit_of_measurement: V
        device_class: voltage
      - name: "Ratio Active Power"
        address: 16412
        slave: 127
        input_type: input
        data_type: uint32
        unit_of_measurement: W
        device_class: power
      - name: "Ratio Total Energy"
        address: 16414
        slave: 127
        input_type: input
        data_type: uint32
        scale: 0.001
        precision: 1
        unit_of_measurement: kWh
        device_class: energy
        state_class: total_increasing
🚀 Installation
Step 1: Add to HACS
1. Open HACS in Home Assistant.
2. Click the three dots in the top right corner and select Custom repositories.
3. Paste the URL of this GitHub repository.
(https://github.com/gerben-f1/ha-ratio-smart-control)
4. Select Integration as the category and click Add.
5. Find Ratio Smart Charging Control and click Download.
6. Restart Home Assistant.
Step 2: Configure the Integration
1. Go to Settings > Devices & Services.
2. Click Add Integration and search for Ratio Smart Charging Control.
3. A configuration menu will appear. Select your sensors:
• Grid Sensors (L1/L2/L3): Your P1 meter current sensors.
• Ratio Current Sensors: Select the L1/L2/L3 sensors from the Modbus configuration above.
• Ratio State Sensor: Select sensor.ratio_charging_state.
• Settings: Define your main fuse limit (e.g., 25A).
⚙️ How it works
The integration creates a background logic controller that constantly monitors your grid usage:
1. Safety First: If the total load on any phase exceeds your Main Fuse limit, it sends a Modbus command to the charger to drop the current immediately.
2. Stability: When household load drops, the integration ensures the power is stable before increasing the charging rate.
3. Efficiency: It always tries to maximize the charging speed (up to 18A-20A depending on your hardware) while keeping your house safe.
🤝 Support
If you encounter issues with the Modbus connection:
• Check your RS485 wiring (A and B wires).
• Ensure the Slave ID is set to 127 (default for Ratio).
• Check the Home Assistant logs for Modbus timeout errors.
