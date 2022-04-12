#!/usr/bin/env python3

# Create home assistant configuration files for integrating Aranet sensors
# from MQTT messages sent by Aranet4 base stations.

import aranet_cloud
import argparse
from collections.abc import Collection
import dataclasses
import os
import pandas
import pathlib
import sys

import ha_aranet_conf


# Class for data of sensor and corresponding base station
@dataclasses.dataclass(eq=True, frozen=True)
class SensorPairing:
    sensor_name: str
    sensor_id: str
    pair_date: str
    gw_id: str
    gw_name: str
    gw_serial: str


def ha_aranet_mqtt_main_conf(sensorPairings: Collection[SensorPairing],
                             file) -> None:
    def printf(s=""):
        print(s, file=file)

    printf("# " + "-"*77)
    printf("# ARANET SENSORS CONFIGURATION")
    printf("# Do NOT modify this file.")
    printf("# This file has been generated with {}".format(os.path.basename(__file__)))
    printf("# https://github.com/tombolano/aranet-cloud-python")
    printf("# " + "-"*77)
    printf()
    metrics_dict = ha_aranet_conf.ARANET_METRICS_DICT | \
        ha_aranet_conf.ARANET_TELEMETRY_DICT
    for s in sensorPairings:
        for metric in metrics_dict.values():
            printf("- platform: mqtt")
            printf("  name: \"Aranet {} {}\"".format(
                   s.sensor_name.replace(".", ""), metric.customName))
            printf("  unit_of_measurement: \"{}\"".format(metric.unit))
            printf("  state_topic: \"Aranet/{}/sensors/{:X}/json/measurements\"".
                   format(s.gw_serial, int(s.sensor_id)))
            printf("  value_template: \"{{{{ value_json.{} }}}}\"".format(
                   metric.aranetName))
            printf()


def ha_aranet_mqtt_stats_conf(sensorPairings: Collection[SensorPairing],
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
    for s in sensorPairings:
        s_id = s.sensor_name.replace(".", "")
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
        description="Create Aranet MQTT configuration files "
                    "for Home Assistant.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-m", "--main",
                        default="ha_aranet_mqtt_main.yaml",
                        help="Main sensors configuration file")
    parser.add_argument("-s", "--stats",
                        default=None,
                        help="Statistics configuration file")
    parser.add_argument("--stats-sensors",
                        default="*",
                        help="Comma separated list of sensors to include in the statistics (* for all)")
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
    for f in [args.main, args.stats]:
        if f is not None and os.path.exists(f):
            print("File \"{}\" already exists, it will be overwritten".format(f))
            if not ha_aranet_conf.ask_continue():
                return

    # If args.ignore is None set it to []
    if args.ignore is None:
        args.ignore = []

    # Set paths
    script_path = pathlib.Path(__file__).parent.absolute()
    data_folder = script_path / ".aranet"

    # create data_folder if it does not exist
    if not os.path.exists(data_folder):
        os.mkdir(data_folder)

    # load Aranet Cloud configuration
    aranet_conf = aranet_cloud.read_aranet_conf(
        script_path / "aranet_cloud.conf")

    # Get sensors information
    aranet_sensors_data = aranet_cloud.get_sensors_info(
        aranet_conf, fields=["name", "devices"])

    # Get base stations information
    aranet_gws_data = aranet_cloud.get_gateways(aranet_conf)

    # Create dict of base station id to base station data
    aranet_gws_dict = {x["id"]: x for x in aranet_gws_data["devices"]}

    # Get list of paired sensors and base stations
    # Filter out sensors indicated in the ignore option
    sensorPairings = [
        SensorPairing(
            sensor_name=sensor["name"],
            sensor_id=sensor["id"],
            pair_date=d["pair"],
            gw_id=d["id"],
            gw_name=aranet_gws_dict[d["id"]]["device"],
            gw_serial=aranet_gws_dict[d["id"]]["serial"]
        )
        for sensor in aranet_sensors_data["data"]["items"]
        if sensor["name"] not in args.ignore
        for d in sensor["devices"]
        if "removed" not in d
    ]

    # Sort sensors by names
    sensorPairings = sorted(sensorPairings, key=lambda x: x.sensor_name)

    # Check that no sensor appears more than once,
    # i.e., they are only paired with one base station,
    # e.g., if a sensor is paired to two base stations it will appear twice
    # For this we use the Pandas library
    df = pandas.DataFrame(sensorPairings)
    df_dup_mask = df["sensor_name"].duplicated()
    if df_dup_mask.any():
        df_dup_names = df.loc[df_dup_mask.array, "sensor_name"]
        print("Error: the following sensors appear to be paired to more "
              "than one base station", file=sys.stderr)
        print(file=sys.stderr)
        for s in df_dup_names:
            df_s = df[df["sensor_name"] == s]
            print("Sensor {} appears {} times:".format(s, len(df_s)),
                  file=sys.stderr)
            print(file=sys.stderr)
            print(df_s.to_string(), file=sys.stderr)
            print(file=sys.stderr)
        sys.exit(1)

    # Create main configuration file
    with open(args.main, "w") as f:
        ha_aranet_mqtt_main_conf(sensorPairings, f)

    # Create statistics configuration file
    if args.stats is not None:
        if args.stats_sensors == "*":
            stats_sensors_pairings = sensorPairings
        else:
            sensor_names_dict = {x.sensor_name: x for x in sensorPairings}
            stats_sensors_names = set()
            for sn in set(ha_aranet_conf.parse_list(args.stats_sensors)):
                if sn in sensor_names_dict:
                    stats_sensors_names.add(sn)
                else:
                    print("[WARNING] sensor \"{}\" does not exist".format(sn),
                          file=sys.stderr)
            stats_sensors_pairings = \
                [sensor_names_dict[x] for x in sorted(stats_sensors_names)]

        with open(args.stats, "w") as f:
            ha_aranet_mqtt_stats_conf(
                stats_sensors_pairings, args.stats_list,
                args.stats_max_hours, args.stats_sampling_size, f)


if __name__ == "__main__":
    main()
