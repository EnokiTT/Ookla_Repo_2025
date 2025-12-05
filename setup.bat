@echo off
REM Installation script for Windows
REM This script sets up the Python environment and installs all dependencies

echo ================================
echo Ookla Data Analysis Setup Script
echo ================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

echo [OK] Python found:
python --version
echo.

REM Check if we're in the correct directory
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found. Please run this script from the project root directory.
    pause
    exit /b 1
)

REM Ask user if they want to create a virtual environment
set /p CREATE_VENV="Do you want to create a virtual environment? (recommended) [Y/n]: "
if "%CREATE_VENV%"=="" set CREATE_VENV=Y

if /i "%CREATE_VENV%"=="Y" (
    echo.
    echo [STEP] Creating virtual environment...
    python -m venv venv
    
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    
    echo [OK] Virtual environment created successfully
    echo.
    echo [STEP] Activating virtual environment...
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment activated
) else (
    echo.
    echo [WARNING] Installing packages globally (not recommended)
)

echo.
echo [STEP] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [STEP] Installing required packages...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Installation failed. Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo [STEP] Installing additional packages for Ookla data download...
pip install pyarrow fsspec s3fs

if errorlevel 1 (
    echo.
    echo [WARNING] Failed to install some additional packages
    echo You may need to install manually: pip install pyarrow fsspec s3fs
) else (
    echo [OK] Additional packages installed successfully!
)

echo.
echo [OK] All packages installed successfully!
echo.
echo ================================
echo Setup Complete!
echo ================================
echo.

if /i "%CREATE_VENV%"=="Y" (
    echo To activate the virtual environment in the future, run:
    echo   venv\Scripts\activate.bat
    echo.
    echo To deactivate the virtual environment, run:
    echo   deactivate
    echo.
)

echo To start Jupyter Notebook, run:
echo   jupyter notebook notebook\Ookla_Extractor.ipynb
echo.

pause
