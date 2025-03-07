import json, random
import datetime as dt
import alertProcessor as ap

config = {}

def load_config():
    global config
    with open("boiler.cfg", "r") as config_file:
        config = json.load(config_file)
        config_file.close()

def get_details():
    alert_id = f"test-" + str(random.randint(1000,9999))
    alert_type = None
    alert_org = None
    alert_minutes = None
    alert_audio = None # Not developing this rn because i'm just gonna steal the AP's store_alert function, so any audio that gets passed will need an ATTN and EOMs... in other words, i don't feel like making a bypass
    alert_text = None
    alert_fips = []
    exit_fips_entry_flag = False

    print(f"Creating alert '{alert_id}'")

    while not alert_type:
        i = input("Event Code (DMO): ")
        if not i:
            alert_type = "DMO"
            break
        if len(i) > 3 or len(i) < 3:
            print("Event code must only be 3 characters long.")
        else:
            alert_type = i
    while not alert_org:
        i = input("Originator (EAS): ")
        if not i:
            alert_org = "EAS"
            break
        if len(i) > 3 or len(i) < 3:
            print("Originator must only be 3 characters long.")
        else:
            alert_org = i
    while not alert_minutes:
        i = input("Effective time in minutes (30): ")
        if not i:
            alert_minutes = 30
            break
        try:
            i = int(i)
            alert_minutes = i
        except:
            print(f"The value you gave was not an integer. Please try again.")
    while not exit_fips_entry_flag:
        i = input("FIPS Area (011001): ")
        if not i and len(alert_fips) == 0:
            alert_fips.append("011001")
            exit_fips_entry_flag = True
            break
        elif not i and len(alert_fips) > 0:
            exit_fips_entry_flag = True
            break
        if len(i) < 6 or len(i) > 6:
            print("FIPS code must consist of 6 numerical characters.")
        else:
            alert_fips.append(i)
    while not alert_text:
        i = input("Alert Text: ")
        if not i:
            alert_text = "BoilerCAP Message. This is a test of the Boiler CAP feed emulator. This test is being performed to verify compatibility with all digital Emergency Alert System platforms. If you are hearing this message, the station you are listening to is part of a network equipped with Boiler CAP. No action is required. Message is from: CCTL."
            break
        else:
            alert_text = i

    alert_sent_time = dt.datetime.now(tz=dt.timezone.utc)
    alert_end_time = dt.datetime.now(tz=dt.timezone.utc) + dt.timedelta(minutes=alert_minutes)
    alert_sent_time_iso = alert_sent_time.isoformat(timespec='seconds').replace("+00:00", "")
    alert_end_time_iso = alert_end_time.isoformat(timespec='seconds').replace("+00:00", "")
    alert_sent_time_epoch = alert_sent_time.timestamp()
    alert_end_time_epoch = alert_end_time.timestamp()

    entry = {
        "id": alert_id,
        "hash": alert_id,
        "type": alert_type,
        "originator": alert_org,
        "fipsCodes": alert_fips,
        "startTimeEpoch": alert_sent_time_epoch,
        "startTime": alert_sent_time_iso,
        "endTimeEpoch": alert_end_time_epoch,
        "endTime": alert_end_time_iso,
        "audioUrl": None,
        "translation": alert_text
    }

    print(entry)
    return entry

if __name__ == "__main__":
    load_config()
    details = get_details()
    ap.store_alert(details, config)