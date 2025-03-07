from flask import Flask, Response, send_file
import os, json

# I threw this together super quickly, it's not anything special except that it forwards the requests made to the feed and update suffixes to the specified alerts directory,
# and then forwards requests for the individual .xml files and the individual .mp3 files. Feel free to improve, if you'd like.

app = Flask("Boiler")

config = {}

def load_config():
    global config
    with open("boiler.cfg") as config_file:
        config = json.load(config_file)
        config_file.close()

load_config()

@app.route(config["web"]["feed_suffix"], methods=["GET"])
def get_feed():
    alerts_dir = config.get("alerts_dir")
    xml_path = os.path.join(alerts_dir, "feed.xml")
    try:
        return send_file(xml_path, mimetype="application/xml")
    except FileNotFoundError:
        return Response("<error>File not found</error>", status=404, mimetype="application/xml")

@app.route(config["web"]["update_suffix"], methods=["GET"])
def get_update():
    alerts_dir = config.get("alerts_dir")
    xml_path = os.path.join(alerts_dir, "update.xml")
    try:
        return send_file(xml_path, mimetype="application/xml")
    except FileNotFoundError:
        return Response("<error>File not found</error>", status=404, mimetype="application/xml")

@app.route(f"{config['web']['alerts_suffix']}/<alert_id>/alert.xml", methods=["GET"])
def get_alert(alert_id):
    alerts_dir = config.get("alerts_dir")
    alert_path = os.path.join(alerts_dir, alert_id, "alert.xml")

    if os.path.exists(alert_path):
        return send_file(alert_path, mimetype="application/xml")
    else:
        return Response("<error>Alert not found</error>", status=404, mimetype="application/xml")
    
@app.route(f"{config['web']['alerts_suffix']}/<alert_id>/eas-audio.mp3", methods=["GET"])
def get_alert_audio(alert_id):
    alerts_dir = config.get("alerts_dir")
    alert_path = os.path.join(alerts_dir, alert_id, "eas-audio.mp3")

    if os.path.exists(alert_path):
        return send_file(alert_path, mimetype="audio/mpeg")
    else:
        return Response("<error>Alert not found</error>", status=404, mimetype="application/xml")


if __name__ == "__main__":
    host_address = config["web"]["flask"]["host_address"]
    host_port = config["web"]["flask"]["host_port"]
    app.run(host=host_address, port=host_port, debug=True)