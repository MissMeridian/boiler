## feedProcessor manages the storage, conversion, and deletion of alerts on the CAP mock feed.
## WRITTEN BY CABLE CONTRIBUTES TO LIFE
import requests, json, logging, os, re
import audioExtractor as ae
import datetime as dt
import xml.etree.ElementTree as ET
log = logging.getLogger(__name__)

def poll(url:str):
    '''Polls for alerts on given URL (alerts.globaleas.org/api/v1/alerts/active) and returns the entire response as dict.
    
    Probably won't work anywhere else but this string is replaceable in the event the API changes in the future.'''
    log.info(f"Polling for active alerts on {url}")

    headers = {
        "User-Agent": "BOILER"
    }

    try:
        r = requests.get(url, timeout=10, headers=headers)
        feed = r.json()
        return feed
    except requests.exceptions.Timeout:
        log.error(f"The API took too long to respond (10+ seconds) or the request timed out.")
    except requests.exceptions.RequestException:
        log.error("A general Exception occured when making the request.", exc_info=True)
    except:
        log.error("An unexpected error occurred when trying to poll the API!", exc_info=True)

def check_filters(entry:dict):
    '''Checks filters.cfg for a matching alert filter. When a filter is matched, it will return True or False depending on the value of "allow" in the filter. If no filter is matched, it will process as True anyway.
    
    Filters are processed from top to bottom, so whatever filter gets matched first will be the one that triggers the filter action. This means your less-specific filters should be located near the bottom of the config.'''
    try:
        with open(f"filters.cfg", "r") as filter_file:
            filters = json.load(filter_file)
            filter_file.close()
            log.debug(f"'filters.cfg' loaded successfully.")
    except FileNotFoundError:
        log.error("'filters.cfg' not found in working directory! Ignoring filters, all alerts will be placed on the feed.")
        process = True
        return process # So that boiler won't continue erroring out
    except json.decoder.JSONDecodeError:
        log.error("'filters.cfg' is not formatted properly and could not be decoded! Filters will be ignored and all alerts will be placed on the feed.")
        process = True
        return process # So that boiler won't continue erroring out
    except:
        log.error(f"An unexpected error occurred while trying to load the filters configuration.", exc_info=True)
        process = True
        return process # So that boiler won't continue erroring out

    for filter_name, rules in filters.items():
        match = True
        log.debug(f"Found filter '{filter_name}'")
        filter_orgs = rules.get("originators", None)
        filter_events = rules.get("events", None)
        filter_fips = rules.get("fips", None)
        filter_stations = rules.get("station_ids", None)
        filter_allow = rules.get("allow", True)
        eas_org = entry.get("originator")
        eas_event = entry.get("type")
        eas_fips = entry.get("fipsCodes")
        eas_station = entry.get("callsign").rstrip() # Remove any left over spaces in the station ID.
        eas_string = f"{eas_org}-{eas_event}-" + ''.join(f"{fips}-" for fips in eas_fips) + f"{eas_station}"

        # tl;dr we go down each filter's values and ignore any set to 'null', and when we match a value that is set, but it doesn't match the alert's values, then we set match to False and ignore.
        if match:
            if filter_orgs != None:
                if isinstance(filter_orgs, str):
                    filter_orgs = list(filter_orgs) # Correct to a list so we can do "if blah in blah"
                if eas_org in filter_orgs:
                    match = True
                    log.debug(f"Matched originator ({eas_org}) in filter '{filter_name}'")
                else:
                    match = False
                    log.debug(f"Did not match an originator in filter '{filter_name}'. Ignoring.")
            else:
                log.debug(f"Filter '{filter_name}' is not targeting any originators.")
        if match:
            if filter_events != None:
                if isinstance(filter_events, str):
                    filter_events = list(filter_events) # Correct to a list so we can do "if blah in blah"
                if eas_event in filter_events:
                    match = True
                    log.debug(f"Matched event type ({eas_event}) in filter '{filter_name}'")
                else:
                    match = False
                    log.debug(f"Did not match an event type in filter '{filter_name}' Ignoring.")
            else:
                log.debug(f"Filter '{filter_name}' is not targeting any event types.")
        if match:
            if filter_fips != None:
                if isinstance(filter_events, str):
                    filter_fips = list(filter_fips) # Correct to a list so we can do "if blah in blah"
                for fips in eas_fips:
                    if eas_event in filter_fips:
                        match = True
                        log.debug(f"Matched FIPS code ({fips}) in filter '{filter_name}'")
                        break
                    else:
                        match = False
                        log.debug(f"Did not match a FIPS code in filter '{filter_name}' Ignoring.")
            else:
                log.debug(f"Filter '{filter_name}' is not targeting any FIPS codes.")
        if match:
            if filter_stations != None:
                if isinstance(filter_stations, str):
                    filter_stations = list(filter_stations) # Correct to a list so we can do "if blah in blah"
                if eas_station in filter_stations:
                    match = True
                    log.debug(f"Matched station ID ({eas_station}) in filter '{filter_name}'")
                else:
                    match = False
                    log.debug(f"Did not match a station ID in filter '{filter_name}' Ignoring.")
            else:
                log.debug(f"Filter '{filter_name}' is not targeting any station IDs.")
        if match:
            log.info(f"Alert '{eas_string}' matched filter '{filter_name}'!")
            break # If we fully matched a filter, we need to break the loop so that it doesn't try to match another filter and then match becomes False.
    if match:
        if filter_allow:
            log.info(f"Filter action for '{filter_name}' is set to ALLOW! '{eas_string}' will be processed.")
            process = True
        else:
            log.info(f"Filter action for '{filter_name}' is set to BLOCK! '{eas_string}' will NOT be processed.")
            process = False
    else:
        log.info(f"Alert '{eas_string}' did not match any filters. It will be processed anyway.")
        process = True
    return process

