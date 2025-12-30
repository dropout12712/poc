@echo off
:: Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed. Installing Python...
    :: Download Python (Windows x86_64 version)
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.10.6/python-3.10.6-amd64.exe' -OutFile 'python_installer.exe'"
    
    :: Install Python silently with PATH enabled
    start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    
    :: Clean up installer
    del python_installer.exe

    :: Refresh environment variables (may require a new session)
    setx PATH "%PATH%;C:\Program Files\Python310\Scripts\;C:\Program Files\Python310\"

    echo Python installed successfully.
) ELSE (
    echo Python is already installed.
)

:: Ensure pip is installed and upgraded
python -m ensurepip --default-pip
python -m pip install --upgrade pip

:: Install required libraries (requests, pillow)
echo Installing required Python libraries...
python -m pip install --upgrade pillow
python -m pip install --upgrade requests 

:: Confirm installation of libraries
echo Checking installed libraries...
python -m pip show requests
python -m pip show pillow


:: Done
echo Installation complete. You can now run your scripts.
pause
