Many thanks to Mel Wilson for the original creation of sump.py (part of pyLogicSniffer)

Settings:
    port
    divider
    read_count
    delay_count
    inverted
    external
    filter
    demux
    channel_groups
    trigger_enable (str)
    ... triggers
    trigger_mask
    trigger_values
    trigger_delay
    trigger_level
    trigger_channel
    trigger_serial
    trigger_start

Metadata [example cap from ols]
    0x01: device name [Open Logic Sniffer ...]
    0x02: firmware version [3.07]
    0x03: pic version []
    0x20: probes []
    0x21: sample memory size [24576]
    0x22: dynamic memory size []
    0x23: maximum rate [200000000]
    0x24: protocol version []
    0x40: probes [32]
    0x41: protocol version [2]

Operations
    capture
    close
    reset
    send_settings (automatic)
    port
    timeout
    xon/xoff

Capture object:
    raw data
    data by channel
    data by member (named channel)
    data by group (of members)
    filter operations (trigger on x, parse by state of x.... etc?)

Channel/Group properties:
    name
    members
    invert
    format: analog/digital[hex, bin, oct, etc...]


Settings should be device independent.
Capture should store information about:
    device settings (trigger, sampling frequency, etc...)
    channel information (names, groups, etc...)
    raw data
