import xml.etree.ElementTree as ET
import os, json, logging, coloredlogs, shutil
import datetime as dt

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
coloredlogs.install(level="DEBUG")

def check_expiry(timestamp:str):
    timestamp_dt = dt.datetime.fromisoformat(timestamp).replace(tzinfo=dt.timezone.utc)
    current_dt = dt.datetime.now(tz=dt.timezone.utc)
    if current_dt > timestamp_dt:
        log.debug(f"The current time ({current_dt.isoformat()}) has exceeded the provided timestamp ({timestamp}).")
        expired = True
    else:
        log.debug(f"The current time ({current_dt.isoformat()}) has NOT exceeded the provided timestamp ({timestamp}).")
        expired = False
    return expired

def move_to_archive(alert_dir:str, archive_dir:str):
    if not os.path.exists(archive_dir):
        log.warning(f"Archive directory {archive_dir} doesn't exist! Creating it for you. :)")
        try:
            os.makedirs(archive_dir)
        except PermissionError:
            log.error(f"Permissions error while attempting to create archive directory ({archive_dir})! Does the user have write permissions on the root folder?")
        except:
            log.error(f"Unexpected error occurred while attempting to create alert archive directory ({archive_dir}). See below.", exc_info=True)
    log.debug(f"Moving directory {alert_dir} to {archive_dir}")
    try:
        shutil.move(src=alert_dir, dst=archive_dir)
    except PermissionError:
        log.error(f"Permissions error while moving {alert_dir} to archive at {archive_dir}. Does the user have write permissions to {archive_dir}?")
    except:
        log.error(f"Unexpected error occurred while attempting to move {alert_dir} to archive ({archive_dir}). See below.", exc_info=True)

