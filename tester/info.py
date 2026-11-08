import random


devices = {
    "ThermoNode": {
        "temperature": {"min": -50.0, "max": 60.0, "unit": "°C", "decimal_places": 1},
        "humidity": {"min": 0.0, "max": 100.0, "unit": "%", "decimal_places": 1},
        "dew_point": {"min": -50.0, "max": 60.0, "unit": "°C", "decimal_places": 1},
        "pressure": {"min": 800.0, "max": 1100.0, "unit": "hPa", "decimal_places": 2},
    },
    "WindSense": {
        "wind_speed": {"min": 0.0, "max": 50.0, "unit": "m/s", "decimal_places": 1},
        "wind_gust": {"min": 0.0, "max": 70.0, "unit": "m/s", "decimal_places": 1},
        "wind_direction": {"min": 0, "max": 359, "unit": "°", "decimal_places": 0},
        "turbulence": {"min": 0.0, "max": 1.0, "unit": "index", "decimal_places": 1},
    },
    "RainDetect": {
        "rainfall": {"min": 0.0, "max": 500.0, "unit": "mm", "decimal_places": 1},
        "soil_moisture": {"min": 0.0, "max": 100.0, "unit": "%", "decimal_places": 1},
        "flood_risk": {"min": 0, "max": 3, "unit": "level", "decimal_places": 0},
        "rain_duration": {"min": 0, "max": 60, "unit": "min", "decimal_places": 0},
    },
    "AirQualityBox": {
        "co2": {"min": 300, "max": 5000, "unit": "ppm", "decimal_places": 0},
        "ozone": {"min": 0.0, "max": 500.0, "unit": "µg/m³", "decimal_places": 1},
        "air_quality_index": {"min": 0, "max": 500, "unit": "AQI", "decimal_places": 0},
    }
}

devices_list = list(devices.keys())

def generate_info(device_type):
    text = ""

    for param, desc in devices[device_type].items():
        min_value, max_value = int(desc["min"]), int(desc["max"])
        decimal_places = desc["decimal_places"]
        scale = 10 ** decimal_places

        value = random.randint(min_value * scale, max_value * scale)

        text += f"{param}:{correct_value_representation(value, decimal_places)};"

    return  text


def correct_value_representation(value: int, decimal_places: int) -> str:
    scale = 10 ** decimal_places
    sign = "-" if value < 0 else ""
    value = abs(value)

    if decimal_places == 0:
        return f"{sign}{value}"

    integer_part = value // scale
    fractional_part = value % scale

    return f"{sign}{integer_part}.{fractional_part:0{decimal_places}d}"