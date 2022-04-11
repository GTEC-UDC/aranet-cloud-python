# Module with common functions and data for
# ha_aranet_*_conf.py scripts
import dataclasses


@dataclasses.dataclass
class Metric:
    aranetName: str
    customName: str
    unit: str


ARANET_METRICS_DICT: dict[str, Metric] = {
    "1": Metric("temperature",         "temperature", "°C"),
    "2": Metric("humidity",            "humidity",    "%"),
    "3": Metric("co2",                 "CO2",         "ppm"),
    "4": Metric("atmosphericpressure", "pressure",    "hPa")
}


ARANET_TELEMETRY_DICT: dict[str, Metric] = {
    "61": Metric("battery", "battery", "%"),
    "62": Metric("rssi",    "RSSI",    "dBm")
}


# List of available Home Assistant statistics
HA_STATS = [
    "average_linear",
    "average_step",
    "average_timeless",
    "change_sample",
    "change_second",
    "change",
    "count",
    "datetime_newest",
    "datetime_oldest",
    "distance_95_percent_of_values",
    "distance_99_percent_of_values",
    "distance_absolute",
    "mean",
    "median",
    "noisiness",
    "quantiles",
    "standard_deviation",
    "total",
    "value_max",
    "value_min",
    "variance"
]


def parse_list(arg: str, delim=",") -> list[str]:
    return [] if arg is None else \
           [y for x in arg.split(delim) if len(y := x.strip()) > 0]


def parse_stats_list(arg: str, delim=",") -> list[str]:
    for x in (s := parse_list(arg, delim)):
        if x not in HA_STATS:
            raise ValueError("{} is not a valid statistics".format(x))
    return s


def ask_continue(default: bool = False, msg: str = None) -> bool:
    if msg is None:
        msg = "Continue?"

    msgopt = "[Y/n]" if default else "[y/N]"

    while True:
        print(msg, msgopt, end=" ")
        res = input().lower()
        if len(res) == 0:
            return default
        elif res in ['y', 'yes']:
            return True
        elif res in ['n', 'no']:
            return False
        else:
            print("Please answer y or n")
