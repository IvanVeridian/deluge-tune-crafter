# Deluge TuneCrafter

A Python application for converting audio files to MIDI format, specifically designed for use with the Synthstrom Deluge synthesizer. This tool processes audio files and generates XML files that are compatible with the Deluge's song format.

## Features

- Convert audio files to MIDI format using basic-pitch
- Convert MIDI files to XML format optimized for Synthstrom Deluge compatibility
- Supports various audio input formats
- Generates Deluge-compatible XML configurations

## Functionality

The program offers two main conversion paths:

1. **Full Audio to XML Conversion**
   - Converts audio files from `data/audio_input` to MIDI format
   - Automatically processes the generated MIDI files to Deluge-compatible XML
   - Uses basic-pitch for accurate audio-to-MIDI conversion
   - Final XML files can be directly loaded into your Deluge

2. **MIDI to XML Conversion**
   - Converts existing MIDI files from `data/input_midi` to Deluge XML format
   - Useful if you already have MIDI files and just need the Deluge format
   - Preserves MIDI note data and converts it to Deluge's song structure

Note: 
1. Basic-pitch produces a single track for all notes. It's best to feed a custom built midi file if possible in lieu of it's outputs. 
2. Well structured midi files will translate over to the Deluge song xml file. 
3. At the moment the instruments assigned to each track are randomized from this list:
    PRESET_NAMES = [
        "000 Rich Saw Bass",
        "001 Sync Bass",
        "002 Basic Square Bass",
        "003 Synthwave Bass",
        "005 Sweet Mono Bass",
        "006 Vaporwave Bass",
        "007 Detuned Saw Bass",
        "009 Hoover Bass",
        "019 Fizzy Strings",
        "026 Pw Organ",
        "030 Distant Porta",
        "040 Spacer Leader",
        "073 Piano",
        "074 Electric Piano",
        "076 Organ",
        "078 House",
    ]
4. The program utilizes a base.xml file found in src/resources. This way we avoid over-complicating the implementation and it simply injects the new tracks with randomly assigned presets to the base.xml file. 

## Prerequisites

- Python >=3.6
- FFmpeg (must be placed in the `bin/` folder)
  - Required files:
    - `bin/ffmpeg.exe`
    - `bin/ffprobe.exe`
  - You can download FFmpeg from [FFmpeg's official website](https://ffmpeg.org/download.html)

## Project Structure

```
DelugeMidiConverter/
├── src/
│   └── deluge_midi_converter/
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── midi_converter.py
│       │   ├── basic_pitch_processor.py
│       │   └── xml_injector.py
│       └── main.py
├── data/
│   ├── audio_input/   # Place input audio files here
│   ├── input_midi/    # Place input MIDI files here
│   ├── midi_output/   # Generated MIDI files will appear here
│   └── deluge_songs/  # Final Deluge XML song files
├── bin/
│   ├── ffmpeg.exe     # Required FFmpeg executable
│   └── ffprobe.exe    # Required FFprobe executable
├── logs/
│   └── app.log        # Application logs
└── requirements.txt   # Python dependencies
```

## Installation

1. Clone the repository:
```bash
git clone [https://github.com/IvanVeridian/deluge-tune-crafter.git]
cd DelugeMidiConverter
```

2. Create a virtual environment:
```bash
python -m venv .venv
```

3. Activate the virtual environment:
- Windows:
```bash
.venv\Scripts\activate
```
- Unix/MacOS:
```bash
source .venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

> **Note about Basic Pitch Installation**: 
> By default, this project uses the platform-specific version of Basic Pitch (ONNX for Windows, CoreML for MacOS, TensorFlowLite for Linux) for wider compatibility. While this works well, the TensorFlow version may provide better performance.
>
> To use the TensorFlow version instead:
> - Option 1: Modify `requirements.txt` to include `basic-pitch[tf]` instead of `basic-pitch`
> - Option 2: Manually install it after the other dependencies: `pip install basic-pitch[tf]`
>
> Note that TensorFlow is automatically included if you're using Python>=3.11.

5. Download and install FFmpeg:
   - Download FFmpeg from [FFmpeg's official website](https://ffmpeg.org/download.html)
   - Extract `ffmpeg.exe` and `ffprobe.exe`
   - Place both files in the `bin/` folder of the project

## Usage

1. Choose your conversion path:
   - For audio to XML: Place your audio files in `data/audio_input`
   - For MIDI to XML: Place your MIDI files in `data/input_midi`

2. Ensure FFmpeg executables are in the `bin/` directory

3. Run the converter:
```bash
python src/deluge_midi_converter/main.py
```

4. Select your desired conversion option from the menu:
   - Option 1: Full process (Audio → MIDI → XML)
   - Option 2: MIDI to XML only
   - Option 3: Exit

5. Find your converted files:
   - MIDI files in `data/midi_output`
   - Final XML files in `data/deluge_songs`
   - Check `logs/app.log` for conversion details

## Troubleshooting

- If you get FFmpeg-related errors, ensure both `ffmpeg.exe` and `ffprobe.exe` are correctly placed in the `bin/` directory
- Make sure your virtual environment is activated before running the converter
- Check the `logs/app.log` file for detailed error messages and debugging information

## Dependencies

See `requirements.txt` for a complete list of Python package dependencies.

## Thank You

This project wouldn't have been possible without the following contributions:

- [Downrush](https://github.com/jamiefaye/downrush) by Jamie Faye - The original midian code provided invaluable insights into the Deluge XML structure conversion, which inspired this Python-based implementation.

- [Basic Pitch](https://github.com/spotify/basic-pitch) by Spotify - A powerful and accurate audio-to-MIDI conversion engine that forms the backbone of our audio processing capabilities.

## License

This project is licensed under a modified MIT License:

- ✅ Free to use, modify, and distribute for personal and non-commercial purposes
- ✅ Free to fork and contribute to the project
- ✅ Must include the original license and copyright notice
- ❌ Commercial use requires explicit written permission from the author
- ❌ No liability or warranty provided

For commercial use inquiries, please contact the author.

## Contributing

We welcome contributions! Here's how you can help:

1. **Fork the Repository**
   - Create your own fork of the code
   - Clone your fork locally

2. **Create a Branch**
   - Create a new branch for your feature/fix
   - Use a clear naming convention (e.g., `feature/new-feature` or `fix/bug-description`)

3. **Code Standards**
   - Follow PEP 8 style guide for Python code
   - Add comments for complex logic
   - Update documentation as needed
   - Include type hints where applicable

4. **Testing**
   - Add tests for new features
   - Ensure all existing tests pass
   - Test with different audio formats if adding format support

5. **Commit Guidelines**
   - Use clear, descriptive commit messages
   - Reference issues in commits where applicable
   - Keep commits focused and atomic

6. **Submit a Pull Request**
   - Provide a clear description of the changes
   - Link any related issues
   - Ensure CI checks pass
   - Be responsive to review comments

7. **Code Review**
   - All contributions require review
   - Address review feedback promptly
   - Be open to suggestions and improvements

For major changes, please open an issue first to discuss what you would like to change. 