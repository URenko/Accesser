@sysproxy.exe pac http://127.0.0.1:7654/pac/?t=%random%
@if exist CERT (
   python\python.exe accesser.py
) else (
   python\python.exe accesser.py -rr
) 