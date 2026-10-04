Chạy trong PowerShell as Administrator:
PowerShellSet-NetFirewallProfile -Profile Domain,Public,Private -Enabled False

Cách xử lý tốt nhất (không cần nhớ IP)
Thay vì hard-code 172.17.48.1, bạn nên lấy IP động mỗi lần dùng.
Trong WSL, dùng lệnh này:
Bash# Lấy IP Windows host tự động
WIN_IP=$(ip route | grep default | awk '{print $3}')
echo $WIN_IP

# Test

curl http://$WIN_IP:8085/health
