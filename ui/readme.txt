sudo apt install \
    gstreamer1.0-tools \
    gstreamer1.0-pipewire \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    python3-gst-1.0 \
    python3-gi

sudo apt install python3-gi python3-gst-1.0



python3.12 -m venv --system-site-packages venv
source venv/bin/activate
pip install PySide6
pip install dbus-next
pip install opencv-python
pip install pydantic