# 🖱️ Mouse and Keyboard Macro Recorder

A comprehensive Python application for recording and replaying mouse and keyboard actions with a user-friendly Flask web interface.

## 📋 Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## ✨ Features

### Recording Capabilities
- **Mouse Actions**: Clicks, movements, and scroll events
- **Keyboard Actions**: Key presses and releases
- **Intelligent Recording**: Throttled mouse movements to avoid excessive events
- **Auto-Save**: Automatically saves macros with timestamp-based names
- **Manual Save**: Option to save with custom names and descriptions

### Playback Features
- **Variable Speed**: Control playback speed (0.5x to 2.0x)
- **Repeat Functionality**: Play macros multiple times
- **Loop Mode**: Continuous playback until stopped with hotkeys
- **Hotkey Control**: Stop loop playback with Ctrl+S or ESC

### Web Interface
- **Modern UI**: Clean, responsive web interface
- **Real-time Status**: Live recording status and event counts
- **Macro Library**: Browse, play, and manage saved macros
- **Cross-platform**: Works on Windows, macOS, and Linux

## 🔧 Requirements

- Python 3.7+
- Required Python packages:
  - `flask`
  - `pynput`

## 📦 Installation

### 1. Clone or Download
Download the project files to your local machine.

### 2. Set Up Virtual Environment (Recommended)

#### On Windows:
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### On macOS/Linux:
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Install Dependencies Manually (if requirements.txt is not available)
```bash
pip install flask pynput
```

## 🚀 Usage

### 1. Start the Application
```bash
# Make sure your virtual environment is activated
python app.py
```

### 2. Open Web Interface
Open your browser and navigate to:
```
http://localhost:5000
```

### 3. Recording Macros

1. **Start Recording**: Click the "▶️ Start Recording" button
2. **Perform Actions**: Execute the mouse clicks, movements, and keyboard inputs you want to record
3. **Stop Recording**: Click "⏹️ Stop Recording" when finished
4. **Auto-Save**: Macro is automatically saved with a timestamp name (e.g., `macro_20250702_143045`)

### 4. Playing Macros

#### Current Macro (just recorded):
- **Play Once**: Click "▶️ Play Current"
- **Loop Mode**: Click "🔄 Loop Current" (stop with Ctrl+S or ESC)

#### Saved Macros:
- Browse the macro library
- Click "▶️ Play" for single playback
- Click "🔄 Loop" for continuous playback

### 5. Playback Controls

- **Speed Control**: Adjust playback speed from 0.5x to 2.0x
- **Repeat Count**: Set number of repetitions (1-100)
- **Loop Delay**: Set delay between loop iterations (0-10 seconds)

### 6. Managing Macros

- **Custom Names**: Optionally rename auto-saved macros
- **Descriptions**: Add descriptions to your macros
- **Delete**: Remove unwanted macros from the library
- **Refresh**: Update the macro list

## 📁 Project Structure

```
macro-recorder/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── macros/               # Directory for saved macros
    ├── macro_20250702_143045.json
    ├── macro_20250702_143120.json
    └── ...
```

### Key Components

- **MacroRecorder**: Handles recording of mouse and keyboard events
- **MacroPlayer**: Manages playback of recorded macros
- **MacroManager**: Handles saving, loading, and managing macro files
- **Flask Web App**: Provides the user interface and API endpoints

### Macro File Format

Macros are saved as JSON files containing:
```json
{
  "name": "macro_20250702_143045",
  "description": "Auto-saved macro: 5 clicks, 12 key presses, 3.2s duration",
  "created": "2025-07-02T14:30:45.123456",
  "events": [
    {
      "type": "mouse_click",
      "timestamp": 0.0,
      "x": 100,
      "y": 200,
      "button": "Button.left",
      "pressed": true
    },
    // ... more events
  ]
}
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main web interface |
| `/start_recording` | POST | Start recording events |
| `/stop_recording` | POST | Stop recording and auto-save |
| `/get_event_count` | GET | Get current event count |
| `/save_macro` | POST | Save macro with custom name |
| `/play_macro` | POST | Play current macro |
| `/play_saved_macro` | POST | Play a saved macro |
| `/play_macro_loop` | POST | Play macro in loop mode |
| `/stop_playback` | POST | Stop current playback |
| `/list_macros` | GET | Get list of saved macros |
| `/delete_macro` | POST | Delete a saved macro |

## 🛠️ Troubleshooting

### Permission Issues

#### macOS:
- Go to **System Preferences** > **Security & Privacy** > **Privacy**
- Add your terminal application to **Accessibility** and **Input Monitoring**
- Restart the application

#### Linux:
- Ensure you have the necessary permissions for input devices
- You may need to run with sudo for some distributions

#### Windows:
- Run the command prompt as Administrator if you encounter permission issues

### Common Issues

1. **"Module not found" errors**:
   - Ensure virtual environment is activated
   - Install requirements: `pip install -r requirements.txt`

2. **Recording not working**:
   - Check system permissions for accessibility/input monitoring
   - Restart the application after granting permissions

3. **Web interface not loading**:
   - Check if port 5000 is available
   - Try a different port by modifying the last line in `app.py`

4. **Playback too fast/slow**:
   - Adjust the speed control in the web interface
   - Default is 1.0x (normal speed)

### Performance Tips

- **Mouse Movement Throttling**: The app automatically throttles mouse movements to prevent excessive events
- **Memory Usage**: Clear recordings when not needed to free memory
- **Loop Playback**: Use Ctrl+S or ESC to stop infinite loops

## 🔒 Security Considerations

- This application requires permissions to monitor and control mouse/keyboard input
- Only grant permissions if you trust the application
- Be cautious when running macros that perform system actions
- Review recorded macros before sharing them

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly on your platform
5. Submit a pull request

## 📝 License

This project is provided as-is for educational and productivity purposes. Please use responsibly and in accordance with your local laws and regulations.

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Ensure all dependencies are installed correctly
3. Verify system permissions are granted
4. Check the console output for error messages

---

**Happy Automation! 🎉**