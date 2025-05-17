# Google Meet Bot

## Pulseaudio setup
```bash
sudo apt-get install -y pulseaudio pulseaudio-utils
pulseaudio --daemonize=yes --disallow-exit=true
pactl load-module module-null-sink sink_name=virtual_sink sink_properties=device.description="VirtualSink"
pactl set-default-sink virtual_sink
pactl load-module module-remap-source source_name=virtual_source master=virtual_sink.monitor source_properties=device.description="VirtualSource"
pactl set-default-source virtual_source
```

## Virtual Camera Setup
```bash
sudo apt install -y v4l2loopback-dkms v4l2loopback-utils # Do not install dkms for kernel 6.8.0 as it is already available
sudo modprobe v4l2loopback devices=1 video_nr=10 card_label="Logi MX Brio" exclusive_caps=1
# persist
echo "v4l2loopback" | sudo tee /etc/modules-load.d/v4l2loopback.conf
echo "options v4l2loopback devices=1 video_nr=10 card_label="Logi MX Brio" exclusive_caps=1" | sudo tee /etc/modprobe.d/v4l2loopback.conf

```

## Playback video in loop
```bash
ffmpeg -stream_loop -1 -re -i meetbot/bot_say_hello.mp4 -vcodec rawvideo -pix_fmt yuv420p -f v4l2 /dev/video0
```

sudo apt update
sudo apt install --reinstall linux-headers-$(uname -r) linux-modules-extra-$(uname -r)
