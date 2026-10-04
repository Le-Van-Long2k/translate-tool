Nếu bạn muốn set lại RAM giới hạn cho WSL2

1. Mở PowerShell/CMD Windows
   notepad %UserProfile%\.wslconfig

Đặt:

[wsl2]
memory=4GB
swap=5GB

Nếu muốn WSL dùng tối đa 4 GB RAM.

2. Restart WSL
   wsl --shutdown
