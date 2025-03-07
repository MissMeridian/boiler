# Configuring Boiler
The default configuration file (boiler.cfg) for boiler should appear as follows:
```js
{
  "poll_url": "https://alerts.globaleas.org/api/v1/alerts/active",
  "alerts_dir": "alerts",
  "archive_dir": "archive",
  "web": {
    "flask": {
      "enabled": true,
      "host_address": "0.0.0.0",
      "host_port": 8080
    },
    "root_url": "https://domain.or.ip-address:port",
    "alerts_suffix": "/IPAWSOPEN_EAS_SERVICE/rest/alerts",
    "feed_suffix": "/IPAWSOPEN_EAS_SERVICE/rest/feed",
    "update_suffix": "/IPAWSOPEN_EAS_SERVICE/rest/update"
  },
  "audio": {
    "store_local": true,
    "trim_headers": true
  },
  "delete_on_expire": true,
  "trim_encoder_prefix": true
}
```