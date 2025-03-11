# Testing Boiler
You can test Boiler and manually add test alerts to the feed using [sendTest.py](https://github.com/MissMeridian/boiler/blob/main/sendTest.py). Run it in the working directory of Boiler and with the python3 virtual environment that was created during setup.

`$HOME/boiler/.venv/bin/python3 $HOME/boiler/sendTest.py`

This script will ask you for input on the test alert details. If you leave all options blank it will default to an EAS-DMO for Washington, DC for 30 minutes, with a default test text.
