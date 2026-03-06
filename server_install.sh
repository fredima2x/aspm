echo "Welcome to the ASPM server installation script!"
echo "This script will set up the server environment and install necessary dependencies."
echo "Please make sure you have Python 3.8 or higher installed on your system."

# Get server location from user input
read -p "Please enter the server location (e.g., /home/user/aspm/server): " SERVER_LOCATION
cd $SERVER_LOCATION

git clone https://github.com/fredima2x/aspm.git .
cd $SERVER_LOCATION/aspm
rm -rf ./.git ./client ./.github
cd $SERVER_LOCATION/aspm/server

# Create a virtual environment
python3 -m venv venv_aspm
source venv_aspm/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

echo "Server installation completed successfully!"
echo "You can start the server by running: source venv_aspm/bin/activate && python main.py"
