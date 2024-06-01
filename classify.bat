python -m venv venv
@echo
call ./venv/Scripts/activate.bat
python -m pip install -r .\requirements.txt
python %cd%\main.py
python %cd%\text_analysis.py
pause