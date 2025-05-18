#!/bin/bash
# set -euo pipefail

# Check for updates and upgrade
echo -e "[Checking for updates]\n"
sudo apt-get update
sudo apt-get upgrade -y

# Virtual display setup
echo -e "[Setting up virtual display]\n"
sudo apt-get install -y xvfb
cat > xvfb.service << EOF
[Unit]
Description=XVFB Display Server
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/Xvfb :99 -screen 0 1920x1080x24
User=nobody
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo mv xvfb.service /etc/systemd/system/
sudo systemctl enable xvfb.service
sudo systemctl start xvfb.service
echo "export DISPLAY=:99" >> ~/.bashrc
source ~/.bashrc

# Pulseaudio setup
echo -e "[Setting up pulseaudio]\n"
sudo apt-get install -y pulseaudio pulseaudio-utils
pulseaudio --daemonize=yes --disallow-exit=true
cat > meetbot.pa << EOF
load-module module-null-sink sink_name=virtual_sink sink_properties=device.description="VirtualSink"
set-default-sink virtual_sink
load-module module-remap-source source_name=virtual_source master=virtual_sink.monitor source_properties=device.description="VirtualSource"
set-default-source virtual_source
EOF
sudo mv meetbot.pa /etc/pulse/default.pa.d/meetbot.pa

# Virtual Camera Setup
echo -e "[Setting up v4l2 for Virtual Camera]\n"
sudo apt-get install -y linux-headers-$(uname -r) linux-modules-extra-$(uname -r)
sudo apt-get install -y v4l2loopback-utils # Do not install v4l2loopback-dkms unless needed
echo "v4l2loopback" | sudo tee /etc/modules-load.d/v4l2loopback.conf
echo "options v4l2loopback devices=1 video_nr=0 card_label=\"Logi MX Brio\" exclusive_caps=1" | sudo tee /etc/modprobe.d/v4l2loopback.conf
sudo usermod -aG video $USER

# Install ffmpeg
echo -e "[Installing ffmpeg]\n"
sudo apt-get install -y ffmpeg

# Install Google Chrome
echo -e "[Installing Google Chrome]\n"
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt-get install -y ./google-chrome-stable_current_amd64.deb

# Install Miniconda
echo -e "[Installing Miniconda]\n"
wget https://repo.anaconda.com/miniconda/Miniconda3-py312_25.3.1-1-Linux-x86_64.sh
chmod +x Miniconda3-py312_25.3.1-1-Linux-x86_64.sh
bash Miniconda3-py312_25.3.1-1-Linux-x86_64.sh -b -u -p ~/miniconda3
$HOME/miniconda3/bin/conda init bash --quiet
source ~/.bashrc

# Install requirements
echo -e "[Installing python requirements]\n"
pip install uv
uv pip install -r requirements.txt

echo -e "[Setup complete]\n"

echo -e "[Rebooting]\n"
sudo reboot
