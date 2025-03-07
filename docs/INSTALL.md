# Installation Instructions (Linux)
1. Install curl, if not already installed. `sudo apt install curl`
2. Download the install script: `curl -O https://raw.githubusercontent.com/MissMeridian/boiler/refs/heads/main/install.sh`
3. Make the script executable: `chmod +x install.sh`
4. Run the installer. `./install.sh`
5. Verify that the services are running:
    - `systemctl status boiler-alerts`
    - `systemctl status boiler-web`
If systemctl does not show a FAILED or DEAD state, you should be able to see a response by visiting the default config's port and path. Replace the hostname with the machine's IP address or localhost if you are running it on your local system.
    - `http://system-ip-or-localhost:8080/IPAWSOPEN_EAS_SERVICE/rest/feed`

That's it for installation!