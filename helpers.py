from crc import Crc32, Calculator
from messages import *
from tester.info import devices_list, generate_info
import random
from datetime import datetime


def parse_parameters(data: str):
    params = data.split(";")
    parameters_dict = {}

    for p in params:
        try:
            parameter, value = p.split(":")
            parameters_dict[parameter] = value
        except ValueError:
            pass

    return parameters_dict


crc_calculator = Calculator(Crc32.CRC32)
def calculate_checksum(data: str) -> int:
    return crc_calculator.checksum(data.encode())


def message_bytes_number(message: Message) -> int:
    ethernet_header = 14
    ip_header = 20
    udp_header = 8

    msg_bytes = len(message.to_bytes())
    return msg_bytes + udp_header + ip_header + ethernet_header


def generate_all_messages():
    device_type = random.choice(devices_list)
    token = "4444"
    time_now = datetime.now().timestamp()

    info = generate_info(device_type)
    checksum = calculate_checksum(info)

    messages = [
        RegistrationMessage(device_type, time_now, False),
        DataMessage(device_type, time_now, False, token, info, checksum),
        AckMessage(device_type, time_now, False, token),
        InvalidTokenMessage(device_type, time_now, False, token),
        RetryMessage(device_type, time_now, False, token),
        ActivityCheckMessage(device_type, time_now, False, token),
    ]

    return messages



if __name__ == "__main__":
    for msg in generate_all_messages():
        print(f"{msg}\nBytes: {msg.to_bytes()}\nBytes number: {message_bytes_number(msg)}\n")