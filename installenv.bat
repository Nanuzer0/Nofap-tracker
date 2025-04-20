@echo off
python -m venv env
call env\Scripts\activate.bat
pip install -r requirements.txt
echo Environment setup complete. To start the server, run startserver.bat.
pause