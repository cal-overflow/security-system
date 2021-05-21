# Build the environment folders and files needed for storing data
echo "[BUILD] Constructing data storage directories."
mkdir data
mkdir data/recordings
mkdir data/stream_frames

echo "[BUILD] Checking for .env file."
ENV_FILE=.env
if test -f "$ENV_FILE"; then
  max=$(grep MAX_CLIENTS .env | cut -d '=' -f2)
else
  echo "[BUILD] .env file not found. Construcing new .env file with a default value of 5 clients maximum."
  max=5
  echo "MAX_CLIENTS=${max}" > .env
fi

for i in `seq 1 $max`
do
  mkdir data/stream_frames/$i
done

echo "[BUILD] Initializing essential data files."
touch data/blacklist.txt
echo "on" > data/alarm_status.txt
echo "0" > data/clients.txt


# Ensure that user has python 3.8.5 or later installed. Let them know if they do not.
echo "[BUILD] Checking Python environment"

pvs="$(python3 --version)"

if [[ "${pvs:7:1}" = "3" ]]; then
  echo "[BUILD] Python3 has been detected on your machine."
else
  echo "[BUILD FAIL] Python3 has not been found. Please install Python 3.8.5 or later and re-run this script."
  exit
fi

echo "\nEnsure python is up to date:\nLocal version: ${pvs:7:10}\nRequired version: 3.8.5 or later\n"

# Install python module dependencies (doesn't work for all environments)
echo "Installing Python modules using pip".
pipvs="$(pip --version)"
if [[ "${pipvs:0:4}" != "pip" ]]; then
  echo "[BUILD FAIL] Cannot detect pip."
  echo "\n---SOLUTION---\nEither\n 1) Install pip and re-run this script, or\n 2) manually install the following modules using pip."
  echo "opencv-python-headless\npython-decouple\nflask\nwaitress"
  exit
fi

pip install --upgrade pip
#pip install opencv-python-headless
#pip install python-decouple
#pip install flask
#pip install waitress
