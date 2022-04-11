# aranet-cloud-python

This repository contains the module `aranet_cloud.py`, which allows recovering
data of the [Aranet4 CO₂ sensors](https://aranet4.com/) from the [Aranet
Cloud](https://aranet.cloud).

## Usage

First, import the module

```python
import aranet_cloud
```

For querying the Aranet Cloud, a configuration file with the Aranet Cloud
access credentials is needed, for this the template file
`aranet_cloud.conf.template` is included. Copy the file
`aranet_cloud.conf.template` to a new file `aranet_cloud.conf` and put the
appropriate data in the fields `username`, `password`, and `space_name`. Then
load the file with the following code:

```python
aranet_conf = aranet_cloud.read_aranet_conf("aranet_cloud.conf")
```

To make the data request to the Aranet Cloud, first a login request is needed,
this will return a JSON data containing the access token to be used in the data
requests. The access token can be stored in a cache file to be used for later
requests, for this define a name for the cache file and use it when calling the
request functions.

```python
login_cache_file = "aranet_login.json"
```

The functions that query the Aranet Cloud receive the `aranet_conf` object as
the first parameter, and they accept the keyword parameter `login_cache_file`
to indicate the file of the login cache. See the section below for the
documentation of the available functions.

## Aranet Cloud Query Functions

### `get_sensors_info`

Get information about a sensor. Usage:

```python
get_sensors_info(
    aranet_conf, fields=['metrics', 'telemetry', 'name'],
    **kwargs) -> Dict[str, Any]:
```

where `fields` is a `list` of `str` with the field names of the data to
request. The fields available in the Aranet Cloud are:
- `alarms`: Alarms raised by the sensor.
- `devices`: List of base stations to which the sensor is paired.
- `files`: Number of files stored in the sensor.
- `integrations`: ?
- `metrics`: Latest data captured by the sensor, e.g., CO2, temperature,
  humidity, pressure.
- `name`: Name of the sensor.
- `position`: Localization of the sensor.
- `rules`: Alarm rules for the sensor.
- `skills`: ?
- `tagids`: Tags identifiers for the tags of the sensor.
- `telemetry`: Telemetry data, e.g., battery, RSSI.
- `txint`: ?
- `virtual`: ?


The function will return a dictionary object with the representation of the
JSON data returned by the Aranet Cloud. An example output for two sensors with
names "1.01", and "1.02" is the following:

```python
{'params': {'lastModified': '2022-02-07T11:01:33.391'},
 'data': {'lang': 'en',
  'currentItemCount': 2,
  'items': [{'id': '4196648',
    'metrics': [{'id': '1',
      't': 1644231619,
      'v': 21.2,
      'novelty': {'id': '1', 'name': 'New'}},
     {'id': '2',
      't': 1644231619,
      'v': 46,
      'novelty': {'id': '1', 'name': 'New'}},
     {'id': '3',
      't': 1644231619,
      'v': 1059,
      'novelty': {'id': '1', 'name': 'New'}},
     {'id': '4',
      't': 1644231619,
      'v': 1030,
      'novelty': {'id': '1', 'name': 'New'}}],
    'name': '1.01',
    'telemetry': [{'id': '61',
      't': 1644231619,
      'v': -98,
      'novelty': {'id': '1', 'name': 'New'}},
     {'id': '62',
      't': 1644231619,
      'v': 56,
      'v%': 56,
      'novelty': {'id': '1', 'name': 'New'}}],
    'type': {'id': 'S4V2'}},
   {'id': '4196666',
    'metrics': [{'id': '1',
      't': 1644231655,
      'v': 19.6,
      'novelty': {'id': '1', 'name': 'New'}},
     {'id': '2',
      't': 1644231655,
      'v': 50,
      'novelty': {'id': '1', 'name': 'New'}},
     {'id': '3',
      't': 1644231655,
      'v': 1066,
      'novelty': {'id': '1', 'name': 'New'}},
     {'id': '4',
      't': 1644231655,
      'v': 1030,
      'novelty': {'id': '1', 'name': 'New'}}],
    'name': '1.02',
    'telemetry': [{'id': '61',
      't': 1644231655,
      'v': -93,
      'novelty': {'id': '1', 'name': 'New'}},
     {'id': '62',
      't': 1644231655,
      'v': 50,
      'v%': 50,
      'novelty': {'id': '1', 'name': 'New'}}],
    'type': {'id': 'S4V2'}}]}}
```

For each object in the `metrics` and the `telemetry` arrays, the measured value
will be returned in the `v` field, and the `id` field will indicate the metric
(e.g., CO₂, temperature, etc). The possible values of `id` for the `metrics`
and `telemetry` data can be queried with the `get_metrics` function.


### `get_sensor_data`

Query the recorded data of an Aranet4 sensor during a certain time interval.
Usage:

```python
get_sensor_data(
    aranet_conf, sensor_id, from_time, to_time, timezone="0000",
    metrics=list(DEFAULT_METRICS_DICT.keys()), **kwargs) -> pandas.DataFrame:
```

where
- `sensor_id` is the sensor ID as a `str` or an `int`.
- `from_time` is the earliest time of the sensor data, as a `str` in the ISO
  8601 format, for example `2022-01-31T12:00:00Z`. **Note:** currently it seems
  that the Aranet Cloud only allows times in UTC, specified with the timezone
  `Z` specification or without any timezone information. A different timezone
  specification will make the request fail.
- `to_time` is the latest time of the sensor data, as a `str` with the same
  format as `from_time`.
- `timezone` is the timezone string of the datetime field of the retrieved
  data, with format *hhmm*, being *hh* the hours and *mm* the minutes.
- `metrics` is a list of the metrics identifiers to query. The default is
`list(DEFAULT_METRICS_DICT.keys())`, which is `["1", "2", "3", "4"]`.


For example,

```python
df = aranet_cloud.get_sensor_data(
    aranet_conf, 4196648, '2022-02-01T12:00:00Z', '2022-02-01T12:20:00Z', 
    login_cache_file=login_cache_file)
print(df.to_string())
```

may return the following data

```
          datetime(UTC)  temperature(C)  humidity(%)  co2(ppm)  atmosphericpressure(hPa)
0   2022.02.01 12:00:01            21.0         41.0       743                      1033
1   2022.02.01 12:01:03            21.1         41.0       769                      1033
2   2022.02.01 12:02:01            21.1         41.0       775                      1033
3   2022.02.01 12:03:01            21.1         41.0       772                      1033
4   2022.02.01 12:04:03            21.1         41.0       770                      1033
5   2022.02.01 12:05:03            21.0         41.0       769                      1033
6   2022.02.01 12:06:02            21.1         41.0       760                      1033
7   2022.02.01 12:07:05            21.1         41.0       765                      1033
8   2022.02.01 12:08:06            21.1         41.0       742                      1033
9   2022.02.01 12:09:06            21.0         41.0       741                      1033
10  2022.02.01 12:10:07            21.0         41.0       736                      1033
11  2022.02.01 12:11:07            21.0         41.0       726                      1033
12  2022.02.01 12:12:05            21.0         41.0       710                      1032
13  2022.02.01 12:13:05            21.0         41.0       707                      1032
14  2022.02.01 12:14:06            21.0         41.0       712                      1032
15  2022.02.01 12:15:06            21.0         41.0       697                      1032
16  2022.02.01 12:16:05            21.0         41.0       688                      1032
17  2022.02.01 12:17:05            21.0         41.0       681                      1032
18  2022.02.01 12:18:05            21.0         41.0       675                      1032
19  2022.02.01 12:19:06            21.0         41.0       668                      1032
```


### `get_metrics`

Get available metrics in the Aranet Cloud. Usage:

```python
get_metrics(aranet_conf, **kwargs) -> Dict[str, Any]:
```

The output may be the following:

```python
{'data': {'lang': 'en',
  'currentItemCount': 6,
  'items': [{'id': '1',
    'name': 'Temperature',
    'units': [{'id': '1',
      'name': '°C',
      'precision': 1,
      'selected': True,
      'default': True,
      'overrides': [{'type': 2, 'variant': 10, 'precision': 2}]},
     {'id': '102',
      'name': 'K',
      'precision': 1,
      'overrides': [{'type': 2, 'variant': 10, 'precision': 2}]},
     {'id': '101',
      'name': '°F',
      'precision': 1,
      'overrides': [{'type': 2, 'variant': 10, 'precision': 2}]}]},
   {'id': '2',
    'name': 'Humidity',
    'units': [{'id': '2',
      'name': '%',
      'precision': 1,
      'selected': True,
      'default': True}]},
   {'id': '3',
    'name': 'CO₂',
    'units': [{'id': '3',
      'name': 'ppm',
      'precision': 0,
      'selected': True,
      'default': True}]},
   {'id': '4',
    'name': 'Atmospheric Pressure',
    'units': [{'id': '104',
      'name': 'hPa',
      'precision': 0,
      'selected': True,
      'default': True},
     {'id': '114', 'name': 'inHg', 'precision': 2},
     {'id': '103', 'name': 'mmHg', 'precision': 1},
     {'id': '105', 'name': 'bar', 'precision': 3},
     {'id': '106', 'name': 'psi', 'precision': 2},
     {'id': '117', 'name': 'atm', 'precision': 3},
     {'id': '4', 'name': 'Pa', 'precision': 0}]},
   {'id': '61',
    'name': 'RSSI',
    'units': [{'id': '11',
      'name': 'dBm',
      'precision': 0,
      'selected': True,
      'default': True}]},
   {'id': '62',
    'name': 'Battery voltage',
    'units': [{'id': '132',
      'name': '%',
      'precision': 0,
      'selected': True,
      'default': True},
     {'id': '16', 'name': 'V', 'precision': 2}]}]}}
```


### `get_rules`

Get rules defined in the Aranet Cloud. Usage:

```python
get_rules(aranet_conf, **kwargs) -> Dict[str, Any]:
```

In the Aranet Cloud there is a low battery built-in rule, thus if no other
rules are defines, the output of the function will be similar to the following:

```python
{'data': {'lang': 'en',
  'currentItemCount': 1,
  'items': [{'id': '289',
    'title': 'Low battery',
    'selection': {'type': {'id': 'all', 'name': 'All sensors'}, 'sensors': 57},
    'metric': {'id': '62'},
    'state': {'id': '1', 'name': 'Enabled'},
    'lastAction': '2022-03-03T11:47:53Z',
    'notes': 'This is a built-in rule that controls sensor battery levels. Battery level thresholds depends on the sensor type. This rule cannot be deleted or copied.'}]}}
```


### `get_gateways`

Get gateways (base stations) registered into the Aranet Cloud. Usage:

```python
get_gateways(aranet_conf, **kwargs) -> Dict[str, Any]:
```
For example, with two gateways in the Aranet Cloud the output may be the
following:

```python
{'devices': [{'id': '123',
   'device': 'Aranet-AAAAAA',
   'serial': '111111111111',
   'regdate': '2020-01-01T08:00:00Z',
   'files': 0},
  {'id': '456',
   'device': 'Aranet-BBBBBB',
   'serial': '222222222222',
   'regdate': '2021-01-01T08:00:00Z',
   'files': 0}]}
```

## Examples

This repository includes several exemplary scripts in the `examples` folder.
These are described below.

### `aranet_get_latest_data.py`

Queries the Aranet Cloud for the most recent data of the Aranet4 sensors and
returns them in a JSON format. The script may be called in the following
way:

```bash
$ PYTHONPATH="." python3 aranet.py | jq
```

then, considering two sensors with names "1.01", and "1.02", the output of the
command may be the following:

```json
{
    "num_sensors": 2,
    "1.01_time": 1644228737,
    "1.01_temperature": 21.3,
    "1.01_humidity": 45,
    "1.01_CO2": 1289,
    "1.01_pressure": 1030,
    "1.01_RSSI": -96,
    "1.01_battery": 56,
    "1.02_time": 1644228711,
    "1.02_temperature": 19.2,
    "1.02_humidity": 50,
    "1.02_CO2": 1136,
    "1.02_pressure": 1030,
    "1.02_RSSI": -89,
    "1.02_battery": 50
}
```

### `aranet_get_sensor_list.py`

Queries the Aranet Cloud and returns the list of sensor IDs and names in CSV
format. The script may be called in the following way:

```bash
$ PYTHONPATH="." python3 aranet_get_sensor_list.py
```

and the output may be the following:

```csv
id,name
4196648,1.01
4196666,1.02
```


### `aranet_get_gw_pairing.py`

Queries the Aranet Cloud and returns a list with the data of each sensor and
the gateway to which each one is paired. Moreover, old pairings are also shown.
The script may be called in the following way:

```bash
$ PYTHONPATH="." python3 aranet_get_gw_pairing.py
```

then, considering two sensors with names "1.01", and "1.02" and two base
stations, the output of the command may be the following:

```
Found 2 paired sensors

    name       id             pair_date gw_id           gw_name     gw_serial
0   1.01  4196648  2020-01-01T10:00:00Z   123     Aranet-AAAAAA  111111111111
1   1.02  4196666  2021-01-01T10:00:00Z   456     Aranet-BBBBBB  222222222222


Found 0 removed pairings
```


### `ha_aranet_cloud_conf.py`

Creates [Home Assistant](https://www.home-assistant.io/) configuration files to integrate the Aranet
sensors by querying the Aranet Cloud.

This script by default creates the following files:
- `ha_aranet_cloud_main.yaml`: Main configuration file. Creates an `aranet` sensor entity which stores all the sensor data as attributes
- `ha_aranet_cloud_templates.yaml`: Templates configuration file. Creates a sensor entity for each Aranet sensor retrieving the corresponding attribute from the `aranet` entity.
- `ha_aranet_cloud_stats.yaml`: Statistics configuration. Creates statistics sensors.


### `ha_aranet_mqtt_conf.py`

Creates [Home Assistant](https://www.home-assistant.io/) configuration files to integrate the Aranet
sensors from the MQTT messages sent by the Aranet base stations.

This script by default creates the following files:
- `ha_aranet_mqtt_main.yaml`: Main configuration file.
- `ha_aranet_mqtt_stats.yaml`: Statistics configuration.



## License

This code is available as open source under the terms of the [MIT License](https://opensource.org/licenses/MIT).
