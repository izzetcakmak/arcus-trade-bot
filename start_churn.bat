@echo off
cd /d %~dp0
:loop
python churn.py >> churn.log 2>&1
echo churn cikti (%date% %time%), 60 sn sonra yeniden >> churn.log
timeout /t 60 /nobreak >nul
goto loop
