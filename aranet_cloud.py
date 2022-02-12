# Module for querying Aranet sensor data from the Aranet Cloud
# Currently only tested with Aranet CO2 sensors
# Reference: https://www.zabbix.com/la/integrations/aranet


import configparser
import json
import logging
import os
import pandas
import ssl
import time
from typing import Any, Dict, Optional
import urllib.error
import urllib.request


# Expiration time of the login cache in seconds
LOGIN_CACHE_EXPIRATION = 595


# Mappings of id to string for the Aranet sensor and telemetry data
# these can be obtained quering the 'metrics/<space id>' Aranet Cloud API URL
METRICS_DICT = {"1": "temperature",
                "2": "humidity",
                "3": "CO2",
                "4": "pressure"}

TELEMETRY_DICT = {"61": "RSSI",
                  "62": "battery"}


# Logger object
logger = logging.getLogger(__name__)


# SSL context
ssl_context = ssl.SSLContext()


class NotAuthorizedError(Exception):
    """Exception raised when a not authorized (HTTP 401) response is received."""

    def __init__(self, message):
        super().__init__(message)


class CacheExpired(Exception):
    """Exception raised if the cache has expired."""

    def __init__(self, message):
        super().__init__(message)


def get_login_data(cache_file) -> Dict[str, Any]:
    """Get the Aranet Cloud login data from the cache file.

    Args:
        cache_file (str or os.PathLike): A path-like object giving the pathname
            of the cache file.

    Raises:
        CacheExpired: If the cache is older than LOGIN_CACHE_EXPIRATION.

    Returns:
        Dict[str, Any]: A Dict with the contents of the login data stored in
        the cache.
    """
    with open(cache_file) as f:
        if LOGIN_CACHE_EXPIRATION is not None and LOGIN_CACHE_EXPIRATION > 0:
            cache_stat = os.stat(f.fileno())
            cache_time = time.time() - cache_stat.st_mtime
            if cache_time >= LOGIN_CACHE_EXPIRATION:
                raise CacheExpired("Login cache expired")
        return json.loads(f.read())


def save_login_data(cache_file, login_data: str) -> None:
    """Save the Aranet Cloud login data to the cache file.

    Args:
        cache_file (str or os.PathLike): A path-like object giving the pathname
            of the cache file.
        login_data (str): The login data as returned by the Aranet Cloud.
    """
    with open(cache_file, 'w') as f:
        f.write(login_data)
        logger.info("Saved login data to cache file")


def save_login_data_no_raise(cache_file: Optional,
                             login_data: str) -> None:
    """Save the Aranet Cloud login data to the cache file (Exception safe).

    Args:
        cache_file (str, os.PathLike, or None): A path-like object giving the
            pathname of the cache file, or None. If None the function does
            nothing.
        login_data (str): The login data as returned by the Aranet Cloud.
    """
    if cache_file is None:
        return
    try:
        save_login_data(cache_file, login_data)
    except Exception as e:
        logger.error("Error saving the loging data to cache: " + str(e))


def login(aranet_conf, cache_file: Optional = None) -> Dict[str, Any]:
    """Login into the Aranet Cloud and obtain the login data.

    If cache_file is not None, this function saves the login data to the cache.

    Args:
        aranet_conf: Object of the Aranet Cloud config.
        cache_file (str, os.PathLike, or None): A path-like object giving the
            pathname of the cache file. Defaults to None.

    Raises:
        NotAuthorizedError: If the login request results in a not authorized
            (HTTP 401) response.

    Returns:
        Dict[str, Any]: A Dict with the contents of the login data returned by
            the Aranet Cloud.
    """
    logger.info("Making login request to Aranet cloud")
    endpoint = aranet_conf['DEFAULT'].get('endoint', "https://aranet.cloud/api")

    req = urllib.request.Request(
        url=endpoint + "/user/login",
        method="POST", headers={"Content-Type": "application/json"},
        data=json.dumps({"login": aranet_conf['DEFAULT']['username'],
                         "passw": aranet_conf['DEFAULT']['password']}).encode())
    try:
        with urllib.request.urlopen(req, context=ssl_context) as f:
            data = f.read().decode()
    except urllib.error.HTTPError as e:
        raise NotAuthorizedError(str(e.reason)) if e.code == 401 \
              else Exception("Cannot login into Aranet cloud: " +
                             str(e.reason))
    login_data = json.loads(data)
    if cache_file is not None:
        save_login_data_no_raise(cache_file, data)
    return login_data


