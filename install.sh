#!/usr/bin/env bash

echo "WARNING: This script will install boiler to a folder in the \$HOME directory. You can re-locate this later, but remember to update the systemd services."
read -p "Proceed? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd "$HOME" || exit 1

    echo "Detecting Linux distribution..."

    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
    else
        echo "Cannot detect Linux distribution. Please install dependencies manually."
        exit 1
    fi

    echo "Detected distro: $DISTRO"

    install_packages() {
        case "$DISTRO" in
            ubuntu|debian)
                sudo apt-get update
                sudo apt-get install -y git ffmpeg python3 python3-venv python3-pip
                ;;
            arch|manjaro)
                sudo pacman -Syu --noconfirm
                sudo pacman -S --noconfirm git ffmpeg python python-virtualenv python-pip
                ;;
            fedora)
                sudo dnf install -y git ffmpeg python3 python3-virtualenv python3-pip
                ;;
            void)
                sudo xbps-install -S
                sudo xbps-install -y git ffmpeg python3 python3-pip python3-virtualenv
                ;;
            gentoo)
                sudo emerge --sync
                sudo emerge dev-vcs/git media-video/ffmpeg dev-lang/python dev-python/pip dev-python/virtualenv
                ;;
            *)
                echo "Unsupported distro: $DISTRO. Please install git, ffmpeg, python3, python3-venv, and python3-pip manually."
                exit 1
                ;;
        esac
    }

    install_packages

    BOILER_DIR=$HOME/boiler
    if [ -d "$BOILER_DIR" ]; then
        echo "Directory $BOILER_DIR already exists. Deleting it..."
        rm -rf "$BOILER_DIR"
    fi

    git clone https://github.com/MissMeridian/boiler.git "$BOILER_DIR"

    VENV_DIR="$BOILER_DIR/.venv"

    if [ ! -d "$VENV_DIR" ]; then
        echo "Creating virtual environment in $VENV_DIR..."
        python3 -m venv "$VENV_DIR"
    else
        echo "Virtual environment already exists....? But how?"
    fi

    source "$VENV_DIR/bin/activate"

    if [ -f "$BOILER_DIR/requirements.txt" ]; then
        echo "Installing dependencies from requirements.txt..."
        pip install --upgrade pip
        pip install -r "$BOILER_DIR/requirements.txt"
    else
        echo "requirements.txt not found, please make sure all the files copied correctly!"
    fi

    deactivate

    # Detect init system
    INIT_SYSTEM="systemd"
    if command -v openrc-init &>/dev/null && [ "$DISTRO" = "gentoo" ]; then
        INIT_SYSTEM="openrc"
    elif [ "$DISTRO" = "void" ] && [ -d /etc/runit ]; then
        INIT_SYSTEM="runit"
    fi

    echo "Using init system: $INIT_SYSTEM"

    case "$INIT_SYSTEM" in
        systemd)
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

            sudo systemctl daemon-reload
            sudo systemctl enable boiler-alerts
            sudo systemctl enable boiler-web
            sudo systemctl start boiler-alerts
            sudo systemctl start boiler-web
            ;;

        openrc)
            echo "Installing OpenRC services..."
            sudo tee /etc/init.d/boiler-alerts > /dev/null <<EOL
#!/sbin/openrc-run

description="Boiler Alerts"
command="$VENV_DIR/bin/python3"
command_args="$BOILER_DIR/boiler.py"
command_background=true
pidfile="/run/boiler-alerts.pid"
EOL

            sudo tee /etc/init.d/boiler-web > /dev/null <<EOL
#!/sbin/openrc-run

description="Boiler Web"
command="$VENV_DIR/bin/python3"
command_args="$BOILER_DIR/webProcess.py"
command_background=true
pidfile="/run/boiler-web.pid"
EOL

            sudo chmod +x /etc/init.d/boiler-*
            sudo rc-update add boiler-alerts default
            sudo rc-update add boiler-web default
            sudo rc-service boiler-alerts start
            sudo rc-service boiler-web start
            ;;

        runit)
            echo "Installing runit services..."
            mkdir -p ~/service/boiler-alerts ~/service/boiler-web

            cat <<EOL > ~/service/boiler-alerts/run
#!/bin/sh
exec $VENV_DIR/bin/python3 $BOILER_DIR/boiler.py
EOL

            cat <<EOL > ~/service/boiler-web/run
#!/bin/sh
exec $VENV_DIR/bin/python3 $BOILER_DIR/webProcess.py
EOL

            chmod +x ~/service/boiler-*/run
            sudo ln -s ~/service/boiler-alerts /etc/sv/
            sudo ln -s ~/service/boiler-web /etc/sv/
            sudo ln -s /etc/sv/boiler-alerts /var/service/
            sudo ln -s /etc/sv/boiler-web /var/service/
            ;;

        *)
            echo "Unsupported init system."
            exit 1
            ;;
    esac

    echo "Setup complete! You should see an XML response on http://localhost:8080/IPAWSOPEN_EAS_SERVICE/rest/update"
    echo "Make sure to edit your config and set the root_url to match your server's domain or IP address! You will need to restart boiler-alerts and boiler-web."
fi
