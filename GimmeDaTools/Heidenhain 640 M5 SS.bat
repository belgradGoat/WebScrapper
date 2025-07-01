@echo off
::Version2 Prints Machine Name - 3/16/24 B. Sihler


::Edit as Needed No Spaces:
set mach=M5
set ipaddress=10.164.181.22
set TncFolder=M5-C42-HERM-UR\Seb


set input_file=%1
set python_script="C:\Users\sszewczyk\Documents\Batch_to_ScanV3_Experimental.py"

:: Download Pocket File from Machine itnc 640
"C:\Program Files (x86)\HEIDENHAIN\TNCremo\TNCCMD.exe" -I%ipaddress% Get TNC:\TABLE\TOOL_P.TCH "C:\Users\%USERNAME%\Desktop\TOOL_P.TXT"

:: Download the tool.t file from the machine
"C:\Program Files (x86)\HEIDENHAIN\TNCremo\TNCCMD.exe" -I%ipaddress% Get TNC:\TABLE\tool.t "C:\Users\%USERNAME%\Desktop\tool.t"

echo     *************************
echo     *  Machine %mach%   *
echo     *************************

:: Run the Python script with the provided input file
python %python_script% %input_file% %mach%

:: Set the Path variable (if needed)
set Path="C:\Program Files (x86)\HEIDENHAIN\TNCremo";c:\windows\system32

:: Upload the file using TNCcmd
TNCcmd -i%ipaddress% put %1 "TNC:\%TncFolder%\%~nx1"

setlocal
::Append the date to the sndto.log file
echo %USERNAME% %date% %mach%>> "\\re9-nlqh01.ecs.apple.com\PRLOU\APPLICATIONS\PRL_TOOL_DATA\sndto.log"
endlocal

@echo off
//echo This Will Explode in 10s
//timeout /t 10 /nobreak
//exit

:: Pause to see any error messages (optional)
pause
