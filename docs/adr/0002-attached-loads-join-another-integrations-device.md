# Attached Loads join another integration's device

An Output whose Load is an existing HA device (e.g. a Versatile Thermostat) has its entity added to that device, the way `switch_as_x` does, rather than living only on the Board device. This puts the heating valve next to the thermostat that drives it, at the cost of an entity that sits on a device this integration doesn't own. If that device is deleted, the Output falls back to its Board.
