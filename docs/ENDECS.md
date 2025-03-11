# EAS ENDEC CAP client configuration
**This guide will provide the settings for known working EAS ENDECs.**

## Digital Alert Systems DASDEC-II & One-Net SE
To set up a Boiler CAP client on the Digital Alert System, follow these steps:
1. In the DAS web interface, go to Setup > Net Alerts.
2. Go to the CAP Decode tab.
3. Under "Remote CAP server setup", click "Add CAP Client Interface".
4. A new CAP interface will be created. Depending on your Boiler setup, choose either HTTP Get or Secure HTTPS Get. (If you don't know, or haven't configured the NGINX proxy, use HTTP Get.)
5. Match the settings below, replacing `host-ip-or-domain:8080` with your Boiler host's address and port, and the configured feed path (`IPAWSOPEN_EAS_SERVICE/rest/feed` in this example).

![DASDEC](https://github.com/MissMeridian/boiler/blob/main/docs/cap-dasdec.png)

**Additional Notes:**
- During testing, the DASDEC seemed to not like the /update target, either due to improper format or signature. Although this has likely been fixed, it's easier just to use /feed since it has a direct link to every active alert.

## Trilithic / Viavi EASyCAP
To set up a Boiler CAP client on the EASyCAP, follow these steps:
1. In the EASyCAP web inteface, go to CAP Sources > IPAWS Atom Feed
2. Click the Add button to the right of the "Atom Feed" entry box.
3. In the URL box, place the URL path (with http:// or https://) to Boiler's **root_url** and **update_suffix**, including everything except for "/update" at the end.
    - This is because the EASyCAP will append `/update` automatically to the end of this URL to parse CAP.
4. Check "Use CAP Proxy" and "Use Alert Text if available". In other words, match the settings below.

![EASYCAP](https://github.com/MissMeridian/boiler/blob/main/docs/cap-easycap.PNG)

**Additional Notes:**
- The EASyCAP will always append `/update` to the end of the URL you gave. So, make sure that your "update_suffix" in ![boiler.cfg](https://github.com/MissMeridian/boiler/blob/main/boiler.cfg) ends with `/update`.
- Required the "statefips" category tag label to be appended on each alert entry in /feed.

## SAGE Digital ENDEC 3644
To set up a Boiler CAP client on the SAGE, follow these steps:
1. In ENDECSetD, go to the CAP tab.
2. Click "Add new server" and name it whatever you want.
3. Set the Server Type to `IPAWS OPEN`.
4. Set the Server Base URL to the IP/domain and port of the Boiler host, *EXCLUDING* http:// or https:// in the URL.
5. Check the boxes for "Enable Polling", "Enforce CAP 1.2", and "No SSL check".
6. Uncheck the box for "Verify Signature".
7. Verify that your settings are similarly matched below, and then click "Save this CAP server". Export your configuration and restore it to your SAGE Digital.

![SAGE](https://github.com/MissMeridian/boiler/blob/main/docs/cap-sage.png)

**Additional Notes:**
- The SAGE Digital was the pickiest ENDEC to get Boiler to work with. That's because...
- It was very picky about HTTP and non-SSL hosts, even with "No SSL check" selected. If you are debugging the SAGE being unable to receive from Boiler, check the journalctl for boiler-web for connection details.
- The SAGE will ALWAYS append the URL with `/IPAWSOPEN_EAS_SERVICE/rest/update`, so your **update_suffix** needs to match that, otherwise it will not work for the SAGE.
- Required "statefips" category tag label on every alert entry in /feed.

## Gorman-Redlich CAPDEC-1
**Untested.** You could be the first to test it! Report your findings in ![Issues](https://github.com/MissMeridian/boiler/issues), or fork the repo and update this file with details on configuring the CAPDEC-1 for Boiler.

## TFT EAS 911+
**Not supported.** The TFT EAS 911+ cannot be supported because verification of IPAWS signatures is forcefully enabled with no way to disable it without modification to the code, which we do not have at this time. If a hack becomes available, an update to Boiler to verify its support will be made later on.

## TFT 3320/2008
**No.**
