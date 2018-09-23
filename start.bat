@if exist CERT (
   python\python.exe accesser.py
) else (
   python\python.exe accesser.py -rr
) 