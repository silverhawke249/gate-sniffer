python dst_delay.py
:start
python fetch_and_start_app.py
python convert_gates.py
if errorlevel 1 goto :error
python copy_gate.py
goto :endscript
:error
echo error getting data. trying again...
goto :start
:endscript