# One config entry per Board, discovered over MQTT

Each Board is its own config entry, discovered from the topics it publishes on HA's existing MQTT integration (no HTTP or Modbus). This deliberately differs from ha-edisio-integration, which has one hub entry (the Dongle) with Devices underneath: there, one radio carries every Device, whereas every Board talks for itself, so per-Board entries give reload, Ignore and removal per Board for free. Loads are stored in the options of their Board's entry.