def get_cloud_space_id(aranet_conf, login_data: Dict[str, Any]) -> str:
    """Get the Aranet Cloud space ID from the login data.

    The aranet_conf config object should contain the parameter space_name
    with the name of the space. Then, this method searches in login_data
    for this space name and returns the corresponding space ID.

    Args:
        aranet_conf: Object of the Aranet Cloud config.
        login_data (Dict[str, Any]): The login data.

    Raises:
        Exception: If the space name indicated in aranet_conf is not found.

    Returns:
        str: The Aranet Cloud space ID corresponding to the space name
            indicated in aranet_conf.
    """
    space_name = aranet_conf['DEFAULT']['space_name']
    spaces = login_data['spaces']
    if len(spaces) == 0:
        raise Exception("Aranet cloud space list is empty")
    elif len(spaces) == 1:
        spaces_item = spaces.items()
        id = list(spaces_item)[0][0]
        name = list(spaces_item)[0][1]
        if name != space_name:
            logger.warn("Aranet cloud space expected name was " + "\"" +
                        space_name + "\", but name is " + name)
        return id
    else:
        id_list = [(x, y) for (x, y) in spaces.items() if y == space_name]
        if len(id_list) == 0:
            raise Exception("Aranet cloud space list does not have the " +
                            "\"" + space_name + "\" space")
        elif len(id_list) > 1:
            raise Exception("Aranet cloud space list has more than one " +
                            "space with name \"" + space_name + "\"")
        else:
            return id_list[0][0]


def get_last_sensor_data2(
        aranet_conf, login_data: Dict[str, Any],
        fields=['metrics', 'telemetry', 'name']) -> Dict[str, Any]:
    """Get the last data for all sensors from the Aranet Cloud.

    Args:
        aranet_conf: Object of the Aranet Cloud config.
        login_data (Dict[str, Any]): The login data.
        fields (list, optional): Fields of the data to request. Defaults to
            ['metrics', 'telemetry', 'name'].

    Raises:
        NotAuthorizedError: If the request results in a not authorized
            (HTTP 401) response.

    Returns:
        Dict[str, Any]: A Dict with the contents of the response.
    """
    logger.info("Making request for sensor data to Aranet cloud")

    cloud_space_id = get_cloud_space_id(aranet_conf, login_data)
    auth_token = login_data['auth']
    endpoint = aranet_conf['DEFAULT'].get('endoint', "https://aranet.cloud/api")

    req = urllib.request.Request(
        url=endpoint + "/sensors/" + cloud_space_id + "?fields=" + ','.join(fields),
        method="GET",
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + auth_token})
    try:
        with urllib.request.urlopen(req, context=ssl_context) as f:
            data = f.read().decode()
    except urllib.error.HTTPError as e:
        raise NotAuthorizedError(str(e.reason)) if e.code == 401 \
              else Exception("Error obtaining the sensor data: " + str(e.reason))
    return json.loads(data)


def get_sensor_data2(
        aranet_conf, login_data: Dict[str, Any],
        sensor_id, from_time, to_time, timezone="0000",
        metrics=list(METRICS_DICT.keys())) -> pandas.DataFrame:
    """Get the data for a given sensor from the Aranet Cloud.

    Args:
        aranet_conf: Object of the Aranet Cloud config.
        login_data (Dict[str, Any]): The login data.
        sensor_id (str or int): The ID of the sensor.
        from_time (str): The earliest time of the data in the ISO 8601 format.
        to_time (str): The latest time of the data in the ISO 8601 format.
        timezone (str, optional): The timezone in format hhmm, where hh are the
            hours, and mm the minutes. Defaults to "0000".
        metrics (list[str], optional): List of metrics IDs to recover. Defaults
            to list(METRICS_DICT.keys()).

    Raises:
        NotAuthorizedError: If the request results in a not authorized
            (HTTP 401) response.

    Returns:
        pandas.DataFrame: A pandas dataframe with the sensor data.
    """
    logger.info("Making request for sensor " + str(sensor_id) + " " +
                "data to Aranet cloud")

    cloud_space_id = get_cloud_space_id(aranet_conf, login_data)
    auth_token = login_data['auth']
    endpoint = aranet_conf['DEFAULT'].get('endoint', "https://aranet.cloud/api")

    aranet_query_url = \
        endpoint + "/sensors/" + cloud_space_id + \
        "/sensor/" + str(sensor_id) + "/export?" + \
        "metric=" + ",".join(metrics) + \
        "&from=" + from_time + \
        "&to=" + to_time + \
        "&timezone=" + timezone

    req = urllib.request.Request(
        url=aranet_query_url, method="GET",
        headers={"Authorization": "Bearer " + auth_token})

    try:
        with urllib.request.urlopen(req, context=ssl_context) as f:
            # return data in pandas dataframe
            df = pandas.read_csv(f, sep=";", header=1)
            logger.info("Downloaded " + str(len(df)) + " data records for " +
                        "sensor " + str(sensor_id) + " from Aranet cloud")
            return df
    except urllib.error.HTTPError as e:
        raise NotAuthorizedError(str(e.reason)) if e.code == 401 \
              else Exception("Error obtaining the sensor data: " + str(e.reason))


