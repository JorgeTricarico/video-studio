import win32process

si = win32process.STARTUPINFO()
si.lpDesktop = "WinSta0\\Default"
url = "https://drive.google.com/drive/folders/1ksGmRs2YYQhI4pF6HMkNZ886H4mvIKF2"
cmd = f'"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" "{url}"'

hProcess, hThread, dwProcessId, dwThreadId = win32process.CreateProcess(
    None, cmd, None, None, False, 0, None, None, si
)
print("Launched Chrome on user desktop with PID:", dwProcessId)
