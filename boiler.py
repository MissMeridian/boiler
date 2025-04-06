## BOILER: CAR to CAP Bridge by CABLE CONTRIBUTES TO LIFE
import os, json, time, logging, datetime as dt
import requests, coloredlogs
import alertProcessor as ap
import feedManagement as fm
import webProcess as wp 

# Setup logging
def setup_logging():
    log = logging.getLogger()
    startup_time = dt.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
    startup_time_actual = dt.datetime.now().strftime("%H:%M:%S %m/%d/%Y")
    
    os.makedirs("logs", exist_ok=True)

    if os.path.exists("logs/boiler.log"):
        os.rename("logs/boiler.log", f"logs/boiler-{startup_time}.log")

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_formatter = logging.Formatter(log_format)
    file_handler = logging.FileHandler("logs/boiler.log")
    file_handler.setFormatter(log_formatter)

    coloredlogs.install(level="INFO")
    log.addHandler(file_handler)
    log.setLevel(logging.INFO)

    log.info(f"Logging started at {startup_time_actual}.")
    return log

log = setup_logging()
config = {}

def load_config():
    """Reloads and validates the configuration."""
    global config
    log.info("Reloading configuration file.")
    
    cfg = {}
    try:
        with open("boiler.cfg", "r") as cfg_file:
            cfg = json.load(cfg_file)
    except FileNotFoundError:
        log.error("'boiler.cfg' not found! Creating with default values.")
    except json.JSONDecodeError:
        log.error("'boiler.cfg' is malformed! Resetting to defaults.")
    except Exception:
        log.exception("Unexpected error while loading 'boiler.cfg'.")

    new_cfg = {
        "poll_url": cfg.get("poll_url", "https://alerts.globaleas.org/api/v1/alerts/active"),
        "alerts_dir": cfg.get("alerts_dir", "alerts"),
        "archive_dir": cfg.get("archive_dir", "archive"),
        "web": {
            "flask": {
                "enabled": cfg.get("web", {}).get("flask", {}).get("enabled", True),
                "host_address": cfg.get("web", {}).get("flask", {}).get("host_address", "127.0.0.1"),
                "host_port": cfg.get("web", {}).get("flask", {}).get("host_port", 8080)
            },
            "root_url": cfg.get("web", {}).get("root_url", "https://your-domain.or.ip-address:port/boiler"),
            "alerts_suffix": cfg.get("web", {}).get("alerts_suffix", "/IPAWSOPEN_EAS_SERVICE/rest/alerts"),
            "feed_suffix": cfg.get("web", {}).get("feed_suffix", "/IPAWSOPEN_EAS_SERVICE/rest/feed"),
            "update_suffix": cfg.get("web", {}).get("update_suffix", "/IPAWSOPEN_EAS_SERVICE/rest/update")
        },
        "audio": {
            "store_local": cfg.get("audio", {}).get("store_local", True),
            "trim_headers": cfg.get("audio", {}).get("trim_headers", True)
        },
        "delete_on_expire": cfg.get("delete_on_expire", True),
        "trim_encoder_prefix": cfg.get("trim_encoder_prefix", True)
    }

    if new_cfg != cfg:
        log.warning("Missing or invalid config keys detected. Rewriting 'boiler.cfg' with defaults.")
        with open("boiler.cfg", "w") as cfg_file:
            json.dump(new_cfg, cfg_file, indent=2)

    if config and new_cfg != config:
        log.info("Configuration updated during runtime.")
    
    config = new_cfg

def main():
    load_config()
    while True:
        feed = ap.poll(config["poll_url"])
        for entry in feed:
            log.debug(f"Alert received: {entry}")
            log.info(f"Processing alert type: {entry.get('type')}")
            
            if not fm.check_expiry(entry.get("endTime")):
                if ap.check_filters(entry):
                    if not ap.check_if_stored(entry, config):
                        ap.store_alert(entry, config)
                    else:
                        log.debug("Alert already stored, skipping.")
                else:
                    log.debug("Alert did not match filter criteria.")
            else:
                log.info("Alert expired, ignoring.")
        
        fm.update_feed(config)
        time.sleep(20)

if __name__ == "__main__":
    main()
