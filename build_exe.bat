@echo off
chcp 65001 > nul
echo ============================================
echo  住宅ローン計算アプリ EXEビルドスクリプト
echo ============================================
echo.

:: Python がインストールされているか確認
python --version >nul 2>&1
if errorlevel 1 (
    echo [エラー] Python が見つかりません。
    echo https://www.python.org/ からインストールしてください。
    pause
    exit /b 1
)

echo [1/3] PyInstaller をインストール中...
pip install pyinstaller --quiet
if errorlevel 1 (
    echo [エラー] PyInstaller のインストールに失敗しました。
    pause
    exit /b 1
)

echo [2/3] EXE をビルド中...
pyinstaller mortgage_calculator.spec --clean --noconfirm
if errorlevel 1 (
    echo [エラー] ビルドに失敗しました。
    pause
    exit /b 1
)

echo [3/3] ビルド完了！
echo.
echo 生成ファイル: dist\住宅ローン計算アプリ.exe
echo.
echo EXEファイルを起動しますか？ (Y/N)
set /p answer=
if /i "%answer%"=="Y" (
    start "" "dist\住宅ローン計算アプリ.exe"
)

pause
