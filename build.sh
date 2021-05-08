# Build the environment folders and files needed for storing data
mkdir data
mkdir data/recordings
mkdir data/stream_frames

max=5
for i in `seq 1 $max`
do
  mkdir data/stream_frames/$i
done

touch data/blacklist.txt
echo "on" > data/alarm_status.txt
echo "0" > data/clients.txt

# Install python module dependencies (doesn't work for all environments)
pip install --upgrade pip
pip install opencv-python-headless
pip install flask
