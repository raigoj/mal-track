import subprocess
import re
import winreg

name = "mal-track.exe"
namealt = "maltrack.exe"
hknames = {
    winreg.HKEY_CURRENT_USER: "HKEY_CURRENT_USER",
    winreg.HKEY_LOCAL_MACHINE: "HKEY_LOCAL_MACHINE"
}
ipr = r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'
regpath = [
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce")
    ]

def killproc():
    taskout = subprocess.check_output(['tasklist', '/FI', f'imagename eq {name}', '/FO', 'CSV']).decode('utf-8')
    lines = taskout.strip().split('\n')
    if len(lines) <= 1:
        taskout = subprocess.check_output(['tasklist', '/FI', f'imagename eq {namealt}', '/FO', 'CSV']).decode('utf-8')
        lines = taskout.strip().split('\n')
        if len(lines) <= 1:
            print(f"{name} process not found")
    else:
        pid = int(lines[1].split(',')[1].strip('""'))
        out = subprocess.check_output(['wmic', 'process', 'where', f'ProcessId={pid}', 'get', 'ExecutablePath'], universal_newlines=True)
        lines = out.strip().split('\n')
        path = None
        if len(lines) > 2:
            path = lines[2].strip()
        if path:
            ips = set()
            with open(path, 'rb') as file:
                data = file.read()
                ips.update(re.findall(ipr, data.decode('latin-1')))
            if ips:
                print(f"Process '{name}' IP: {', '.join(ips)}")
            else:
                print(f"No IP for {path} {name}")
        subprocess.call(['taskkill', '/F', '/PID', str(pid)])
        print(f"{name} killed")

def delregkey():
    exists = False
    for hkey, skey in regpath:
        try:
            key = winreg.OpenKey(hkey, skey, 0, winreg.KEY_ALL_ACCESS)
            i = 0
            while True:
                try:
                    vname, vdata, _ = winreg.EnumValue(key, i)
                    if vdata.lower().endswith(f"\\{name.lower()}"):
                        key_path = "\\".join([hknames.get(hkey, str(hkey)), skey])
                        print(f"{name} found in {key_path}")
                        exists = True
                        winreg.DeleteValue(key, vname)
                        print(f"{vname} removed from start-up.")
                    if vdata.lower().endswith(f"\\{namealt.lower()}"):
                        key_path = "\\".join([hknames.get(hkey, str(hkey)), skey])
                        print(f"{namealt} found in {key_path}")
                        exists = True
                        winreg.DeleteValue(key, vname)
                        print(f"{vname} removed from start-up.")
                    i += 1
                except OSError:
                    break
        except FileNotFoundError:
            pass
    if not exists:
        print(f"{name} not found registry.")


if __name__ == "__main__":
    killproc()
    delregkey()