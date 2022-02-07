#!/usr/bin/env python3

# This script queries the Aranet cloud to obtain the sensors list
# and returns the id and name of each sensor in CSV format
# Reference: https://www.zabbix.com/la/integrations/aranet

import aranet_cloud
import csv
import logging
import os
import pathlib
import sys


def main():
    script_path = pathlib.Path(__file__).parent.absolute()
    data_folder = script_path / ".aranet"

    # create data_folder if it does not exist
    if not os.path.exists(data_folder):
        os.mkdir(data_folder)

    # load Aranet Cloud configuration
    aranet_conf = aranet_cloud.read_aranet_conf(script_path / "aranet_cloud.conf")

    # Aranet Cloud login cache file
    login_cache_file = data_folder / "aranet_login.json"
    # login_cache_file = None  # disable cache

    aranet_data = aranet_cloud.get_last_sensor_data(
        aranet_conf, login_cache_file, fields=['name'])

    # get sensor id and name data
    data = [(d['id'], d['name']) for d in aranet_data['data']['items']]

    # sort data by sensor name
    data = sorted(data, key=lambda x: x[1])

    # write data in CSV format
    csvwriter = csv.writer(sys.stdout)
    csvwriter.writerow(['id', 'name'])  # header
    for item in data:
        csvwriter.writerow(item)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(str(e))
        sys.exit(1)
