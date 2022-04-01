#!/usr/bin/env python3

# This script queries the Aranet cloud to obtain information
# about sensors and the gateways (base stations) to which
# each one is paired.

import aranet_cloud
import dataclasses
import logging
import os
import pandas
import pathlib
import sys


@dataclasses.dataclass
class Pairing:
    name: str
    id: str
    pair_date: str
    gw_id: str
    gw_name: str
    gw_serial: str


@dataclasses.dataclass
class OldPairing(Pairing):
    removed_date: str
    pair_sensor_name: str


def main():
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

    aranet_sensors_data = aranet_cloud.get_sensors_info(
        aranet_conf, fields=["name", "devices"],
        login_cache_file=login_cache_file)

    aranet_gws_data = aranet_cloud.get_gateways(
        aranet_conf, login_cache_file=login_cache_file)

    aranet_gws_dict = {x['id']: x for x in aranet_gws_data['devices']}

    pairings_list: list[Pairing] = []
    old_pairings_list: list[OldPairing] = []

    for sensor in aranet_sensors_data['data']['items']:
        for d in sensor['devices']:
            kwargs = {
                'name': sensor['name'],
                'id': sensor['id'],
                'pair_date': d['pair'],
                'gw_id': d['id'],
                'gw_name': aranet_gws_dict[d['id']]['device'],
                'gw_serial': aranet_gws_dict[d['id']]['serial']
            }

            if 'removed' in d:
                old_pairings_list.append(OldPairing(
                    **kwargs,
                    removed_date=d['removed'],
                    pair_sensor_name=d['name'],
                ))
            else:
                pairings_list.append(Pairing(**kwargs))

    # Print data
    print("Found {} paired sensors".format(len(pairings_list)))
    if len(pairings_list) != 0:
        print()
        print(pandas.DataFrame(pairings_list).
              sort_values(by='name', ignore_index=True).to_string())
        print()
        print()

    print("Found {} removed pairings".format(len(old_pairings_list)))
    if len(old_pairings_list) != 0:
        print()
        print(pandas.DataFrame(old_pairings_list).
              sort_values(by='name', ignore_index=True).to_string())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(str(e))
        sys.exit(1)
