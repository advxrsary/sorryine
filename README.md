
# Video File Enumeration and Download

This Python script allows you to enumerate and download video files from a given base URL. It supports resuming downloads, merging downloaded files into a single file, and converting the merged file to various output formats.

## Features

- Enumerates video files by incrementing a numeric value in the URL
- Downloads video files concurrently for faster performance
- Resumes downloads from the last downloaded file in case of interruption
- Merges downloaded files into a single file
- Converts the merged file to the desired output format (e.g., mp4, mkv, avi)
- Provides a progress table to monitor the download progress

## Requirements

- Python 3.x
- `requests` library
- `blessed` library
- `ffmpeg` (for merging and converting files)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/video-file-downloader.git
   ```

2. Install the required libraries:
   ```
   pip install requests blessed
   ```

3. Make sure you have `ffmpeg` installed on your system. You can download it from the official website: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

## Usage

```
python ine_enum.py [-h] [-s START] [-p PROGRESS_FILE] [-d] [-y] [-m] [-o OUTPUT] [-f FORMAT] [-c CONCURRENT] url
```

- `url`: Base URL for enumeration (required)
- `-s`, `--start`: Starting number for enumeration (default: 0)
- `-p`, `--progress-file`: File to store progress (default: progress.txt)
- `-d`, `--debug`: Enable debug mode
- `-y`, `--yes`: Automatically answer 'yes' to download prompt
- `-m`, `--merge`: Merge downloaded files into one
- `-o`, `--output`: Output file name for merged file
- `-f`, `--format`: Output format for merged file (default: ts)
- `-c`, `--concurrent`: Maximum number of concurrent downloads (default: 5)

## Examples

1. Enumerate and download video files starting from number 100:
   ```
   python ine_enum.py https://example.com/video/file- -s 100
   ```

2. Automatically download files and merge them into a single mp4 file:
   ```
   python ine_enum.py https://example.com/video/file- -y -m -f mp4
   ```

3. Specify the output file name and enable debug mode:
   ```
   python ine_enum.py https://example.com/video/file- -o merged_video.ts -d
   ```

## License

This project is licensed under the [MIT License](LICENSE).
