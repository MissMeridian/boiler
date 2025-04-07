## BOILER: CAR to CAP Bridge by CABLE CONTRIBUTES TO LIFE
import requests, time, json, logging, os, coloredlogs
import alertProcessor as ap
import feedManagement as fm
import webProcess as wp
import datetime as dt

# Logging setup.
log = logging.getLogger()
startup_time = dt.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
startup_time_actual = dt.datetime.now().strftime("%H:%M:%S %m/%d/%Y")
if not os.path.exists(f"logs"):
    os.mkdir("logs")
if os.path.exists("logs/boiler.log"):
    os.rename("logs/boiler.log", f"logs/boiler-{startup_time}.log")
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
log_formatter = logging.Formatter(log_format)
FileOutputHandler = logging.FileHandler('logs/boiler.log')
FileOutputHandler.setFormatter(log_formatter)
coloredlogs.install(level="INFO")
log.addHandler(FileOutputHandler)
log.info(f"Logging started at {startup_time_actual}.")

config = None

def load_config():
    '''Reloads the config file on startup and at the start of each main loop. Additionally, it will also correct any malformed JSON and reset config objects to default values if objects are missing or incorrect.'''
    global config
    log.info("Reloading configuration file.")
    try:
        with open(f"boiler.cfg", "r") as cfg_file: # Yeah, sorry, this means you need to run this script in its working directory.
            cfg = json.load(cfg_file)
            cfg_file.close()
    except FileNotFoundError:
        log.error(f"'boiler.cfg' not found in working directory! Config will be re-written and set to default values.")
        cfg = {}
    except json.decoder.JSONDecodeError:
        log.error(f"'boiler.cfg' was not properly formatted as JSON! Config will be re-written and reset.")
        cfg = {}
    except: 
        log.error(f"Something unexpected happened while trying to load the config file. You can find out more in the traceback below!", exc_info=True)
    
    # We'll load the current config values as a new config, if they exist, and if not, the values will be set back to the default.
    new_cfg = {
        "poll_url": str(cfg.get("poll_url", "https://alerts.globaleas.org/api/v1/alerts/active")),
        "alerts_dir": str(cfg.get("alerts_dir", "alerts")),
        "archive_dir": str(cfg.get("archive_dir", "archive")),
        "web": {
            "flask": {
                "enabled": bool(cfg.get("web", {}).get("flask", {}).get("enabled", True)),
                "host_address": str(cfg.get("web", {}).get("flask", {}).get("host_address", "127.0.0.1")),
                "host_port": int(cfg.get("web", {}).get("flask", {}).get("host_port", 8080))
            },
            "root_url": str(cfg.get("web", {}).get("root_url", "https://your-domain.or.ip-address:port/boiler")),
            "alerts_suffix": str(cfg.get("web", {}).get("alerts_suffix", "/IPAWSOPEN_EAS_SERVICE/rest/alerts")),
            "feed_suffix": str(cfg.get("web", {}).get("feed_suffix", "/IPAWSOPEN_EAS_SERVICE/rest/feed")),
            "update_suffix": str(cfg.get("web", {}).get("update_suffix", "/IPAWSOPEN_EAS_SERVICE/rest/update"))
        },
        "audio": {
            "store_local": bool(cfg.get("audio", {}).get("store_local", True)),
            "trim_headers": bool(cfg.get("audio", {}).get("trim_headers", True))
        },
        "delete_on_expire": bool(cfg.get("delete_on_expire", True)),
        "trim_encoder_prefix": bool(cfg.get("trim_encoder_prefix", True))
    }
    if new_cfg != cfg: # This condition would only ever be met if a key was reset to the default value.
        difference = new_cfg.keys() - cfg.keys()
        log.warning(f"Some config items were missing or invalid and reset to the default values: {difference}")
        log.info("Overwriting config file 'boiler.cfg'")
        with open(f"boiler.cfg", "w") as cfg_file:
            json.dump(obj=new_cfg, fp=cfg_file, indent=2)
            cfg_file.close()
    if config and new_cfg != config:
        log.info("Config change detected! Updating running config with new values.")
        config = new_cfg
    else:
        log.debug(f"Config has not changed since last run.")
    if not config:
        log.debug(f"Initialized config for first-time run.")
        config = new_cfg
        

def main():
    ## Main Loop
    while True:
        load_config()
        feed_CAR = ap.poll(config.get("poll_url", "https://alerts.globaleas.org/api/v1/alerts/active"))
        for entry in feed_CAR:
            log.debug(f"Alert received from CAR: {entry}")
            log.info(f"Found alert on CAR: {entry.get('type')}")
            timestamp = entry.get("endTime")
            expired = fm.check_expiry(timestamp=timestamp)
            if not expired:
                filter_match = ap.check_filters(entry=entry) 
                if filter_match:
                    if not ap.check_if_stored(entry=entry, config=config):
                        ap.store_alert(entry=entry, config=config)
                    else:
                        log.debug(f"We have already downloaded this alert.")
            else:
                log.info(f"Alert is expired and won't be processed.")
        fm.update_feed(config=config)
        time.sleep(20) # Poll every 20 seconds

if __name__ == "__main__":
    main()
