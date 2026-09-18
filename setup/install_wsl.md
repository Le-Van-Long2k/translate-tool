# Hướng dẫn cài lại WSL2 Ubuntu 22.04 trên Windows 11

## 1. Kiểm tra các distro WSL hiện tại

Mở **PowerShell** hoặc **Command Prompt (CMD)** và chạy:

```cmd
wsl -l -v
```

Nếu Ubuntu đang tồn tại, có thể thấy:

```text
  NAME            STATE           VERSION
* Ubuntu-22.04    Stopped         2
```

---

## 2. Tắt toàn bộ WSL

Chạy:

```cmd
wsl --shutdown
```

Lệnh này sẽ tắt tất cả các WSL instance đang chạy.

---

## 3. Xóa Ubuntu 22.04 hiện tại

> **Lưu ý:** `wsl --unregister` sẽ xóa toàn bộ dữ liệu của distro Ubuntu đó.

Chạy:

```cmd
wsl --unregister Ubuntu-22.04
```

Nếu thành công:

```text
Unregistering.
The operation completed successfully.
```

---

## 4. Kiểm tra lại danh sách WSL

Chạy:

```cmd
wsl -l -v
```

Nếu không còn distro nào, Windows sẽ hiển thị:

```text
Windows Subsystem for Linux has no installed distributions.

You can resolve this by installing a distribution with the instructions below:

Use 'wsl.exe --list --online' to list available distributions
and 'wsl.exe --install <Distro>' to install.
```

---

## 5. Kiểm tra các bản Ubuntu có thể cài

Có thể xem danh sách distro:

```cmd
wsl --list --online
```

Ví dụ:

```text
NAME            FRIENDLY NAME
Ubuntu          Ubuntu
Ubuntu-22.04    Ubuntu 22.04 LTS
Ubuntu-24.04    Ubuntu 24.04 LTS
```

---

## 6. Cài Ubuntu 22.04

Chạy:

```cmd
wsl --install -d Ubuntu-22.04
```

Windows sẽ tải Ubuntu:

```text
Downloading: Ubuntu 22.04 LTS
Installing: Ubuntu 22.04 LTS
```

Nếu cài đặt thành công:

```text
Distribution successfully installed.
It can be launched via 'wsl.exe -d Ubuntu-22.04'
```

Sau đó WSL sẽ tự khởi chạy Ubuntu:

```text
Launching Ubuntu-22.04...
Provisioning the new WSL instance Ubuntu-22.04
This might take a while...
```

---

## 7. Tạo tài khoản Linux

Trong lần chạy đầu tiên, Ubuntu sẽ yêu cầu tạo user:

```text
Create a default Unix user account:
```

Nhập username, ví dụ:

```text
dev
```

Sau đó nhập password:

```text
New password:
Retype new password:
```

> Khi nhập password trong Linux, màn hình **không hiển thị ký tự `*` hoặc ký tự nào cả**. Đây là hành vi bình thường.

Nếu thành công:

```text
passwd: password updated successfully
```

Ubuntu sẽ hiển thị hướng dẫn:

```text
To run a command as administrator (user "root"),
use "sudo <command>".
```

---

## 8. Kiểm tra Ubuntu đã cài thành công

Thoát khỏi Ubuntu:

```bash
exit
```

Quay lại CMD/PowerShell và chạy:

```cmd
wsl -l -v
```

Kết quả mong muốn:

```text
  NAME            STATE           VERSION
* Ubuntu-22.04    Stopped         2
```

Điểm quan trọng là:

```text
VERSION
2
```

Điều này xác nhận Ubuntu đang sử dụng **WSL 2**.

---

## 9. Khởi động Ubuntu

Có thể chạy:

```cmd
wsl -d Ubuntu-22.04
```

Hoặc đơn giản:

```cmd
wsl
```

Sau khi vào Ubuntu, kiểm tra:

```bash
uname -a
```

Kiểm tra phiên bản Ubuntu:

```bash
lsb_release -a
```

Ví dụ:

```text
Distributor ID: Ubuntu
Description:    Ubuntu 22.04 LTS
Release:        22.04
Codename:       jammy
```

---

## 10. Cập nhật Ubuntu sau khi cài

Nên cập nhật package ngay sau khi cài:

```bash
sudo apt update
sudo apt upgrade -y
```

Sau đó nên cài một số package cơ bản:

```bash
sudo apt install -y \
    build-essential \
    curl \
    wget \
    git \
    unzip \
    zip \
    ca-certificates \
    software-properties-common \
    make
```

---

## 11. Kiểm tra WSL từ Windows

Từ CMD/PowerShell:

```cmd
wsl --status
```

Kiểm tra phiên bản WSL:

```cmd
wsl --version
```

Kiểm tra distro:

```cmd
wsl -l -v
```

Kết quả cuối cùng nên tương tự:

```text
  NAME            STATE           VERSION
* Ubuntu-22.04    Running         2
```

---

# Tóm tắt toàn bộ quá trình

Nếu muốn cài lại hoàn toàn Ubuntu 22.04, các lệnh chính là:

```cmd
wsl --shutdown
```

```cmd
wsl --unregister Ubuntu-22.04
```

```cmd
wsl -l -v
```

```cmd
wsl --install -d Ubuntu-22.04
```

Sau khi Ubuntu được cài:

```bash
sudo apt update
sudo apt upgrade -y
```

Kiểm tra cuối cùng:

```cmd
wsl -l -v
```

Kết quả cần có:

```text
Ubuntu-22.04    Running/Stopped    2
```

---

# Lưu ý quan trọng

## `wsl --unregister` có nguy hiểm không?

Có.

Lệnh:

```cmd
wsl --unregister Ubuntu-22.04
```

xóa **toàn bộ filesystem của Ubuntu-22.04**.

Ví dụ các file:

```text
/home/dev/
~/projects/
~/translate-tool/
Docker-related files trong Ubuntu
SSH keys
Python environments
```

đều sẽ bị xóa nếu chúng nằm trong distro đó.

Vì vậy chỉ sử dụng `--unregister` khi thực sự muốn cài lại Ubuntu từ đầu.

## WSL 2

Nên kiểm tra distro đang chạy WSL 2:

```cmd
wsl -l -v
```

Nếu thấy:

```text
Ubuntu-22.04    Running    2
```

thì đã đúng.

Nếu Ubuntu đang ở version 1, có thể chuyển sang WSL 2:

```cmd
wsl --set-version Ubuntu-22.04 2
```

Đặt WSL 2 làm mặc định cho các distro cài mới:

```cmd
wsl --set-default-version 2
```
