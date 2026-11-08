from abc import ABC
from dataclasses import dataclass, field
from enum import Enum
from tester.info import devices_list, devices, correct_value_representation




class MessageType(Enum):
    REGISTRATION = 1
    TOKEN = 2
    DATA = 3
    INVALID_TOKEN = 4
    ACK = 5
    RETRY = 6
    ACTIVITY_CHECK = 7


def int_to_bits(value: int, length: int):
    necessary_bit_length = value.bit_length()

    if necessary_bit_length > length:
        raise ValueError(
            f"Not enough bits allocated for value {value}. Allocated: {length}, necessary: {necessary_bit_length}.")

    bits = format(value, f"0{length}b")
    return bits


@dataclass
class Message(ABC):
    message_type: MessageType
    device_type: str
    timestamp: float
    low_battery: bool
    device_token: str

    def __post_init__(self):
        self.timestamp = int(self.timestamp)

    def to_bits(self):
        message_type = self.message_type.value
        message_type_bits = int_to_bits(message_type, 3)

        device_type_int = devices_list.index(self.device_type)
        device_type_bits = int_to_bits(device_type_int, 2)

        timestamp_bits = int_to_bits(self.timestamp, 32)

        low_battery_bit = "1" if self.low_battery else "0"

        if self.device_token:
            device_token_bits = int_to_bits(int(self.device_token), 14)
        else:
            device_token_bits = "0" * 14

        base_bits = message_type_bits + device_type_bits + timestamp_bits + low_battery_bit + device_token_bits

        return base_bits


    @classmethod
    def from_bits (cls, bits: str):
        message_type = MessageType(int(bits[0:3], 2))

        device_type_int = int(bits[3:5], 2)
        device_type = devices_list[device_type_int]

        timestamp = int(bits[5:37], 2)

        low_battery = True if bits[37] == "1" else False

        device_token = int(bits[38:52], 2)

        base = (device_type, timestamp, low_battery, device_token)
        match message_type:
            case MessageType.REGISTRATION:
                 return RegistrationMessage(device_type, timestamp, low_battery)
            case MessageType.TOKEN:
                return TokenMessage(*base)
            case MessageType.DATA:
                offset = 52
                data = ""

                for param, info in devices[device_type].items():
                    decimal_places = info["decimal_places"]
                    scale = 10 ** decimal_places

                    bit_length = (int(info["max"] * scale)).bit_length() + 1

                    value_bits = bits[offset + 1: offset + bit_length]
                    value = int(value_bits, 2)

                    value = correct_value_representation(value, decimal_places)

                    sign = "-" if bits[offset] == "1" else ""
                    data += f"{param}:{sign}{value};"

                    offset += bit_length

                checksum = int(bits[offset: offset + 32], 2)

                return DataMessage(*base, data, checksum)

            case MessageType.INVALID_TOKEN:
                return InvalidTokenMessage(*base)
            case MessageType.ACK:
                return AckMessage(*base)
            case MessageType.RETRY:
                return RetryMessage(*base)
            case MessageType.ACTIVITY_CHECK:
                return ActivityCheckMessage(*base)
            case _:
                raise ValueError()


    def to_bytes(self):
        bits = self.to_bits()

        bytes_length = (len(bits) + 7) // 8
        estimated_bit_length = bytes_length * 8

        diff = estimated_bit_length - len(bits)
        for _ in range(diff):
            bits += "0"

        return int(bits, 2).to_bytes(bytes_length)


    @classmethod
    def from_bytes(cls, b: bytes):
        integer = int.from_bytes(b)
        total_bits = len(b) * 8

        bits = int_to_bits(integer, total_bits)
        return cls.from_bits(bits)



@dataclass
class RegistrationMessage(Message):
    message_type: MessageType = field(default=MessageType.REGISTRATION, init=False)
    device_token: str = field(default=None, init=False)


@dataclass
class TokenMessage(Message):
    message_type: MessageType = field(default=MessageType.TOKEN, init=False)

@dataclass
class DataMessage(Message):
    message_type: MessageType = field(default=MessageType.DATA, init=False)
    data: str
    checksum: int

    def to_bits(self) -> str:
        base_bits = super().to_bits()
        device_type = self.device_type

        for param, value in [data.split(":") for data in self.data.split(";")][:-1]:
            param_info = devices[device_type][param]

            decimal_places = param_info["decimal_places"]
            scale = 10 ** decimal_places
            bit_length = (int(param_info["max"]) * scale).bit_length()

            sign_bit = "1" if value.startswith("-") else "0"
            if sign_bit == "1":
                value = value[1:]

            if decimal_places == 0:
                value = int(value)
            else:
                integer_part, fractional_part = value.split(".")
                value = int(integer_part) * scale + int(fractional_part)

            base_bits += sign_bit
            base_bits += int_to_bits(value, bit_length)

        base_bits += int_to_bits(self.checksum, 32)
        return base_bits



@dataclass
class AckMessage(Message):
    message_type: MessageType = field(default=MessageType.ACK, init=False)

@dataclass
class InvalidTokenMessage(Message):
    message_type: MessageType = field(default=MessageType.INVALID_TOKEN, init=False)

@dataclass
class RetryMessage(Message):
    message_type: MessageType = field(default=MessageType.RETRY, init=False)

@dataclass
class ActivityCheckMessage(Message):
    message_type: MessageType = field(default=MessageType.ACTIVITY_CHECK, init=False)






