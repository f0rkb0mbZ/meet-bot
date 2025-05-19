# Google Meet Bot

A google meet bot with Selenium, FastAPI and Undetected Chromedriver, with a typer CLI and some websocket magic✨!

## Features

### Server to client commands
- ✅ Join a google meet with given URL
- ✅ Toggle mute / unmute
- ✅ Toggle video on / off
- ✅ Send a chat message to all participants
- ✅ Change meet layout for the bot
- ✅ Take a screenshot of the Meet window anytime
- ✅ Leave the meeting

### Client to server events
- ✅ Host has accepted bot
- ✅ Participant has joined the meeting
- ✅ Participant has left the meeting
- ✅ Completion events for all the server commands

### Bonus
- ✅ Play any video stream from the internet to the virtual camera

### Video Demo

[![meetbot-demo](https://r2.snehangshu.dev/meetbot-demo-thumbnail.jpg)](https://r2.snehangshu.dev/meetbot-demo.mp4)

## Setup

Quick Install script: [configure.sh](configure.sh). This script covers steps 1-7, then restarts the system to load display, audio, and video. After restart, run step 8 and the system is ready to run!

### 1. Set up an Ubuntu Server 24.04 VM

Spin up an Ubuntu Server 24.04 Virtual Machine. Fastest way to do that is using [Multipass](https://multipass.run/). Install and boot up a VM with following configuration, then check for updates:

```plaintext
- CPU: 4 Core
- Memory: 4 GB
- Disk: 10 GB
```

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 2. Virtual display setup
```bash
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
```

### 3. Pulseaudio setup
```bash
sudo apt-get install -y pulseaudio pulseaudio-utils
pulseaudio --daemonize=yes --disallow-exit=true
cat > meetbot.pa << EOF
load-module module-null-sink sink_name=virtual_sink sink_properties=device.description="VirtualSink"
set-default-sink virtual_sink
load-module module-remap-source source_name=virtual_source master=virtual_sink.monitor source_properties=device.description="VirtualSource"
set-default-source virtual_source
EOF
sudo mv meetbot.pa /etc/pulse/default.pa.d/meetbot.pa
```

### 4. Virtual Camera Setup
```bash
sudo apt-get install -y linux-headers-$(uname -r) linux-modules-extra-$(uname -r)
sudo apt-get install -y v4l2loopback-utils # Do not install v4l2loopback-dkms unless needed, already in kernel 6.8.0 / extras
echo "v4l2loopback" | sudo tee /etc/modules-load.d/v4l2loopback.conf
echo "options v4l2loopback devices=1 video_nr=0 card_label=\"Logi MX Brio\" exclusive_caps=1" | sudo tee /etc/modprobe.d/v4l2loopback.conf
sudo usermod -aG video $USER
```

### 5. Install ffmpeg
```bash
sudo apt-get install -y ffmpeg
```

### 6. Install Google Chrome
```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
```

### 7. Install Miniconda
```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-py312_25.3.1-1-Linux-x86_64.sh
chmod +x Miniconda3-py312_25.3.1-1-Linux-x86_64.sh
bash Miniconda3-py312_25.3.1-1-Linux-x86_64.sh -b -u -p ~/miniconda3
$HOME/miniconda3/bin/conda init bash --quiet
source ~/.bashrc
```

### 8. Install requirements
```bash
pip install uv
uv pip install -r requirements.txt
```

## Run
First we need to start a live feed to our virtual camera, otherwise it will not be detected by chrome. This plays back a 5s video ([https://r2.snehangshu.dev/bot_say_hello.mp4](https://r2.snehangshu.dev/bot_say_hello.mp4)) in loop to virtual camera `/dev/video0`:
```bash
python video2cam.py
```
Then, we need to spin up the server:
```bash
fastapi run api.py
```
Lastly, spin up the CLI:
```
python cli.py console
```
### CLI Docs

#### Main commands
```bash
python cli.py --help
                                                                                                                                                                                            
 Usage: cli.py [OPTIONS] COMMAND [ARGS]...                                                                                                                                                  
                                                                                                                                                                                            
 A console-like CLI built with Typer and WebSocket support.                                                                                                                                 
                                                                                                                                                                                            
                                                                                                                                                                                            
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current shell.                                                                                                                  │
│ --show-completion             Show completion for the current shell, to copy it or customize the installation.                                                                           │
│ --help                        Show this message and exit.                                                                                                                                │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ join-meeting        Join a meeting with meeting_url and bot_name                                                                                                                         │
│ leave-meeting       Leave the current meeting.                                                                                                                                           │
│ toggle-mute         Toggle the mute state of the current meeting.                                                                                                                        │
│ toggle-video        Toggle the video state of the current meeting.                                                                                                                       │
│ send-message        Send a message to the current meeting.                                                                                                                               │
│ change-layout       Change the layout of the current meeting.                                                                                                                            │
│ create-screenshot   Create a screenshot of the current window.                                                                                                                           │
│ console             Launch Meetbot CLI session with WebSocket logging.                                                                                                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

#### `join-meeting` subcommand
```bash
python cli.py join-meeting --help
                                                                                                                                                                                            
 Usage: cli.py join-meeting [OPTIONS] [MEETING_URL] [BOT_NAME]                                                                                                                              
                                                                                                                                                                                            
 Join a meeting with meeting_url and bot_name                                                                                                                                               
                                                                                                                                                                                            
                                                                                                                                                                                            
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│   meeting_url      [MEETING_URL]  Meeting URL to join. [default: None]                                                                                                                   │
│   bot_name         [BOT_NAME]     Name of the bot to join the meeting as. [default: Sidekick]                                                                                            │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                                                                                              │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```


#### `send-message` subcommand
```bash
python cli.py send-message --help
                                                                                                                                                                                            
 Usage: cli.py send-message [OPTIONS] [MESSAGE]...                                                                                                                                          
                                                                                                                                                                                            
 Send a message to the current meeting.                                                                                                                                                     
                                                                                                                                                                                            
                                                                                                                                                                                            
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│   message      [MESSAGE]...  Chat message to send. Can include spaces. [default: None]                                                                                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                                                                                              │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

#### `change-layout` subcommand
```bash
python cli.py change-layout --help
                                                                                                                                                                                            
 Usage: cli.py change-layout [OPTIONS] [LAYOUT]:[auto|tiled|spotlight|sidebar]                                                                                                              
                                                                                                                                                                                            
 Change the layout of the current meeting.                                                                                                                                                  
                                                                                                                                                                                            
                                                                                                                                                                                            
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│   layout      [LAYOUT]:[auto|tiled|spotlight|sidebar]  Layout to change to. [default: auto]                                                                                              │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                                                                                              │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```