def __get_data(aranet_conf, func, func_args, func_kwargs,
               login_cache_file=None):
    """Call a get*data function and handles the needed login calls.

    The function `func` must receive the aranet_conf and the login data as the
    two first positional parameters.

    Args:
        aranet_conf: Object of the Aranet Cloud config.
        func (function): Function to call.
        func_args (list): Positional arguments to the function.
        func_kwargs (Dict): Named arguments to the function.
        login_cache_file (str, os.PathLike, or None): A path-like object giving
            the pathname of the login cache file. Defaults to None.

    Raises:
        NotAuthorizedError: If the request results in a not authorized
            (HTTP 401) response.

    Returns:
        [Any]: The returned value is the one returned by `func`.
    """
    try:
        login_data = get_login_data(login_cache_file)
        cached = True
    except Exception as e:
        logger.info(str(e))
        login_data = login(aranet_conf, login_cache_file)
        cached = False

    try:
        data = func(aranet_conf, login_data, *func_args, **func_kwargs)
    except NotAuthorizedError as e:
        logger.error(str(e))
        if cached:
            # maybe the login data expired, try login in again
            login_data = login(aranet_conf, login_cache_file)
            data = func(aranet_conf, login_data, *func_args, **func_kwargs)
        else:
            raise e

    return data


def get_last_sensor_data(
        aranet_conf, login_cache_file=None,
        fields=['metrics', 'telemetry', 'name']
        ) -> Dict[str, Any]:
    """Get the last data for all sensors from the Aranet Cloud.

    This function performs the needed function calls to recover the loging
    data from the cache file or by calling the Aranet Cloud, and then it
    calls the function get_last_sensor_data2 with the loging data.

    Args:
        aranet_conf: Object of the Aranet Cloud config.
        login_cache_file (str, os.PathLike, or None): A path-like object giving
            the pathname of the login cache file. Defaults to None.
        fields (list[str], optional): Fields of the data to request. Defaults
            to ['metrics', 'telemetry', 'name'].

    Returns:
        Dict[str, Any]: A Dict with the contents of the response.
    """
    return __get_data(aranet_conf, get_last_sensor_data2,
                      [], {'fields': fields}, login_cache_file)


def get_sensor_data(
        aranet_conf, sensor_id, from_time, to_time, timezone="0000",
        metrics=list(METRICS_DICT.keys()), login_cache_file=None
        ) -> pandas.DataFrame:
    """Get the data for a given sensor from the Aranet Cloud.

    This function performs the needed function calls to recover the loging
    data from the cache file or by calling the Aranet Cloud, and then it
    calls the function get_sensor_data2 with the loging data.

    Args:
        aranet_conf: Object of the Aranet Cloud config.
        sensor_id (str or int): The ID of the sensor.
        from_time (str): The earliest time of the data in the ISO 8601 format.
        to_time (str): The latest time of the data in the ISO 8601 format.
        timezone (str, optional): The timezone in format hhmm, where hh are the
            hours, and mm the minutes. Defaults to "0000".
        metrics (list[str], optional): List of metrics IDs to recover. Defaults
            to list(METRICS_DICT.keys()).

    Raises:
        NotAuthorizedError: If the request results in a not authorized
            (HTTP 401) response.

    Returns:
        pandas.DataFrame: A pandas dataframe with the sensor data.
    """
    return __get_data(aranet_conf, get_sensor_data2, [],
                      {'sensor_id': sensor_id, 'from_time': from_time,
                       'to_time': to_time, 'metrics': metrics,
                       'timezone': timezone},
                      login_cache_file)


def read_aranet_conf(file):
    """Reads the Aranet Cloud configuration file

    Args:
        file (str or os.PathLike): A path-like object giving the pathname of
            the configuration file.

    Returns:
        [configparser.ConfigParser]: A ConfigParser object with the
            configuration.
    """
    aranet_conf = configparser.ConfigParser()
    with open(file) as f:
        aranet_conf.read_file(f)
    return aranet_conf
