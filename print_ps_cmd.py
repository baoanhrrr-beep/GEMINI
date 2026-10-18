import os
ud = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data')
args = [
    f'--remote-debugging-port=12345',
    f'--user-data-dir={ud}',
    f'--profile-directory=Profile 88',
    'about:blank'
]
args_ps = ",".join(f'"{a}"' for a in args)
ps_cmd = f"Start-Process -FilePath 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe' -ArgumentList {args_ps}"
print(ps_cmd)
