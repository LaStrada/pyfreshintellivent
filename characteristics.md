# Fresh Intellivent Sky Bluetooth Characteristics

A list of known characteristics for this fan.

## Connection flow

To be able to read and write to the device, you need to [authenticate](#Authenticate) before reading/writing to other characteristics.

## Characteristics

| Name                | Format | Read/Write |
|---------------------|--------|------------|
| Device name (alias) | String | R/W        |
| Sensor data         |        | R          |
| Authenticate        | BBBB   | R/W        |
| Humidity            | BBH    | R/W        |
| Light/Odour         | BBBB   | R/W        |
| Constant speed      | BH     | R/W        |
| Timer               | BBBH   | R/W        |
| Airing              | BBBH   | R/W        |
| Pause               | BB     | R/W        |
| Boost               | BHH    | R/W        |
| Temporary RPM       | BH     | W          |

### Device name (alias)
```
b85fa07a-9382-4838-871c-81d045dcc2ff
```
**Format:** String


### Sensor data
```
528b80e8-c47a-4c0a-bdf1-916a7748f412
```
**Format:** Unknown (work in progress)


### Authenticate
```
4cad343a-209a-40b7-b911-4d9b3df569b2
```
**Format:** 4 bytes
#### How to use
1. Press power button on fan
2. Press and hold WiFi button on fan 8 seconds
3. The fan is now in "Pairing" mode
4. Connect to the fan and read this Characteristic
5. This value can now be used next time to authenticate by writing this value (4 bytes)


### Humidity
```
7c4adc01-2f33-11e7-93ae-92361f002671
```
**Format:** BBH\
**B:** Off/on (`00`/`01`)\
**B:** Humidity detection (low: `00`, medium: `01`, high: `02`)\
**H:** RPM

#### Example
On, low humidity detection, 2071 RPM:\
`00001708`


### Light/Odour
```
7c4adc02-2f33-11e7-93ae-92361f002671
```
**Format:** BBBB\
**B:** Light sensor off/on (`00`/`01`)\
**B:** Light sensor detection (low: `00`, medium: `01`, high: `02`)\
**B:** Odour sensor off/on (`00`/`01`)\
**B:** Odour sensor detection (no: `00`, high: `01`, medium: `02`, low: `03`)

#### Examples
Light and odour sensors off, no detections:\
`00000000`\
\
Light detection on, high light detection, odour detection on, high odour detection:\
`01020101`


### Constant speed
```
7c4adc03-2f33-11e7-93ae-92361f002671
```
**Format:** BH\
**B:** Off/on (`00`/`01`)\
**H:** RPM


### Timer
```
7c4adc04-2f33-11e7-93ae-92361f002671
```
**Format:** BBBH\
**B:** Running time in minutes\
**B:** Delay active (disabled: `00`, enabled: `01`)\
**B:** Delay start minutes\
**H:** RPM


### Airing
```
7c4adc05-2f33-11e7-93ae-92361f002671
```
**Format:** BBBH\
**B:** Off/on (off: `00`, on: `01`)\
**B:** ?\
**B:** Minutes\
**H:** RPM


### Pause
```
7c4adc06-2f33-11e7-93ae-92361f002671
```
**Format:** BB\
**B:** Off/on (off: `00`, on: `01`)\
**B:** Minutes


### Boost
```
7c4adc07-2f33-11e7-93ae-92361f002671
```
**Format:** BHH\
**B:** Off/on (off: `00`, on: `01`)\
**H:** RPM
**H:** Seconds


### Temporary RPM
```
7c4adc08-2f33-11e7-93ae-92361f002671
```
**Format:** BH\
**B:** Off/on (off: `00`, on: `01`)\
**H:** RPM

Will keep the speed you send in as long as you are connected. This will override all other modes.
