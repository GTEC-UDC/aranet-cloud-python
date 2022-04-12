#!/usr/bin/env python3

# Create home assistant configuration files for integrating Aranet sensors
# from the Aranet Cloud using the aranet.py script

import aranet_cloud
import argparse
from collections.abc import Collection
import os
import pathlib
import sys

import ha_aranet_conf


def ha_aranet_cloud_main_conf(sensor_names: Collection[str],
                              program: str, file) -> None:
    def printf(s=""):
        print(s, file=file)

    printf("# ARANET SENSOR CONFIGURATION")
    printf("# DO NOT MODIFY THIS FILE")
    printf("# THIS FILE HAS BEEN GENERATED WITH THE SCRIPT {}".
           format(os.path.basename(__file__)))
    printf()
    printf("# Aranet entity")
    printf("# The sensor data is recovered from the command line and set as ")
    printf("# attributes of the \"aranet\" entity")
    printf()
    printf("- platform: command_line")
    printf("  command: \"{}\"".format(program))
    printf("  name: \"aranet\"")
    printf("  scan_interval: 60")
    printf("  command_timeout: 30")
    printf("  # we specify a dummy value template")
    printf("  value_template: \"{{ value_json.num_sensors }}\"")
    printf("  json_attributes:")
    for s in sensor_names:
        for metric in ha_aranet_conf.ARANET_METRICS_DICT.values():
            printf(" "*4 + "- {}_{}".format(s, metric.customName))


def ha_aranet_cloud_templates_conf(sensor_names: Collection[str], file) -> None:
    def printf(s=""):
        print(s, file=file)

    printf("# ARANET TEMPLATES CONFIGURATION")
    printf("# DO NOT MODIFY THIS FILE")
    printf("# THIS FILE HAS BEEN GENERATED WITH THE SCRIPT {}".
           format(os.path.basename(__file__)))
    printf()
    printf("- sensor:")
    metrics_dict = ha_aranet_conf.ARANET_METRICS_DICT | \
        ha_aranet_conf.ARANET_TELEMETRY_DICT
    for s in sensor_names:
        for metric in metrics_dict.values():
            printf("  - name: \"Aranet {} {}\"".
                   format(s.replace(".", ""), metric.customName))
            printf("    unit_of_measurement: \"{}\"".format(metric.unit))
            printf("    value_template: "
                   "\"{{{{ state_attr('sensor.aranet', '{}_{}'}}}}\"".
                   format(s, metric.customName))
            printf()


def ha_aranet_cloud_stats_conf(sensor_names: Collection[str],
                               stats: Collection[str],
                               max_hours: int, sampling_size: int,
                               file) -> str:
    def printf(s=""):
        print(s, file=file)

    printf("# ARANET STATISTICS CONFIGURATION")
    printf("# DO NOT MODIFY THIS FILE")
    printf("# THIS FILE HAS BEEN GENERATED WITH THE SCRIPT {}".
           format(os.path.basename(__file__)))
    printf()
    for s in sensor_names:
        s_id = s.replace(".", "")
        for metric in ha_aranet_conf.ARANET_METRICS_DICT.values():
            for stat in stats:
                printf("- platform: statistics")
                printf("  name: \"Aranet {} {} stats {}\"".
                       format(s_id, metric.customName, stat))
                printf("  entity_id: sensor.aranet_{}_{}".
                       format(s_id, metric.customName.lower()))
                printf("  state_characteristic: \"{}\"".format(stat))
                printf("  sampling_size: {}".format(sampling_size))
                printf("  max_age:")
                printf("    hours: {}".format(max_hours))
                printf()


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

    # Aranet Cloud login cache file
    login_cache_file = data_folder / "aranet_login.json"
    # login_cache_file = None  # disable cache

    # Get sensors information
    aranet_data = aranet_cloud.get_sensors_info(
        aranet_conf, fields=["name"],
        login_cache_file=login_cache_file)

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
