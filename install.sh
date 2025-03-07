#!/bin/bash
echo "WARNING: This script will install boiler to a folder in the $HOME directory. You can re-locate this later, but remember to update the systemd services."
read -p "Proceed? (y/n) " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]
then
    cd $HOME # get us where we need to be 

    echo "Updating package repositories"
    sudo apt-get update

    echo "Checking for git."
    if ! command -v git &> /dev/null
    then
        echo "git not found, installing."
        sudo apt install -y git
    else
        echo "git is installed."
    echo "Checking for ffmpeg."
    if ! command -v ffmpeg &> /dev/null
    then
        echo "ffmpeg not found, installing."
        sudo apt install -y ffmpeg
    else
        echo "ffmpeg is installed."

    echo "Checking for python3, python3-venv, and python3-pip."
    if ! command -v python3 &> /dev/null
    then
        echo "Python 3 is not installed, installing."
        sudo apt install -y python3 python3-venv python3-pip
    else
        if ! command -v python3-venv &> /dev/null
        then
            echo "Python 3 is installed but python3-venv is missing. Installing."
            sudo apt install -y python3-venv
        else
            echo "python3-venv is installed."
        if ! command -v python3-pip &> /dev/null
        then
            echo "python3-pip is not installed, installing."
            sudo apt install -y python3-pip
        else
            echo "python3-pip is installed."

    BOILER_DIR=$HOME/boiler
    if [ -d "$BOILER_DIR" ]; then
        echo "Directory $BOILER_DIR already exists. Deleting it..."
        rm -rf "$BOILER_DIR" # oh god, PLEASE be careful
    fi

    git clone https://github.com/MissMeridian/boiler.git "$BOILER_DIR"

    VENV_DIR="$BOILER_DIR/.venv"

    if [ ! -d "$VENV_DIR" ]; then
        echo "Creating virtual environment in $VENV_DIR..."
        python3 -m venv $VENV_DIR
    else
        echo "Virtual environment already exists....? But how?"
    fi

    source $VENV_DIR/bin/activate

    if [ -f "$BOILER_DIR/requirements.txt" ]; then
        echo "Installing dependencies from requirements.txt..."
        pip install --upgrade pip
        pip install -r requirements.txt
    else
        echo "requirements.txt not found, please make sure all the files copied correctly!"
    fi

    deactivate

    echo "Installing boiler-alerts and boiler-web systemd services..."
    cat <<EOL | sudo tee /etc/systemd/system/boiler-alerts.service
[Unit]
Description=Boiler - Alerts & Feed Management
After=network.target

[Service]
ExecStart=$VENV_DIR/bin/python3 $BOILER_DIR/boiler.py
WorkingDirectory=$BOILER_DIR
Restart=always
RestartSec=30
User=${USER}

[Install]
WantedBy=multi-user.target
EOL

    echo "Created boiler-alerts.service"

    cat <<EOL | sudo tee /etc/systemd/system/boiler-web.service
[Unit]
Description=Boiler - Flask Web Service
After=network.target

[Service]
ExecStart=$VENV_DIR/bin/python3 $BOILER_DIR/webProcess.py
WorkingDirectory=$BOILER_DIR
Restart=always
RestartSec=30
User=${USER}

[Install]
WantedBy=multi-user.target
EOL

    echo "Created boiler-web.service"

    echo "Restarting systemctl daemon..."
    sudo systemctl daemon-reload

    echo "Enabling services..."
    sudo systemctl enable boiler-alerts.service
    sudo systemctl enable boiler-web.service

    echo "Setup complete! You should see an XML response on http://localhost:8080/IPAWSOPEN_EAS_SERVICE/rest/update"
    echo "Make sure to edit your config and set the root_url to match your server's domain or IP address! You will need to restart boiler-alerts and boiler-web."
fi