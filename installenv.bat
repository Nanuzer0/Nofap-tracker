@echo off
python -m venv env
call env\Scripts\activate.bat
pip install -r requirements.txt
echo Virtual environment setup complete.
pause