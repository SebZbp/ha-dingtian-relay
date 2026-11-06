# Dingtian Relay

Home Assistant integration for Dingtian relay Boards that publish over MQTT.
It shows each Board as one device with its Outputs, Inputs and health, all
local, no cloud.

## Install

1. In HACS, add this repository as a custom repository (type: Integration),
   install **Dingtian Relay** and restart Home Assistant.
2. The MQTT integration must be set up and the Boards must publish to the same
   broker.

## Usage

- **Discovery**: a Board announcing its serial on MQTT shows up as a discovered
  device. Confirm it, optionally change its name and pick an area. A Board is
  never offered twice; Ignore works as usual. There is no manual setup.
- **Entities per Board**:
  - one switch per Output (`Output 1`, `Output 2`, ...);
  - one binary sensor per Input (`Input 1`, ...);
  - **All on** and **All off** buttons;
  - diagnostic entities: connectivity, IP address and MAC address.
  The number of Outputs and Inputs comes from the Board; if it does not report
  them, 8 of each are assumed.
- The device also carries the serial and the hardware and software versions the
  Board publishes, and a link to its web page. Entities become unavailable
  while the Board reports itself offline.
- **Diagnostics**: download them from the device page. They include the last
  value of every topic the Board published, and which ones were not recognised.
