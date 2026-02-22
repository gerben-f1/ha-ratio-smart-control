Ratio Smart Charging Control (HACS)
This integration provides Dynamic Load Balancing for Ratio Electric EV Chargers using Home Assistant. It acts as the "brain" on top of a Modbus connection, ensuring your car charges as fast as possible without tripping your main fuse.
Features
• ⚡ Fast-Down Response: Instant current reduction when household power usage spikes (e.g., using a kettle or oven).
• 📈 Stepped Slow-Up: Increases charging current in gentle 2A increments after 30 seconds of stability to prevent oscillation.
• 🎯 Smart Calculation: Automatically determines the available room based on the busiest phase (3-phase support).
• 📝 Human Readable Status: Translates Modbus codes (1-5) into clear text like "Charging" or "Finished".
🛠 Prerequisites (Very Important!)
Before installing this HACS integration, you must have a working Modbus connection to your Ratio charger. This integration uses a Serial/USB RS485 adapter.
1. Modbus Configuration
Add the following to your configuration.yaml. Note: Ensure the port matches your specific USB-to-RS485 stick ID.

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
      - name: "Ratio Voltage L2"
        address: 16408
        slave: 127
        input_type: input
        data_type: uint32
        scale: 0.1
        unit_of_measurement: V
        device_class: voltage
      - name: "Ratio Voltage L3"
        address: 16410
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
      - name: "Ratio Session Energy"
        address: 16416
        slave: 127
        input_type: input
        data_type: uint32
        scale: 0.001
        precision: 2
        unit_of_measurement: kWh
        device_class: energy
      - name: "Ratio Comm Timeout"
        address: 16418
        slave: 127
        input_type: input
        data_type: uint32
      - name: "Ratio Modbus Address Status"
        address: 16420
        slave: 127
        input_type: input
        data_type: uint32
      - name: "Ratio Modbus Mode"
        address: 16422
        slave: 127
        input_type: input
        data_type: uint32
    numbers:
      - name: "Ratio Laadstroom Limiet"
        unique_id: ratio_charging_limit
        address: 16640
        slave: 127
        native_min_value: 6
        native_max_value: 20
        native_step: 1
        unit_of_measurement: "A"
🚀 Installation
Step 1: Add to HACS
1. Open HACS in Home Assistant.
2. Click the three dots in the top right corner and select Custom repositories.
3. Paste the URL of this GitHub repository.
4. Select Integration as the category and click Add.
5. Find "Ratio Smart Charging Control" and click Download.
6. Restart Home Assistant.
Step 2: Configure the Integration
1. Go to Settings > Devices & Services.
2. Click Add Integration and search for Ratio Smart Charging Control.
3. A configuration menu will appear. Select your sensors:
• L1/L2/L3 Grid Sensors: Your P1 meter current sensors.
• Ratio Current Sensor: Select sensor.ratio_current_l1 (or a combined total if available).
• Ratio State Sensor: Select sensor.ratio_charging_state.
• Settings: Define your main fuse (e.g., 25A) and your charger's circuit limit (e.g., 20A).
⚙️ How it works
The integration creates a hidden calculator that constantly monitors your grid usage.
1. Safety First: If the total load on any phase exceeds your Main Fuse - Safety Margin, it sends a Modbus command to the charger to drop the current immediately.
2. Stability: When the household load drops, the integration waits for 30 seconds. If the power is still available, it increases the charging rate by 2 Amperes. This repeats until the maximum allowed current is reached.
🤝 Support
If you encounter issues with the Modbus connection, check your RS485 wiring (A and B wires) and ensure the Slave ID is set to 127.
