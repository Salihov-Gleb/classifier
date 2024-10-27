python -m venv venv
call ./venv/Scripts/activate.bat
@echo cd = %cd%
streamlit run .\pull_feeds.py
#legacy --global.dataFrameSerialization=arrow
pause