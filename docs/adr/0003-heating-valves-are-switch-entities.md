# Heating valves are switch entities

A heating-circuit Load physically drives a valve, but it is exposed as a `switch`, not a `valve` entity, because Versatile Thermostat (10.6.3) only accepts switch, input_boolean, select, input_select or climate as the underlying of an on/off thermostat. Changing the entity type later would break every VTherm that uses it, so revisit only once VTherm accepts `valve` entities.
