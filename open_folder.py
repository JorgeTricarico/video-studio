import win32process

si = win32process.STARTUPINFO()
si.lpDesktop = "WinSta0\\Default"
path = r"C:\Users\admin\Desktop\Reels_Instagram_Edicion\REELS_Octubre_Johanna_Nueva_Ley_Pediatrica"
cmd = f'explorer.exe "{path}"'

hP, hT, pid, tid = win32process.CreateProcess(None, cmd, None, None, False, 0, None, None, si)
print("Opened Explorer window on user desktop! PID:", pid)
