SEPERATOR="---------------------------------------------------";
echo "[ABOUT] Security System program by Christian Lisle (http://christianlisle.com)"
echo "[ABOUT] Learn More about this project: https://github.com/ChristianLisle/Security-System"
echo "[ABOUT] This bash script constructs necessary storage arrangements and ensures that the local environment is suitable to run the program."
# Build the environment folders and files needed for storing data
echo "${SEPERATOR}\n[BUILD] Constructing data storage directories, setting data values, and creating essential storage files."

directories=("data" "data/recordings" "data/stream_frames")

for directory in ${directories[@]}
do
  DIR="${directory}"
  if [ ! -d "$DIR" ]; then
    echo "[BUILD] Creating directory: ${directory}"
    mkdir "${directory}"
  fi
done

ENV_FILE=.env
if test -f "$ENV_FILE"; then
  max=$(grep MAX_CLIENTS .env | cut -d '=' -f2)
else
  max=5
  echo "[BUILD] .env file not found.\n[BUILD] Construcing new .env file with a default MAX_CLIENTS of 5."
  echo "MAX_CLIENTS=${max}\nGMAIL_USER=\nGMAIL_APP_PASSWORD=" > .env
fi

for i in `seq 1 $max`
do
  if [ ! -d "${directories[2]}/${i}" ]; then
    echo "[BUILD] Creating storage directory: data/stream_frames/${i}"
    mkdir data/stream_frames/$i
  fi
done

touch data/blacklist.txt
echo "on" > data/alarm_status.txt
echo "0" > data/clients.txt

echo "${SEPERATOR}\n[BUILD] Checking Python version"
pvs="$(python3 --version)"
IFS='.' read -r -a version <<< "${pvs:7:20}" # convert Python version string to array (i.e., "3.8.5" to 3 8 5)

# Check that machine is using Python 3.8.5 or later
valid=false
if [ $((${version[0]} + 0)) == 3 ]; then
  if [ $((${version[1]} + 0)) == 8 ] && [ $((${version[2]} + 0)) -ge 5 ]; then
      valid=true
  elif [ $((${version[1]} + 0)) -gt 8 ]; then
    valid=true
  fi
elif [[ $((${version[0]} + 0)) -gt 3 ]]; then
  valid=true
fi

if [ valid ]; then
  echo "[BUILD] Your Python version (${pvs:7:10}) is sufficient."
else
  echo "[BUILD] Your Python version (${pvs:7:10}) is older than the recommended version, Python 3.8.5. Consider updating before running the program."
fi

# Install python module dependencies.
echo "${SEPERATOR}\n[BUILD] Installing Python modules using pip. ${WARNING}"

# Install pip commands using pip3 or pip. If neither commands work, alert the user.
{
  pip3 install --upgrade pip
  pip3 install opencv-python-headless
  pip3 install python-decouple
  pip3 install flask
  pip3 install waitress
} || {
  pip install --upgrade pip
  pip install opencv-python-headless
  pip install python-decouple
  pip install flask
  pip install waitress
}|| {
  echo "[FAILURE] Could not install Python modules using pip. Manually install Python modules listed on the README. Your environment should then be ready."
  exit
}

echo "[SUCCESS] Your environment appears to be sufficient for this program. View the README (https://github.com/ChristianLisle/Security-System) for information on how to run the program."
