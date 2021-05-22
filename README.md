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
 3. [GNU Screen](https://www.gnu.org/software/screen/) (only required for server side)

## Deploying the system:

### 1) Clone the repository

### 2) Build the environment
  Run the bash script `sh build.sh` to automate the build process. This script will build all necessary data storage directories/files and then ensure that Python is up to date. If Python is up-to-date, the script will attempt to install all required modules (through Pip).

  If you see `BUILD SUCCESS` after running the script, skip to step **5**. Otherwise, read the `BUILD FAILURE` message provided by the script and follow the steps mentioned.

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


### 5) Start the program

#### Server:

  Deploy both Socket Server and Web Server in their own (detached) screens:

    screen -d -m -S server bash -c 'python3 server.py' && screen -d -m -S webserver bash -c 'python3 webserver.py'

  Or, just manually run both scripts: `python3 webserver.py` and `python3 server.py`.

#### Clients:

  Before you can deploy a client, you must change the `HOST` address found in the `client.py` script to match the URL of the machine running the Server. You can then run the client script `python3 client.py` and wait for the client to connect.


### 6) View the website:
  By default, the flask (web) server runs on port `8000`. You can view the website by visiting `http://serverIP:8000` on your browser, where `serverIP` is the local IP address of the machine acting as the Server.

  If you are trying to view the server from an outside network, then you will have to use the public IP address of the server, and might have to deal with some advanced networking. If that is the case, you may want to consider [port forwarding](https://en.wikipedia.org/wiki/Port_forwarding) and learning about [static vs. dynamic IP addresses](https://support.google.com/fiber/answer/3547208?hl=en).
