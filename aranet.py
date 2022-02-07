#!/usr/bin/env python3

# This script queries the Aranet cloud to obtain the sensors data
# Reference: https://www.zabbix.com/la/integrations/aranet

import aranet_cloud
import json
import logging
import os
import pathlib
import sys
from typing import Any, Dict


def aranet_extract_data(aranet_data: Dict[str, Any]) -> Dict[str, Any]:
    sensors_dict = {}

    sensor_data = aranet_data["data"]["items"]
    sensors_dict["num_sensors"] = len(sensor_data)
    for sensor in sensor_data:
        name = sensor["name"]
        sensors_dict[name + "_time"] = sensor["metrics"][0]["t"]
        for metric in sensor["metrics"]:
            metric_name = aranet_cloud.METRICS_DICT[metric["id"]]
            sensors_dict[name + "_" + metric_name] = metric["v"]
        for telemetry in sensor['telemetry']:
            telemetry_name = aranet_cloud.TELEMETRY_DICT[telemetry["id"]]
            sensors_dict[name + "_" + telemetry_name] = telemetry["v"]

    return sensors_dict


def main():
    script_path = pathlib.Path(__file__).parent.absolute()
    data_folder = script_path / ".aranet"

    # create data_folder if it does not exist
    if not os.path.exists(data_folder):
        os.mkdir(data_folder)

    # configure logging
    log_file = data_folder / "aranet.log"
    log_format = '%(asctime)-15s %(levelname)s %(message)s'

    logging.basicConfig(filename=str(log_file),
                        format=log_format,
                        level=logging.WARNING)

    # load Aranet Cloud configuration
    aranet_conf = aranet_cloud.read_aranet_conf(script_path / "aranet_cloud.conf")

    # Aranet Cloud login cache file
    login_cache_file = data_folder / "aranet_login.json"
    # login_cache_file = None  # disable login cache

    aranet_data = aranet_cloud.get_last_sensor_data(aranet_conf, login_cache_file)
    print(aranet_data)
    print(json.dumps(aranet_extract_data(aranet_data)))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(str(e))
        sys.exit(1)
