![Boiler](https://github.com/MissMeridian/boiler/blob/main/docs/boiler.png)
# What is Boiler?
Boiler is an IPAWS feed emulator that converts alerts from GWES's ["Central Alert Repository" (CAR)](https://alerts.globaleas.org/) into Common Alert Protocol (CAP) alerts for digital reception on all IoT EAS platforms. 

To elaborate, participants are uploading their received Emergency Alert System messages to a public, custom-made internet repository using a protocol called EAS_NET. This repository website shows active alerts with their audio and text using its own API. **Boiler** takes advantage of this public API to download the alert information and convert it into **Common Alert Protocol** format, allowing for these local over-the-air and digital alerts to be processed as an IPAWS feed, eliminating the need to monitor an IP audio stream to receive these daisy-chained alert messages.

The conversion of these alerts is somewhat experimental because EAS_NET uploads the full alert audio, which includes the original FSK headers and attention tones. In order to prevent duplicate FSK headers and attention tones, Boiler runs the provided MP3 files through its own ![audioExtractor](https://github.com/MissMeridian/boiler/blob/main/audioExtractor.py) to locate the end point of the attention tone and cut the audio to that point, as well as subtracting the End Of Message FSK. In testing, it has been mostly consistent, but is not perfect and certainly not immune to error. That said, please read the disclaimers below before installing Boiler.

# Disclaimers
- ***DO NOT USE THIS IN A PRODUCTION EMERGENCY ALERT SYSTEM ENVIRONMENT!*** This software is intended for __HOBBYIST USE ONLY__.
- I am not responsible for over-the-air the transmission of illegitimate alerts induced by a Boiler feed.
- I am not responsible for any individual who infiltrates or configures a production EAS receiver for Boiler CAP. ("Production" meaning equipped on a live, FCC-certified broadcast station)
- I am not responsible for any damage done to any device hosting or receiving Boiler CAP as a result of misuse or unexpected error.
- I am not responsible for any harm to persons or organizations caused by intentional misuse or abuse of the software.

Great. Now that we're on the same page, let's begin!

# Quick Start
1. [Installing Boiler](https://github.com/MissMeridian/boiler/blob/main/docs/INSTALL.md)
2. [Configuring Boiler](https://github.com/MissMeridian/boiler/blob/main/docs/CONFIG.md)
3. [Setting up filters](https://github.com/MissMeridian/boiler/blob/main/docs/FILTERS.md)
4. [Adding Boiler to your Emergency Alert System receiver](https://github.com/MissMeridian/boiler/blob/main/docs/ENDECS.md)
5. [Testing the feed](https://github.com/MissMeridian/boiler/blob/main/docs/TESTING.md)

# Support and Feedback
If you experience issues or errors with Boiler, please report them in [issues](https://github.com/MissMeridian/boiler/issues). I will do my best to make fixes where necessary.

Are there features or improvements you'd like to see in Boiler? Don't ask me to make them for you. Make it yourself! Fork this repo, make modifications to the software as you'd like, and then when you're done, make a pull request. If your additions are well-structured and beneficial, I will merge your fork with the main branch.

# To-Do:
- Explain NGINX proxy config
- Come up with a better solution for attention tone detection (eventually)
- Circumvent overwrite of boiler.cfg and filters.cfg on re-running install.sh