def update_feed(config:dict):
    '''Updates the feed XML with all of the active alerts in the alerts_dir. This function pretty much re-builds the XML every single time it runs, since it would be easier to do that instead of manually removing alerts from the feed.'''
    alerts_dir = config.get("alerts_dir")
    archive_dir = config.get("archive_dir")
    config_delete_on_expire = config.get("delete_on_expire") # If this is true, the alerts won't be archived.
    config_url_root = config.get("web").get("root_url")
    config_feed_suffix = config.get("web").get("feed_suffix")
    config_alerts_suffix = config.get("web").get("alerts_suffix")
    config_feed_url = config_url_root + config_feed_suffix
    config_alerts_url = config_url_root + config_alerts_suffix

    root = ET.Element("feed", {"xmlns": "http://www.w3.org/2005/Atom"})
    title = ET.SubElement(root, "title")
    title.set("type", "text")
    title.text = "BOILER EAS FEED"
    updated = ET.SubElement(root, "updated")
    utc_right_now = dt.datetime.now(dt.timezone.utc).isoformat(timespec='milliseconds')
    utc_right_now = utc_right_now.replace("+00:00", "Z")
    updated.text = utc_right_now
    feed_id = ET.SubElement(root, "id")
    feed_id.text = config_feed_url

    # Check to see if the alerts directory even exists first
    if not os.path.exists(alerts_dir):
        log.warning(f"Alerts directory does not yet exist! Creating.")
        os.makedirs(alerts_dir)
        log.info(f"Successfully created directory: {alerts_dir}")
    else:
        log.debug(f"OK - {alerts_dir} exists.")

    # Update feed.xml
    for alert_dir in os.listdir(alerts_dir):
        alert_path = os.path.join(alerts_dir, alert_dir)
        if os.path.isdir(alert_path):
            log.debug(alert_path)
            alert_xml_path = os.path.join(alert_path, "alert.xml")
            alert_json_path = os.path.join(alert_path, "response.json")
            if os.path.exists(alert_xml_path) and os.path.exists(alert_json_path):
                with open(alert_json_path, "r") as alert_json_file:
                    alert_json = json.load(alert_json_file)
                    alert_json_file.close()
                expiration_time = alert_json.get("endTime")
                alert_id = alert_json.get("id")
                alert_event = alert_json.get("type")
                alert_url = f"{config_alerts_url}/{alert_id}/alert.xml"
                alert_fips = alert_json.get("fipsCodes")
                alert_fips_1 = alert_fips[0]
                alert_state_fips = alert_fips_1[1:3] # Thanks, SAGE and Trilithic. No, really, this is stupid. Why are you using this to verify alerts? DAS wasn't smoking whatever crack you two were.
                alert_receive_time = alert_json.get("boilerTime", utc_right_now) # receive time so endecs won't pull the same alert constantly, uses UTC now as backup
                expired = check_expiry(expiration_time)
                if expired: # Expire the alert and move it to the archive if archiving is enabled
                    log.info(f"Alert {alert_id} ({alert_json.get('cacheKey')}) has expired!")
                    if config_delete_on_expire:
                        log.info(f"Deleting alert {alert_id}.")
                        os.remove(path=alert_path)
                    else:
                        log.info(f"Archiving alert {alert_id}.")
                        move_to_archive(alert_dir=alert_path, archive_dir=archive_dir)
                else:
                    log.info(f"Writing alert {alert_id} to feed.")
                    entry = ET.SubElement(root, "entry")
                    entry_title = ET.SubElement(entry, "title")
                    entry_title.set("type", "text")
                    entry_title.text = alert_event
                    entry_link = ET.SubElement(entry, "link")
                    entry_link.set("href", alert_url)
                    entry_id = ET.SubElement(entry, "id")
                    entry_id.text = alert_url
                    entry_updated = ET.SubElement(entry, "updated")
                    entry_updated.text = alert_receive_time
                    entry_category = ET.SubElement(entry, "category")
                    entry_category.set("term", alert_event)
                    entry_category.set("label", "event")
                    entry_category_2 = ET.SubElement(entry, "category")
                    entry_category_2.set("term", alert_state_fips)
                    entry_category_2.set("label", "statefips")

    xml_tree = ET.ElementTree(root)
    ET.indent(xml_tree, space="  ", level=0)
    xml_path = os.path.join(alerts_dir, "feed.xml")
    xml_tree.write(xml_path, encoding="utf-8", xml_declaration=True)
    log.debug(ET.tostring(root, encoding='utf-8').decode('utf-8'))

    # Update update.xml
    root = ET.Element("feed", {"xmlns": "http://www.w3.org/2005/Atom"})
    title = ET.SubElement(root, "title")
    title.set("type", "text")
    title.text = "BOILER EAS FEED"
    updated = ET.SubElement(root, "updated")
    utc_right_now = dt.datetime.now(dt.timezone.utc).isoformat(timespec='milliseconds')
    utc_right_now = utc_right_now.replace("+00:00", "Z")
    updated.text = utc_right_now
    feed_id = ET.SubElement(root, "id")
    feed_id.text = config_feed_url
    xml_tree = ET.ElementTree(root)
    ET.indent(xml_tree, space="  ", level=0)
    xml_path = os.path.join(alerts_dir, "update.xml")
    xml_tree.write(xml_path, encoding="utf-8", xml_declaration=True)
    log.debug(ET.tostring(root, encoding='utf-8').decode('utf-8'))



if __name__ == "__main__":
    test_cfg = {
    "poll_url": "https://alerts.globaleas.org/api/v1/alerts/active",
    "alerts_dir": "alerts",
    "archive_dir": "archive",
    "web": {
        "flask": {
        "enabled": True,
        "host_address": "0.0.0.0",
        "host_port": 8080
        },
        "root_url": "http://localhost:8080",
        "alerts_suffix": "/IPAWSOPEN_EAS_SERVICE/rest/alerts",
        "feed_suffix": "/IPAWSOPEN_EAS_SERVICE/rest/feed",
        "update_suffix": "/IPAWSOPEN_EAS_SERVICE/rest/update"
    },
    "audio": {
        "store_local": True,
        "trim_headers": True
    },
    "delete_on_expire": False,
    "trim_encoder_prefix": True
    }
    update_feed(test_cfg)