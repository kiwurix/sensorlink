import socket
import time
from datetime import datetime
from time import sleep
from helpers import calculate_checksum
from messages import RegistrationMessage, DataMessage, MessageType, Message
from typing import Callable
from tester.info import generate_info
from threading import Thread

timeout_bytes = 0

class RegistrationError(Exception):
    pass

class Device:
    def __init__(self, device_type: str, log: Callable[[str], None], ):
        self.device_type = device_type
        self.low_battery: bool = False
        self.last_data_message: DataMessage = None

        self.log = log
        self.sock: socket.socket = None
        self.server: (str, int) = None
        self.token = None

        self.is_auto_sending: bool = False
        self.auto_sending_thread: Thread = None

        self.is_receiving: bool = False
        self.receiving_thread: Thread = None
        self.awaiting_response: bool = False


    def send(self, message):
        self.sock.sendto(message.to_bytes(), self.server)

    def send_data_message(self):
        self.send(self.last_data_message)
        self.awaiting_response = True


    def generate_data_message(self):
        if not self.token:
            self.register()

        data = generate_info(self.device_type)
        self.last_data_message = DataMessage(self.device_type, datetime.now().timestamp(), self.low_battery, self.token,
                                             data, calculate_checksum(data))


    def receive(self):
        data, _ = self.sock.recvfrom(1024)
        message = Message.from_bytes(data)

        return message


    def _receiving_process(self):
        global timeout_bytes

        while self.is_receiving:
            try:
                response = self.receive()
                message_type = response.message_type

                self.awaiting_response = False

                if message_type == MessageType.TOKEN:
                    self.token = response.device_token

                elif message_type == MessageType.RETRY:
                    self.last_data_message.checksum = calculate_checksum(self.last_data_message.data)
                    self.send_data_message()

                elif message_type == MessageType.INVALID_TOKEN:
                    self.register()
                    self.last_data_message.device_token = self.token
                    self.send_data_message()

                elif message_type == MessageType.ACTIVITY_CHECK:
                    self.generate_data_message()
                    self.send_data_message()


            except (socket.timeout, ConnectionResetError, OSError, RegistrationError) as e:
                if isinstance(e, socket.timeout) and self.awaiting_response:
                    timeout_bytes += len(self.last_data_message.to_bytes())
                    self.log(f"Cumulative size of messages with no response received: {timeout_bytes}")
                    self.send_data_message()


    def register(self):
        old_token = self.token

        reg_msg = RegistrationMessage(self.device_type, datetime.now().timestamp(), self.low_battery)
        self.send(reg_msg)

        now = datetime.now()
        while self.token == old_token:
            sleep(0.01)
            if (datetime.now() - now).total_seconds() > 1:
                raise RegistrationError



    def configure(self, server_ip: str, server_port: int):
        auto_sending = self.is_auto_sending

        self.quit()

        self.server = (server_ip, server_port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(5)

        self.start_receiving()

        if auto_sending:
            self.start_auto_sending()


    def start_auto_sending(self):
        self.is_auto_sending = True
        if not (self.auto_sending_thread and self.auto_sending_thread.is_alive()):
            self.auto_sending_thread = Thread(target=self._auto_sending_process, daemon=True)
            self.auto_sending_thread.start()

    def stop_auto_sending(self):
        self.is_auto_sending = False

    def start_receiving(self):
        self.is_receiving = True
        if not (self.receiving_thread and self.receiving_thread.is_alive()):
            self.receiving_thread = Thread(target=self._receiving_process, daemon=True)
            self.receiving_thread.start()

    def stop_receiving(self):
        self.is_receiving = False

    def _auto_sending_process(self):
        while self.is_auto_sending:
            try:
                self.generate_data_message()
                self.send_data_message()
                time.sleep(10)
            except (OSError, RegistrationError):
                time.sleep(5)


    def quit(self):
        self.stop_receiving()
        self.stop_auto_sending()
        self.token = None

        if self.sock:
            self.sock.close()
            self.sock = None


    def make_checksum_error(self):
        data = generate_info(self.device_type)
        self.last_data_message  = DataMessage(self.device_type, datetime.now().timestamp(), self.low_battery,
                                              self.token, data, calculate_checksum(data) + 3)
        self.send_data_message()


    def activity_mechanism_check(self):
        self.stop_receiving()
        self.stop_auto_sending()
        self.sock.settimeout(16)

        for server_attempt in range(0, 3):
            self.receive()
            if server_attempt == 2:
                self.sock.settimeout(5)
                self.start_auto_sending()
                self.start_receiving()