def trim_string(alert_text:str):
    '''A bunch of regex screwery to try and eliminate as much of the encoder prefix string as possible. Not perfect but if for some reason an exception occurs, a default string will be placed.'''
    try:
        # Good luck!
        pattern = re.compile(
            r'^(.*?\buntil\b.*?)'  # Match everything up to and including "until"
            r'(\b(?:[A-Z][a-z]+ \d{1,2},? \d{1,2}:\d{2} [APM]{2}(?: [A-Z]{3})?|' # DASDEC time
            r'[A-Z][a-z]+ \d{1,2}- \d{1,2}:\d{2} [APM]{2} [A-Z]{3}|' # EASyCAP time
            r'\d{1,2}:\d{2} [APM]{2}|'   # Time
            r'\d{1,2}:\d{2} [APM]{2} [A-Z]{3} \d{1,2}, \d{4})\b)' # More time
            r'(?:.*?\bMESSAGE FROM [A-Z\d/]{1,8}\b\.?)?',  # Allows letters, numbers, and "/" in MESSAGE FROM XXXXXXXX
            re.IGNORECASE | re.DOTALL
        )

        cleaned_text = re.sub(pattern, '', alert_text).strip()
        cleaned_text = re.sub(r'^\.+', '', cleaned_text).strip()

        
        if len(cleaned_text) < 3:
            final_text = "BoilerCAP Message"
        else:
            final_text = cleaned_text

        log.info(f"Alert description trimmed: '{final_text}'")
        return final_text
    except:
        final_text = "BoilerCAP Message"
        log.error(f"Something went horribly wrong while trying to magically remove the encoder's prefix string. Defaulting!", exc_info=True)
        return final_text

def check_if_stored(entry:dict, config:dict):
    '''Checks to see if an alert is already stored and matches the hash inside of the original API response.'''
    alerts_directory = config.get("alerts_dir")
    alert_id = str(entry.get("id"))

    if alert_id:
        alert_directory = os.path.join(alerts_directory, alert_id)
        if os.path.exists(alert_directory):
            alert_json_path = os.path.join(alert_directory, "response.json")
            alert_xml_path = os.path.join(alert_directory, "alert.xml")
            alert_audio_path = os.path.join(alert_directory, "source-audio.mp3")
            if os.path.exists(alert_json_path):
                log.debug(f"{alert_json_path} exists.")
                with open(alert_json_path, "r") as alert_json_file:
                    alert_json = json.load(alert_json_file)
                    alert_json_file.close()
                    entry["boilerTime"] = alert_json.get("boilerTime", None) # After making a change to manage the <updated> tag of each individual alert, this is required to prevent the program from entering a loop of re-downloading every alert because the new value no longer matches the API's raw response.
                    if alert_json != entry:
                        log.warning(f"Alert {alert_id}'s JSON file existed, but did not match the original API response!")
                        return False
                    else:
                        log.debug(f"{alert_json_path} matched integrity of original API response.")
            else:
                log.debug(f"{alert_json_path} does not exist!")
                return False
            if os.path.exists(alert_xml_path):
                log.debug(f"{alert_xml_path} exists.")
            else:
                log.debug(f"{alert_xml_path} does not exist!")
                return False
        else:
            log.debug(f"Directory {alert_directory} does not yet exist for alert {alert_id}!")
            return False
    
    # If it didn't return False, then it exists.
    return True


