# OpenAI Text-to-Speech Tool

A desktop Text-to-Speech (TTS) app built with Python, Tkinter, and the OpenAI API.  
It converts text into natural-sounding speech with adjustable speed, voice, and playback controls.

## Features
- Convert text to speech using OpenAI's TTS models
- Choose from multiple voices
- Adjust playback speed
- Pause, resume, and replay specific sections
- Save audio as MP3
- Simple, clean GUI with character count and status display

##  Requirements
- Python 3.9+
- OpenAI API key (with TTS access)
- Internet connection

## Installation
1. **Clone the repository**
   ```
   git clone https://github.com/yourusername/tts-tool.git
   cd tts-tool
   ```

2. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   - Copy .env.example to .env
   - Add your OpenAI API key in .env:
    ```
    OPENAI_API_KEY=your_key_here
    ```
 4. **Run the app**
    ```
    python tts_tool.py
    ```

## File Structure
```
tts-tool/
├── tts_tool.py         # Main application
├── requirements.txt    # Python dependencies
├── .env.example        # Example environment variables file
├── .gitignore          # Files ignored by Git
└── LICENSE             # License file
```

## License
This project is licensed under the MIT License - see the LICENSE file for details.


