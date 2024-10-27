python -m venv venv
call ./venv/Scripts/activate.bat
python -m pip install -r .\requirements.txt
SET DATE_START=%date% %time%
python %cd%\cycle_runner.py
python %cd%\theme_classifier.py
python %cd%\export_feeds.py