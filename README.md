# aranet-cloud-python

This repository contains the module `aranet_cloud.py`, which allows recovering data of the [Aranet4](https://aranet4.com/) sensors from the [Aranet Cloud](https://aranet.cloud).

## Usage

First, import the module

```python
import aranet_cloud
```

For querying the Aranet Cloud, a configuration file with the Aranet Cloud access credentials is needed, for this just copy the file `aranet_cloud.conf.template` to a new file `aranet_cloud.conf` and put the appropriate data in the fields `username`, `password`, and `space_name`. Then load the file with the following code

```python
aranet_conf = aranet_cloud.read_aranet_conf("aranet_cloud.conf")
```

To make the data request to the Aranet cloud, first a login request is needed, this will return a JSON data containing the access token to be used in the data requests. The access token can be stored in a cache file to be used for later requests, for this define a name for the cache file and use it when calling the request functions.

```python
login_cache_file = "aranet_login.json"
```

### Query the last sensor data
The last recorded data of the Aranet4 sensors may be queried with the function

```python
get_last_sensor_data(
    aranet_conf, login_cache_file=None,
    fields=['metrics', 'telemetry', 'name']) -> Dict[str, Any]:
```

where 
- `aranet_conf` is the object containing the Aranet Cloud configuration.
- `login_cache_file` is the file to use for storing the Aranet Cloud login data, or `None` for not saving the data.
- `fields` is a list containing the fields to recover. The possible values are:
  - `metrics`: the CO2, temperature, humidity, and pressure data
  - `telemetry`: the battery and RSSI data of the sensor
  - `name`: the name of the sensor

This function will query the Aranet Cloud, and will return a dictionary object with the representation of the JSON data returned by the Aranet Cloud. For example, if we have two sensors with names "1.01", and "1.02", the return value may be the following:

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

For each object in the `metrics` and the `telemetry` arrays, the measured value will be returned in the `v` field, and the `id` field will indicate what is the measure (e.g., CO2, temperature, etc). The possible values of `id` for the `metrics` and `telemetry` data are provided in the module variables `METRICS_DICT` and `TELEMETRY_DICT`, defined as

```python
METRICS_DICT = {"1": "temperature",
                "2": "humidity",
                "3": "CO2",
                "4": "pressure"}

TELEMETRY_DICT = {"61": "RSSI",
                  "62": "battery"}
```

### Query the data of a sensor

The recorded data of an Aranet4 sensor during a certain time interval may be queried with the function

```python
get_sensor_data(
    aranet_conf, sensor_id, from_time, to_time, timezone="0000",
    metrics=list(METRICS_DICT.keys()), login_cache_file=None
    ) -> pandas.DataFrame:
```

where
- `aranet_conf` is the object containing the Aranet Cloud configuration.
- `sensor_id` is the sensor id as a `str` or an `int`.
- `from_time` is the earliest time of the sensor data, as a `str` in the ISO 8601 format, for example `2022-01-31T12:00:00Z`.
- `to_time` is the latest time of the sensor data, as a `str` in the ISO 8601 format.
- `timezone` is the timezone in *hhmm* format of the retrieved data, being *hh* the hours and *mm* the minutes.
- `metrics` is a list of the metrics identifiers to query.
- `login_cache_file` is the file to use for storing the Aranet Cloud 

This function will query the Aranet Cloud, and will return a pandas DataFrame object with the data of the sensor returned by the Aranet Cloud. For example, considering code

```python
df = aranet_cloud.get_sensor_data(
    aranet_conf, 4196648,
    '2022-02-01T12:00:00Z', '2022-02-01T12:20:00Z', 
    login_cache_file=login_cache_file)
print(df.to_string())
```

the output may be

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

## Example files
This repository includes two exemplary scripts, `aranet.py` and `aranet_get_sensor_list.py`.

The `aranet.py` script queries the Aranet Cloud for the last data of the Aranet4 sensors and it returns the data in a JSON format. For example if we have two sensors with names "1.01", and "1.02", the output of executing the shell command

```bash
python3 aranet.py | jq
```

may be the following

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

The `aranet_get_sensor_list.py` script queries the Aranet cloud and returns the list of sensor ids and names in CSV format. For example, executing the following shell command

```bash
python3 aranet_get_sensor_list.py
```

may return the following result

```csv
id,name
4196648,1.01
4196666,1.02
```

## License

This code is available as open source under the terms of the [MIT License](https://opensource.org/licenses/MIT).
