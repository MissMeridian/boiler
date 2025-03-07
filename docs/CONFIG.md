# Configuring Boiler
The default configuration file (boiler.cfg) for boiler should appear as follows:
```js
{
  "poll_url": "https://alerts.globaleas.org/api/v1/alerts/active",
  "alerts_dir": "alerts",
  "archive_dir": "archive",
  "delete_on_expire": true,
  "trim_encoder_prefix": true,
  "web": {
    "flask": {
      "enabled": true,
      "host_address": "0.0.0.0",
      "host_port": 8080
    },
    "root_url": "http://domain.or.ip-address:port",
    "alerts_suffix": "/IPAWSOPEN_EAS_SERVICE/rest/alerts",
    "feed_suffix": "/IPAWSOPEN_EAS_SERVICE/rest/feed",
    "update_suffix": "/IPAWSOPEN_EAS_SERVICE/rest/update"
  },
  "audio": {
    "store_local": true,
    "trim_headers": true
  }
}
```
**You need to make the following changes to this config before Boiler will work for any ENDEC:**
- **Change "root_url" to match the domain name or IP address of the Boiler host, followed by the port number (host_port).**
  - Example 1: If I'm hosting Boiler on my LAN on a server with an IP of 192.168.1.55, I will change root_url to: "http://192.168.1.55:8080"
  - Example 2: If I'm hosting Boiler facing the WAN with a domain name of boiler.eas-hollyanne.com, I will change root_url to: "http://boiler.eas-hollyanne.com:8080"
  - Only use HTTP unless you are using the ![NGINX proxy setup](https://github.com/MissMeridian/boiler/edit/main/docs/NGINX-SETUP.md) with a Cloudflare-proxied record, or a valid SSL cert.

The reason for this change is explained below.
After making the change, restart the Boiler services. 
- `systemctl restart boiler-alerts boiler-web`

If for some reason the JSON formatting is incorrect or a value is not the expected instance, it will be reset to the default value(s).

That concludes the essential initial configuration necessary to get Boiler running properly with HTTP. Check out ![configuring filters](https://github.com/MissMeridian/boiler/blob/main/docs/FILTERS.md) next.

# Explanation of config options
**poll_url**
- This is the URL in which Boiler will expect a JSON response from with the alert details. The JSON keys in the response are specific to the GWES Central Alert Repository, so this link won't need to be changed unless a change is made by GWES or you wish to emulate the CAR feed.

**alerts_dir**
- String value containing the local directory of which the alerts will be stored to and pulled from. Can be an entire directory path like `/var/www/boiler/alerts` or a folder in the working directory of Boiler.

**archive_dir**
- String value containing the local directory of which alerts will be archived to once they expire. Can be an entire directory path or a folder in the working directory of Boiler. To archive alerts, you need to set **delete_on_expire** to `false`.

**delete_on_expire**
- Boolean value (true/false) that decides whether or not alerts will be deleted upon expiration.
- If set to `false`, it will move alerts to the **archive_dir** upon expiration.

**trim_encoder_prefix**
- Boolean value (true/false) that decides whether or not Boiler will attempt to delete the ENDEC prefix string submitted with the alert's translation on the CAR feed.
- If set to `false`, the alert text sent by Boiler will include the alert prefix ("Originator" has issued an "Event" for Blah, Blah...) sent by the original CAR participant.
- If set to `true`, the encoder prefix will be targeted via regex patterns, but if no string is left after the trim, the text will default to "BoilerCAP Message".
  - There are plans to provide a generic alert summary if no string is available in the near future.

## web
**flask**
- **enabled**
  - A boolean true/false value, determines whether or not the Flask service should be running. However, this value is not actually checked since webProcess.py is installed as a systemd service (boiler-web). To actually disable the Flask web service, run `systemctl stop boiler-web` followed by `systemctl disable boiler-web`.
- **host_address**
  - The host's IP address that Flask will listen for communications on. The default value of **0.0.0.0** ensures that it is readily available on all network interfaces.
- **host_port**
  - The network port that the Flask web service is hosted on. If set to 80, you do not need to include the port number in the **root_url**.

**root_url**
- The string value containing the domain name/IP address and network port that the ENDECs will be directed to for communicating and polling the emulated CAP feed.
- This value is used in the XML feed in the <id> tags to build a complete URL that the ENDECs will pull the target file from. If this isn't set correctly, the ENDECs will be unable to locate the XML for the feed and the alerts.
- Needs to include http:// or https:// depending on your configuration.

**alerts_suffix**
- The string value containing the path for the individual alerts which suffixes the **root_url**. This path can be anything, webProcess.py will always route it to the **alerts_dir**. Must begin with forward-slash (/)
- There is no particular requirement for this value, and if set correctly, the Flask server will respond with a request to **root_url/alerts_suffix/<alert_id_will_be_here>.xml**.

**feed_suffix**
- The string value containing the path for the CAP XML feed which indexes the alert entries. Must begin with forward-slash (/).
- It is unknown at this time if the IPAWS-standard format is required for the feed, so for compatibility with all ENDECs, keep it set to `/IPAWSOPEN_EAS_SERVICE/rest/feed`.

**update_suffix**
- The string value containing the path for the CAP XML update response. Must begin with forward-slash (/).
- For compatibility with the SAGE Digital ENDEC, this MUST be set to `/IPAWSOPEN_EAS_SERVICE/rest/update`.
- For compatibility with the Trilithic EASyCAP, this value MUST end with `/update`.

## audio
**store_local**
- Boolean value (true/false) that decides whether or not the EAS information audio is stored locally for each alert.
- ~~If set to `false`, the audio URL delivered on the alert XML will point to the original source on GWES CAR.~~ **NOT CURRENTLY FUNCTIONAL**

**trim_headers**
- Boolean value (true/false) that decides whether or not Boiler will attempt to delete the headers, attention tone, and EOM from the source audio.
- This is very experimental and although it has been mostly consistent, it will error out if it does not find an attention tone, and will resort to TTS audio.