def store_alert(entry:dict, config:dict):
    '''Stores an individual alert into the specified root directory, and gives the alert its own directory, in which contains the original JSON response from the server, an XML file with the alert formatted to CAP protocol, and associated alert audio, both trimmed and untrimmed (if config allows for local storage).'''
    
    alerts_directory = config.get("alerts_dir")
    entry["boilerTime"] = dt.datetime.now(tz=dt.timezone.utc).isoformat(timespec='milliseconds').replace("+00:00", "Z") # Receive time so we can specify when the alerts were placed onto the feed.
    try: 
        with open("dicts.json", "r") as EASdictsfile:
            eas_dicts = json.load(EASdictsfile)
            EASdictsfile.close()
    except:
        log.error("Couldn't load EAS dictionaries from dicts.json.")
        eas_dicts = {}

    alert_id = str(entry.get("id"))
    alert_hash = str(entry.get("hash"))
    alert_event = str(entry.get("type"))
    alert_event_name = str(eas_dicts.get("EVENTS", {}).get(alert_event, "Unknown Event"))
    alert_severity = str(entry.get("severity")) # For future use
    alert_org = str(entry.get("originator"))
    alert_station = str(entry.get("callsign"))
    alert_fips = list(entry.get("fipsCodes"))
    alert_effective_epoch = int(entry.get("startTimeEpoch"))
    alert_effective_utc = str(entry.get("startTime"))
    alert_expire_epoch = int(entry.get("endTimeEpoch"))
    alert_expire_utc = str(entry.get("endTime"))
    alert_audio_url = entry.get("audioUrl", None) 
    config_audio_store_local = config.get("audio").get("store_local", True)
    config_audio_trim_headers = config.get("audio").get("trim_headers", True)
    config_address = config.get("host_address", "127.0.0.1")
    config_port = config.get("host_port", "9090")
    config_root_url = config["web"]["root_url"]
    config_alerts_suffix = config["web"]["alerts_suffix"]
    config_alerts_url = config_root_url + config_alerts_suffix

    if bool(config.get("trim_encoder_prefix", True)):
        alert_desc = trim_string(str(entry.get("translation", "")))
    else:
        alert_desc = str(entry.get("translation", ""))

    if not os.path.exists(alerts_directory):
        log.warning(f"User-specified alert directory '{alerts_directory}' does not exist! Attempting to create path.")
        try:
            os.makedirs(name=alerts_directory)
        except PermissionError:
            log.error(f"Can not create folder '{alerts_directory}' due to invalid user permissions!")
            raise Exception
    if alert_id:
        alert_directory = os.path.join(alerts_directory, alert_id)
        ## Create directory if nonexistent
        if not os.path.exists(alert_directory):
            log.debug(f"Creating alert directory for {alert_id}. ({alert_directory})")
            os.mkdir(path=alert_directory)
        ## Store original API response
        path_response = os.path.join(alert_directory, "response.json")
        log.debug(f"Writing original API response to JSON. ({path_response})")
        with open(path_response, "w") as file:
            json.dump(obj=entry, fp=file, indent=2)
            file.close()
        
        ## Audio management:
        if alert_audio_url:
            try:
                ## Store audio (if enabled)
                if config_audio_store_local:
                    audio_filename = "source-audio.mp3"
                    path_audio = os.path.join(alert_directory, audio_filename)
                    log.debug(f"Storing audio to local directory. ({path_audio})")
                    ae.download_mp3(url=alert_audio_url,path=path_audio)
                    ## Trim headers (if enabled)
                    if config_audio_trim_headers:
                        ae.trim_headers(alert_directory, path_audio)
                        audio_filename = "eas-audio.mp3"
                        path_audio = os.path.join(alert_directory, audio_filename)
                    local_audio_url = f"{config_alerts_url}/{alert_id}/{audio_filename}"
            except:
                log.warning("Something went wrong when audioExtractor was processing audio for this alert. Audio will not be assigned to this alert. See above for details.", exc_info=True)
                path_audio = None
                local_audio_url = None
        else:
            local_audio_url = None
        
        ## XML storing:
        # Alert Root Section
        xml_alert = ET.Element("alert", {"xmlns": "urn:oasis:names:tc:emergency:cap:1.2"}) # root element
        xml_id = ET.SubElement(xml_alert, "identifier")
        xml_id.text = f"Boiler-{alert_hash}"
        xml_sender = ET.SubElement(xml_alert, "sender")
        xml_sender.text = f"BOILER"
        xml_sent = ET.SubElement(xml_alert, "sent")
        xml_sent.text = alert_effective_utc + "-00:00" # dasdec requires timezone or else it gets upsetti spaghetti
        xml_status = ET.SubElement(xml_alert, "status")
        xml_status.text = "Actual"
        xml_msgtype = ET.SubElement(xml_alert, "msgType")
        xml_msgtype.text = "Alert"
        xml_source = ET.SubElement(xml_alert, "source")
        xml_source.text = f"BOILER-CAP"
        xml_scope = ET.SubElement(xml_alert, "scope")
        xml_scope.text = "Public"
        xml_addresses = ET.SubElement(xml_alert, "addresses")
        xml_addresses.text = "0"
        xml_code = ET.SubElement(xml_alert, "code")
        xml_code.text = "IPAWSv1.0"
        # Info Section
        xml_info = ET.SubElement(xml_alert, "info")
        xml_language = ET.SubElement(xml_info, "language")
        xml_language.text = "en-US" # Uhhh. Well. Let's hope none of the alerts are in Spanish, I guess. Aún es imperfecta!
        xml_category = ET.SubElement(xml_info, "category")
        xml_category.text = "Safety" # Don't know why this matters other than IPAWS filtering.
        xml_event = ET.SubElement(xml_info, "event")
        xml_event.text = alert_event_name # Event code name set here.
        xml_urgency = ET.SubElement(xml_info, "urgency")
        xml_urgency.text = "Immediate" # Do the ENDECs even parse this info?
        xml_severity = ET.SubElement(xml_info, "severity")
        xml_severity.text = "Severe" # Again. Do they even parse this?
        xml_certainty = ET.SubElement(xml_info, "certainty")
        xml_certainty.text = "Observed" # Yeah bro, I saw the Required Monthly Test, it was happening down the street.
        xml_eventCode = ET.SubElement(xml_info, "eventCode")
        xml_eventCode_valueName = ET.SubElement(xml_eventCode, "valueName")
        xml_eventCode_valueName.text = "SAME"
        xml_eventCode_value = ET.SubElement(xml_eventCode, "value")
        xml_eventCode_value.text = alert_event # Event code set here.
        xml_effective = ET.SubElement(xml_info, "effective")
        xml_effective.text = alert_effective_utc + "-00:00" # dasdec requires timezone or else it gets upsetti spaghetti
        xml_expires = ET.SubElement(xml_info, "expires")
        xml_expires.text = alert_expire_utc + "-00:00" # dasdec requires timezone or else it gets upsetti spaghetti
        xml_senderName = ET.SubElement(xml_info, "senderName")
        xml_senderName.text = "BOILER BY CABLE CONTRIBUTES TO LIFE"
        xml_headline = ET.SubElement(xml_info, "headline")
        xml_headline.text = f"{alert_event_name} via Boiler"
        xml_description = ET.SubElement(xml_info, "description")
        xml_description.text = alert_desc # Set alert description text here.
        xml_parameters = [
            ("EAS-ORG", alert_org),
            ("timezone", "UTC"),
            ("BLOCKCHANNEL", "CMAS")
        ]
        for name, value in xml_parameters:
            param = ET.SubElement(xml_info, "parameter")
            param_valueName = ET.SubElement(param, "valueName")
            param_valueName.text = name
            param_valueElement = ET.SubElement(param, "value")
            param_valueElement.text = value
        # Audio Resource Section
        if config_audio_store_local:
            if local_audio_url:
                xml_resource = ET.SubElement(xml_info, "resource")
                xml_resourceDesc = ET.SubElement(xml_resource, "resourceDesc")
                xml_resourceDesc.text = "EAS Broadcast Content"
                xml_mimeType = ET.SubElement(xml_resource, "mimeType")
                xml_mimeType.text = "audio/x-ipaws-audio-mp3" # It'll always be mp3
                xml_uri = ET.SubElement(xml_resource, "uri")
                xml_uri.text = local_audio_url
            else:
                log.warning(f"No audio for this alert.")
        else:
            if alert_audio_url:
                xml_resource = ET.SubElement(xml_info, "resource")
                xml_resourceDesc = ET.SubElement(xml_resource, "resourceDesc")
                xml_resourceDesc.text = "EAS Broadcast Content"
                xml_mimeType = ET.SubElement(xml_resource, "mimeType")
                xml_mimeType.text = "audio/x-ipaws-audio-mp3" # It'll always be mp3
                xml_uri = ET.SubElement(xml_resource, "uri")
                xml_uri.text = alert_audio_url
                log.warning(f"Audio includes original headers and attention tone from GWES CAR.")
            else:
                log.warning(f"No audio for this alert.")
        # Area Section
        xml_area = ET.SubElement(xml_info, "area")
        for fips in alert_fips:
            xml_geocode = ET.SubElement(xml_area, "geocode")
            xml_geocode_valueName = ET.SubElement(xml_geocode, "valueName")
            xml_geocode_valueName.text = "SAME"
            xml_geocode_value = ET.SubElement(xml_geocode, "value")
            xml_geocode_value.text = fips
        # That's it!

        xml_tree = ET.ElementTree(xml_alert)
        ET.indent(xml_tree, space="  ", level=0)
        xml_path = os.path.join(alert_directory, "alert.xml")
        xml_tree.write(xml_path, encoding="utf-8", xml_declaration=True)
        log.debug(ET.tostring(xml_alert, encoding='utf-8').decode('utf-8'))

    else:
        log.error(f"Blasphemy! There was no ID number delivered by the API!")
        raise Exception