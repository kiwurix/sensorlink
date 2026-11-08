# SensorLink

A client-server sensor network simulator written in Python. Simulated sensors send readings to a monitoring server using a custom binary protocol over UDP.

## Features

- Four sensor profiles: ThermoNode, WindSense, RainDetect and AirQualityBox.
- Device registration with server-issued tokens.
- Bit-packed messages with timestamps and battery status.
- CRC32 validation, acknowledgements and retransmission.
- Activity checks for inactive sensors.
- Tkinter interfaces for the server and client simulator.
- Controls for sending custom readings, corrupting checksums and suppressing acknowledgements.

## How it works

The client registers a sensor and receives a token. It then sends readings with a CRC32 checksum. The server acknowledges valid readings or requests a retry when the checksum is wrong. The client also resends data when a response is missing.

`server/core.py` contains the server, `tester/device.py` contains the sensor client, and `messages.py` handles binary message encoding. The original `tester` package name refers to the client simulator.

## Run

Requires Python 3.11+ and Tkinter. Install the dependency in a virtual environment:

```bash
python -m venv .venv
```

Activate it with `.venv\Scripts\activate` on Windows or `source .venv/bin/activate` on Linux/macOS, then run:

```bash
python -m pip install -r requirements.txt
python -m server.gui
```

In a second terminal with the same environment activated:

```bash
python -m tester.gui
```

1. In the **Server** window, configure `127.0.0.1:50000` and click **Apply**. This starts listening.
2. In **Test program**, configure the devices with the same address and port.
3. Enable **Auto send** to register sensors and send generated readings.

For a LAN demo, use the server's LAN IPv4 address in both configurations and allow the chosen UDP port. Linux may require the `python3-tk` system package.

## Try it

- **Checksum error** sends a reading with a bad checksum. The server requests a retry.
- **Do not acknowledge the data message** suppresses the next three acknowledgements for a selected sensor, triggering retransmission.
- **Sensor activity mechanism check** temporarily pauses a sensor to exercise activity probes.

Register devices with automatic sending before trying these scenarios. For custom readings, keep the generated field order and numeric precision.

## Protocol

Each message starts with a 52-bit header: message type (3 bits), sensor profile (2), Unix timestamp (32), battery flag (1) and token (14). Data messages add profile-specific readings and a 32-bit CRC. Messages are padded to whole bytes.

Message types: `REGISTRATION`, `TOKEN`, `DATA`, `INVALID_TOKEN`, `ACK`, `RETRY`, `ACTIVITY_CHECK`. Sensor fields and ranges are defined in `tester/info.py`. CRC32 covers the canonical reading text, not the full header.
