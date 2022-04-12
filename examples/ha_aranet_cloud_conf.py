#!/usr/bin/env python3

# Create home assistant configuration files for integrating Aranet sensors
# from the Aranet Cloud using the aranet.py script

import aranet_cloud
import argparse
from collections.abc import Collection
import os
import pathlib
import sys
import yaml

import ha_aranet_conf


def ha_aranet_cloud_main_conf(sensor_names: Collection[str],
                              program: str, file) -> None:
    def printf(s=""):
        print(s, file=file)

    printf("# " + "-"*77)
    printf("# ARANET SENSOR CONFIGURATION")
    printf("# Do NOT modify this file.")
    printf("# This file has been generated with {}".format(os.path.basename(__file__)))
    printf("# https://github.com/tombolano/aranet-cloud-python")
    printf("# " + "-"*77)
    printf()
    printf("# Aranet entity")
    printf("# The sensor data is recovered from the command line and set as ")
    printf("# attributes of the \"aranet\" entity")

    main_conf = {
        "platform": "command_line",
        "command": program,
        "name": "aranet",
        "scan_interval": 60,
        "command_timeout": 30,
        "value_template": "{{ value_json.num_sensors }}",
        "json_attributes": [
            "{}_{}".format(s, m.customName)
            for s in sensor_names
            for m in ha_aranet_conf.ARANET_METRICS_DICT.values()
        ]
    }

    yaml.dump([main_conf], file, sort_keys=False, allow_unicode=True)


def ha_aranet_cloud_templates_conf(sensor_names: Collection[str], file) -> None:
    def printf(s=""):
        print(s, file=file)

    printf("# " + "-"*77)
    printf("# ARANET TEMPLATES CONFIGURATION")
    printf("# Do NOT modify this file.")
    printf("# This file has been generated with {}".format(os.path.basename(__file__)))
    printf("# https://github.com/tombolano/aranet-cloud-python")
    printf("# " + "-"*77)
    printf()

    metrics_dict = ha_aranet_conf.ARANET_METRICS_DICT | \
        ha_aranet_conf.ARANET_TELEMETRY_DICT

    templ_conf = [
        {
            "name": "Aranet {} {}".format(s.replace(".", ""), m.customName),
            "unit_of_measurement": m.unit,
            "value_template": "{{{{ state_attr('sensor.aranet', '{}_{}'}}}}".
                              format(s, m.customName)
        }
        for s in sensor_names for m in metrics_dict.values()
    ]

    yaml.dump([{"sensor": templ_conf}], file,
              sort_keys=False, allow_unicode=True)


def ha_aranet_cloud_stats_conf(sensor_names: Collection[str],
                               stats: Collection[str],
                               max_hours: int, sampling_size: int,
                               file) -> str:
    def printf(s=""):
        print(s, file=file)

    printf("# " + "-"*77)
    printf("# ARANET STATISTICS CONFIGURATION")
    printf("# Do NOT modify this file.")
    printf("# This file has been generated with {}".format(os.path.basename(__file__)))
    printf("# https://github.com/tombolano/aranet-cloud-python")
    printf("# " + "-"*77)
    printf()

    stats_conf = [
        {
            "platform": "statistics",
            "name": "Aranet {} {} stats {}".
                    format((sid := s.replace(".", "")), m.customName, stat),
            "entity_id": "sensor.aranet_{}_{}".
                         format(sid, m.customName.lower()),
            "state_characteristic": stat,
            "sampling_size": sampling_size,
            "max_age": {"hours": max_hours}
        }
        for s in sensor_names
        for m in ha_aranet_conf.ARANET_METRICS_DICT.values()
        for stat in stats
    ]

    yaml.dump(stats_conf, file, sort_keys=False, allow_unicode=True)


def main():
    # Parse command line parameters
    parser = argparse.ArgumentParser(
        description="Create Aranet Cloud configuration files "
                    "for Home Assistant.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-m", "--main",
                        default="ha_aranet_cloud_main.yaml",
                        help="Main sensors configuration file")
    parser.add_argument("-t", "--templ",
                        default="ha_aranet_cloud_templates.yaml",
                        help="Templates configuration file")
    parser.add_argument("-s", "--stats",
                        default=None,
                        help="Statistics configuration file")
    parser.add_argument("--stats-sensors",
                        default="*",
                        help="Comma separated list of sensors to include in the statistics (* for all)")
    parser.add_argument("-p", "--prog",
                        default="python3 aranet_get_latest_data.py",
                        help="Command to execute")
    parser.add_argument("--stats-list",
                        type=ha_aranet_conf.parse_stats_list,
                        default="mean,value_max,value_min,standard_deviation",
                        help="Comma separated list of statistical characteristics")
    parser.add_argument("--stats-max-hours",
                        type=int, default=168,
                        help="Maximum age for calculating statistics")
    parser.add_argument("--stats-sampling-size",
                        type=int, default=10080,
                        help="Maximum number of samples for calculating statistics")
    parser.add_argument("-i", "--ignore",
                        type=ha_aranet_conf.parse_list, default=None,
                        help="Comma separated list of sensors names to ignore")
    args = parser.parse_args()

    # Check if files exist
    for f in [args.main, args.templ, args.stats]:
        if f is not None and os.path.exists(f):
            print("File \"{}\" already exists, it will be overwritten".format(f))
            if not ha_aranet_conf.ask_continue():
                return

    # If args.ignore is None set it to []
    if args.ignore is None:
        args.ignore = []

    script_path = pathlib.Path(__file__).parent.absolute()
    data_folder = script_path / ".aranet"

    # create data_folder if it does not exist
    if not os.path.exists(data_folder):
        os.mkdir(data_folder)

    # load Aranet Cloud configuration
    aranet_conf = aranet_cloud.read_aranet_conf(
        script_path / "aranet_cloud.conf")

    # Get sensors information
    aranet_data = aranet_cloud.get_sensors_info(
        aranet_conf, fields=["name"])

    # get sensor names
    # also filter out sensors indicated in the ignore option
    sensor_names = sorted(set(d["name"] for d in aranet_data["data"]["items"]
                          if d["name"] not in args.ignore))

    # Create main configuration file
    with open(args.main, "w") as f:
        ha_aranet_cloud_main_conf(sensor_names, args.prog, f)

    # Create templates configuration file
    with open(args.templ, "w") as f:
        ha_aranet_cloud_templates_conf(sensor_names, f)

    # Create statistics configuration file
    if args.stats is not None:
        if args.stats_sensors == "*":
            stats_sensors_names = sensor_names
        else:
            stats_sensors_names = set()
            for sn in set(ha_aranet_conf.parse_list(args.stats_sensors)):
                if sn in sensor_names:
                    stats_sensors_names.add(sn)
                else:
                    print("[WARNING] sensor \"{}\" does not exist".format(sn),
                          file=sys.stderr)
            stats_sensors_names = sorted(stats_sensors_names)

        with open(args.stats, "w") as f:
            ha_aranet_cloud_stats_conf(
                stats_sensors_names, args.stats_list,
                args.stats_max_hours, args.stats_sampling_size, f)


if __name__ == "__main__":
    main()
