import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtMultimedia import QScreenCapture, QMediaCaptureSession, QVideoSink
from PySide6.QtCore import QTimer, Slot

app = QApplication(sys.argv)

screen_capture = QScreenCapture()
session = QMediaCaptureSession()
video_sink = QVideoSink()

session.setScreenCapture(screen_capture)
session.setVideoSink(video_sink)

captured = False

@Slot(object)
def on_frame(frame):
    global captured
    if captured or not frame.isValid():
        return

    image = frame.toImage()
    if image.isNull():
        return

    image.save("screenshot.png")
    print("✅ Đã lưu screenshot.png (không chớp)")
    captured = True
    screen_capture.setActive(False)
    QTimer.singleShot(100, app.quit)

video_sink.videoFrameChanged.connect(on_frame)

def on_error(error, msg):
    print("❌ Lỗi:", error, msg)
    app.quit()

screen_capture.errorOccurred.connect(on_error)

print("→ Dialog sẽ hiện ra, chọn màn hình rồi bấm Share/Allow")
screen_capture.setActive(True)

# Timeout 25 giây
QTimer.singleShot(25000, lambda: (print("Timeout"), app.quit()))
sys.exit(app.exec())