@echo cd = %cd%
python -m venv venv
@echo
call ./venv/Scripts/activate.bat
pip install -r %cd%\requirements.txt
pause