import win32process
import time
import threading
import win32service, win32gui, win32con, win32ui, ctypes
from PIL import Image

for prof in ['Profile 1', 'Profile 3']:
    print(f"Testing {prof}...")
    si = win32process.STARTUPINFO()
    si.lpDesktop = "WinSta0\\Default"
    url = "https://drive.google.com/drive/folders/1ksGmRs2YYQhI4pF6HMkNZ886H4mvIKF2"
    cmd = f'"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --profile-directory="{prof}" "{url}"'
    hP, hT, pid, tid = win32process.CreateProcess(None, cmd, None, None, False, 0, None, None, si)
    time.sleep(6)

def capture_all():
    desk = win32service.OpenDesktop('Default', 0, False, win32con.MAXIMUM_ALLOWED)
    desk.SetThreadDesktop()
    def cb(h, _):
        if win32gui.IsWindowVisible(h):
            t = win32gui.GetWindowText(h)
            if 'chrome' in t.lower() or 'drive' in t.lower():
                print(f"HWND {h}: {t}")
    win32gui.EnumWindows(cb, None)

t = threading.Thread(target=capture_all)
t.start()
t.join()
