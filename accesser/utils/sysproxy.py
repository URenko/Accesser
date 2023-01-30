import sys
from . import setting

if sys.platform.startswith('win'):
    from ctypes import windll
    import winreg

#TODO: use Windows API instead of winreg, see https://github.com/Noisyfox/sysproxy for example.

def set_pac(pac):
    if setting.config['setproxy'] and sys.platform.startswith('win'):
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                        r'Software\Microsoft\Windows\CurrentVersion\Internet Settings',
                                        0, winreg.KEY_ALL_ACCESS) as INTERNET_SETTINGS:
            if pac is None:
                winreg.DeleteValue(INTERNET_SETTINGS, 'AutoConfigURL')
            else:
                winreg.SetValueEx(INTERNET_SETTINGS, 'AutoConfigURL', 0, winreg.REG_SZ, pac)

        INTERNET_OPTION_REFRESH = 37
        INTERNET_OPTION_SETTINGS_CHANGED = 39
        windll.Wininet.InternetSetOptionW(0, INTERNET_OPTION_REFRESH, 0, 0)
        windll.Wininet.InternetSetOptionW(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)