# Filter configuration
Boiler allows for you to filter out specific alerts from being placed on its feed. You can target by event codes, originators, FIPS codes, station sender IDs, or a combination of your choice.

Filters are laid out in ![filters.cfg](https://github.com/MissMeridian/boiler/blob/main/filters.cfg) as JSON with the following format:
```js
{
    "FILTER NAME": {
        "events": ["ABC","DEF","GHI"],
        "originators": ["JKL","MNO","PQR"],
        "fips": ["000001", "000002"],
        "station_ids": ["FOO/BAR1","JOHN/DOE","DEFAULT"],
        "allow": true
    },
}
```
**General Behavior:**
- Alerts are matched to a filter from top to bottom in ![filters.cfg](https://github.com/MissMeridian/boiler/blob/main/filters.cfg).
  - This means your more broader filters (like simply catching one originator) should be placed near the bottom of the config, because if they are placed above a filter that uses that option with additional target options, it will never be hit. View the example filter explanation below for more details.
- When an alert is matched to a filter, the value of "allow" determines what will happen to that alert.
  - If "allow" is `true`, the alert will be accepted.
  - If "allow" is `false`, the alert will be ignored/blocked.
  - If "allow" is undefined, the alert will be accepted (interpreted as `true` if given no value).

Make sure your comma placement and JSON formatting is correct otherwise your filters will fail.

## Explanation of options
**events**
- Single string or list of string values containing the three-letter EAS event codes. (i.e. "CDW", "TOR", "RWT")

**originators**
- Single string or list of string values containing the three-letter EAS originator codes. (i.e. "EAS", "CIV", "PEP", "WXR")

**fips**
- Single string or list of string values containing the 6-digit FIPS area codes. (i.e. "017001", "005053")

**station_ids**
- Single string or list of string values containing the 8-letter station IDs of the alert sender. (i.e. "KLT/SAGE", "WAHC")

**allow**
- Boolean value (true/false) that determines whether the alert is sent to the feed, or ignored.


## Example filters
```js
{   
    "BLOCK ALL FOR AN AREA": {
        "fips": ["73231", "73251"],
        "allow": false
    },
    "BLOCK TESTS": {
        "events": ["RWT", "RMT", "DMO"],
        "originators": ["EAS", "CIV"],
        "allow": false
    },
    "ALLOW ALL EAS ORIGINATOR": {
        "originators": ["EAS"],
        "allow": false
    },
    "ALLOW ANY ALERTS": {
        "events": null,
        "originators": null,
        "fips": null,
        "station_ids": null,
        "allow": true
    }
}
```
The configuration above has four filters:
- "BLOCK ALL FOR AN AREA"
  - This filter will be matched first.
  - If any alert - regardless of originator, event code, or station ID - is received with a FIPS code of either `73231` or `73251`, it will be BLOCKED and not placed on the feed.
- "BLOCK TESTS"
  - If any alert is received with an originator of either `EAS` or `CIV`, *and* has an event code of `RWT`, `RMT`, or `DMO`, it will be BLOCKED and not place on the feed.
- "ALLOW ALL EAS ORIGINATOR" 
  - If any alert with an originator of `EAS` is received, it will be placed on the feed *if it does not match the "BLOCK TESTS" filter above it first.*
  - For example, if an EAS-RWT is received, it won't be accepted because it will match the "BLOCK TESTS" filter above "ALLOW ALL EAS ORIGINATOR".
- "ALLOW ANY ALERTS"
  - Should be self explanatory. Any alert that does not fall under a filter before it will be accepted onto the feed.
  - This is essentially a "CATCH ALL" filter that will catch anything that does not maybe a filter before it.
