import socket
from helpers import calculate_checksum
from messages import *
import random
from datetime import datetime
from typing import Callable
import time
from threading import Thread


class Server:
    def __init__(self, log: Callable[[str], None]) -> None:
        self.sock: socket.socket = None
        self.connected_devices: dict[str, dict[str, str]] = None

        self.log: Callable[[str, bool], None] = log

        self.is_listening: bool = False
        self.main_thread: Thread = None



    def configure(self, ip: str, port: int):
        self.quit()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((ip, port))
        self.connected_devices = {}

        self.listen()


    def send_response(self, client, message):
        self.sock.sendto(message.to_bytes(), client)

    def listen(self):
        self.is_listening = True
        if not self.main_thread or not self.main_thread.is_alive():
            self.main_thread = Thread(target=self._listening, daemon=True)
            self.main_thread.start()

    def stop_listening(self):
        self.is_listening = False


    def _listening(self):
        Thread(target= self.activity_check, daemon= True).start()

        while self.is_listening:
            try:
                data, addr = self.sock.recvfrom(1024)
                message = Message.from_bytes(data)

                self.handle_message(message, addr)
            except OSError:
                time.sleep(1)



    def handle_message(self, message, addr):
        message_type = message.message_type

        if message_type == MessageType.REGISTRATION:
            self.handle_registration(message, addr)

        elif self.check_token(message, addr):
            if message_type == MessageType.DATA:
                self.handle_data(message, addr)

    def check_token(self, message, addr):
        device_type = message.device_type
        token = message.device_token
        low_battery = message.low_battery

        try:

            if self.connected_devices[device_type]["token"] != token:
                self.send_response(
                    addr, InvalidTokenMessage(
                            device_type, datetime.now().timestamp(), low_battery, token
                                   )
                                   )
                return False
            else:
                return True
        except KeyError:
            self.send_response(
                addr, InvalidTokenMessage(
                    device_type, datetime.now().timestamp(), low_battery, token
                )
            )
            return False

    def handle_registration(self, message, addr):
        token = random.randint(1000, 9999)
        device_type = message.device_type
        low_battery = message.low_battery

        current_time = datetime.now()
        self.connected_devices[device_type] = {
            "token" : token,
            "last_seen" : current_time,
            "address" : addr,
            "ignore" : 0
        }

        timestamp = current_time.timestamp()
        self.log(f"INFO: {device_type} REGISTERED at {timestamp}")

        self.send_response(
            addr, TokenMessage(device_type, timestamp, low_battery, token)
        )


    def handle_data(self, message, addr):
        device_type = message.device_type
        token = message.device_token
        timestamp = message.timestamp
        data = message.data
        low_battery = message.low_battery
        checksum = message.checksum

        current_time = datetime.now()
        self.connected_devices[device_type]["last_seen"] = current_time

        if calculate_checksum(data) != int(checksum):
            print(message, checksum, calculate_checksum(data))
            self.log(f"INFO: {device_type} CORRUPTED DATA at {timestamp}. REQUESTING DATA")
            self.send_response(
                addr, RetryMessage(device_type, current_time.timestamp(), low_battery, token)
            )
            return

        battery_text = ""
        if low_battery:
            battery_text = "WARNING: LOW BATTERY"

        self.log(f"{timestamp} - {battery_text} {device_type}\n{data}")


        if self.connected_devices[device_type]["ignore"]:
            self.connected_devices[device_type]["ignore"] -= 1
            return

        self.send_response(
            addr, AckMessage(device_type, current_time.timestamp(), low_battery, token)
        )

    def quit(self):
        self.stop_listening()

        if self.sock:
            self.sock.close()
            self.sock = None

    def wake_up_device(self, device_type: str, now_checking: set, n: int = 1):
        if n <= 10 and self.is_listening:
            device_info = self.connected_devices[device_type]

            msg = ActivityCheckMessage(device_type, datetime.now().timestamp(), True, device_info["token"])

            self.send_response(device_info["address"], msg)

            time.sleep(1)

            if (datetime.now() - device_info["last_seen"]).total_seconds() > 15:
                self.log(f"WARNING: {device_type} DISCONNECTED")
                time.sleep(4)
                self.wake_up_device(device_type, now_checking, n+1)
            else:
                self.log(f"INFO: {device_type} RECONNECTED")
                now_checking.discard(device_type)

    def activity_check(self):
        now_checking = set()

        while self.is_listening:
            for device_type, device_info in self.connected_devices.items():
                if (((datetime.now() - device_info["last_seen"]).total_seconds() > 15) and
                        not device_type in now_checking):

                    Thread(target= self.wake_up_device, args=(device_type, now_checking), daemon= True).start()
                    now_checking.add(device_type)

            time.sleep(1)

    def stop_ack(self, device_type: str):
        self.connected_devices[device_type]["ignore"] = 3



