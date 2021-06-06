# Security-System
Custom built security system that (optionally) alerts the user via email when motion has been detected. The system also records video streams when motion is detected for later viewing.

## How it works

This security system works has three main components.

**Socket Server:** Receives live camera feeds from connected clients. Processes video recording and security alerts.

**Web Server:** Displays live camera feed from Socket Server onto a webpage.

**Client:** Sends video feed to the Socket Server.

The Socket Server and Web Server must run on the same machine, whereas the client(s) can run separately.

## Environment requirements:

 1. [Python 3.8.5](https://www.python.org/downloads/release/python-385/) or later
 2. [Pip](https://pypi.org/project/pip/) (package installer for Python)
 3. [FFMPEG](https://www.ffmpeg.org/) (only required for server side)
 <!--- 4. H264 Codec 1.8 for FFMPEG. Download [here](https://github.com/cisco/openh264/releases) -->
 <!-- 5.-->
 4. Optional: [GNU Screen](https://www.gnu.org/software/screen/) (helpful for server side)

## Deploying the system:

### 1) Clone the repository

### 2) Build the environment
  Run the bash script `bash build.sh` to automate the build process. This script will build all necessary data storage directories/files and then ensure that Python is up to date. If Python is up-to-date, the script will attempt to install all required modules (through Pip).

  If you see `BUILD SUCCESS` after running the script, skip to [**step 5**](#5-install-ffmpeg). Otherwise, read the `BUILD FAILURE` message provided by the script and follow the steps mentioned.

  If you are unable to run the bash script, continue following this documentation to properly build your environment.

  **a)** Create a .env file with default values:

    echo "MAX_CLIENTS=5" > .env && echo "SECONDS=30" >> .env && echo "RECORDING_TYPE=mp4" >> .env && echo "GMAIL_USER=" >> .env && echo "GMAIL_APP_PASSWORD=" >> .env

  The Environment Variables and their default values are:
  - **MAX_CLIENTS:** 5 - The maximum number of clients that can connect to the server at one time
  - **SECONDS:** 30 - The number of seconds that are recorded before and after motion is detected
  - **RECORDING_TYPE:** mp4 - The type of video recordings that are produced by the server. `mp4` and `avi` are the only accepted options.
  - **GMAIL_USER:** unset
  - **GMAIL_APP_PASSWORD:** unset

  Learn about connecting gmail account with app-specific passwords [here](https://support.google.com/accounts/answer/185833?hl=en).

**b)** Create the necessary storage directories and files:

    mkdir static/recordings && mkdir data && mkdir data/stream_frames && touch data/whitelist.txt data/blacklist.txt && echo "0" > data/clients.txt && echo "on" > data/alarm_status.txt

**c)** Create subfolders for the client frames:

    cd data/stream_frames && mkdir 1 2 3 4 5 && cd ../../

  If you have changed the value of `MAX_CLIENTS` from its default value of 5, be sure to include all numbers from 1 to `MAX_CLIENTS` in the `mkdir` command.

### 3) Manually install Python 3.8.5 (or later) and Pip
  Visit [Python's official website](https://www.python.org/) > Downloads > Python 3.8.5 or later > follow the instructions specific to your operating system.

  Pip should come installed with all versions of Python >= 3.4 ([Source](https://pip.pypa.io/en/stable/installing/)). If you do not have Pip installed or are unable to use Pip to install packages, view the [Pip documentation](https://pip.pypa.io/en/stable/).

### 4) Manually install Python packages using Pip
  The build script attempts to install Python packages using four different possible Pip installation commands:

    pip install SomePackage
    pip3 install SomePackage
    python -m pip install SomePackage
    python3 -m pip install SomePackage

  If none of the above commands work, then it is likely Pip is not installed correctly. It is also possible that there is some other problem with the build script executing Pip installations.

  The quickest solution would be to check your Pip installation and manually install the required Python packages using Pip:

#### Server:

  - opencv
  - pickle
  - decouple
  - flask
  - waitress

#### Clients:
  - opencv
  - pickle
  - decouple

### 5) Install FFMPEG

  FFMPEG is a video and audio processing tool that is essential for the recording of videos with this security system. You can install FFMPEG via the [official website](https://www.ffmpeg.org/). [Here](https://www.wikihow.com/Install-FFmpeg-on-Windows) is a helpful guide for installing it on Windows operating Systems.

### 6) Start the program

#### Server:

  Deploy both Socket Server and Web Server in their own (detached) screens:

    screen -d -m -S server bash -c 'python3 server.py' && screen -d -m -S webserver bash -c 'python3 webserver.py'

  Or, just manually run both scripts: `python3 webserver.py` and `python3 server.py`.

#### Clients:

  Before you can deploy a client, you must change the `HOST` address found in the `client.py` script to match the URL of the machine running the Server. You can then run the client script `python3 client.py` and wait for the client to connect.


### 7) View the website:
  By default, the flask (web) server runs on port `8000`. You can view the website by visiting `http://serverIP:8000` on your browser, where `serverIP` is the local IP address of the machine acting as the Server.

  If you are trying to view the server from an outside network, then you will have to use the public IP address of the server, and might have to deal with some advanced networking. If that is the case, you may want to consider [port forwarding](https://en.wikipedia.org/wiki/Port_forwarding) and learning about [static vs. dynamic IP addresses](https://support.google.com/fiber/answer/3547208?hl=en).

### Troubleshooting
##### [OpenCV - Import Error](https://stackoverflow.com/a/56972113)

##### [OpenCV - The function is not implemented](https://stackoverflow.com/questions/14655969/opencv-error-the-function-is-not-implemented)

##### *cvWaitKey - the function is not implemented*

Try uninstalling opencv-headless and installing normal opencv. Use a variant of the command listed below

    pip uninstall opencv-python-headless && pip install opencv-python
