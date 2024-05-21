import argparse
import requests
import os
import signal
import sys
import shutil
import blessed
# Commenting out the progress bar
# from progress.bar import FillingSquaresBar
from concurrent.futures import ThreadPoolExecutor, as_completed

# ANSI escape codes for colors
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

term = blessed.Terminal()

def enumerate_urls(base_url, progress_file, start_num, debug=False):
    extension = ".ts"
    consecutive_denials = 0
    max_num = start_num
    video_files = []

    def save_progress():
        with open(progress_file, "w") as f:
            f.write(f"{max_num}\n")
            f.write("\n".join(video_files))

    def signal_handler(sig, frame):
        print("\nProcess interrupted. Saving progress...")
        save_progress()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    if os.path.exists(progress_file):
        try:
            with open(progress_file, "r") as f:
                lines = f.read().splitlines()
                if lines:
                    max_num = int(lines[0])
                    video_files = lines[1:]
                    start_num = max_num + 1
        except (ValueError, IndexError):
            print(f"Error: Invalid progress file format in {progress_file}. Starting from scratch.")

    print(f"Starting enumeration from number: {start_num}")

    current_num = start_num
    while True:
        url = f"{base_url.rsplit('-', 1)[0]}-{current_num}{extension}"

        try:
            response = requests.head(url, timeout=10)  # Set a timeout for the request
            status_code = response.status_code

            if status_code == 200:
                if debug:
                    print(f"\nSuccessful response: {url}")
                video_files.append(url)
                max_num = current_num
                consecutive_denials = 0

                current_num += 1
                print(f"\rEnumerating: {start_num} - {current_num}", end="", flush=True)
            else:
                if debug:
                    print(f"\nDenied response: {url}")
                consecutive_denials += 1

                if consecutive_denials == 3:
                    print(f"\nEncountered three consecutive denials. Enumeration complete at number: {current_num}")
                    save_progress()
                    break

        except requests.exceptions.RequestException as e:
            print(f"\nError occurred: {e}")
            save_progress()
            break

    print()  # Print a newline after enumeration is complete
    return video_files

def download_video_file(video_file, directory, max_retries=3):
    file_name = os.path.basename(video_file)
    file_path = os.path.join(directory, file_name)

    if os.path.exists(file_path):
        print(f"{file_name} already exists. Skipping download.")
        return file_name, os.path.getsize(file_path)

    retry_count = 0
    while retry_count < max_retries:
        try:
            response = requests.get(video_file, stream=True, timeout=10)  # Set a timeout for the request
            response.raise_for_status()  # Raise an exception for non-2xx status codes
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while downloading {file_name}: {e}")
            retry_count += 1
            continue

        total_size = int(response.headers.get("Content-Length", 0))
        block_size = 1024
        # Commenting out the progress bar
        # progress_bar = FillingSquaresBar(f'{GREEN}Downloading{RESET}', max=total_size, suffix=f'{GREEN}%(percent)d%%{RESET}', fill='▣', hide_cursor=True)

        with open(file_path, "wb") as file:
            for data in response.iter_content(block_size):
                size = file.write(data)
                # Commenting out the progress bar
                # progress_bar.next(size)
        # Commenting out the progress bar
        # progress_bar.finish()

        return file_name, total_size

    return file_name, 0

def download_video_files(video_files, directory, max_concurrent_downloads=5, always_continue=False):
    completed_downloads = 0
    total_size = 0
    failed_downloads = []

    os.makedirs(directory, exist_ok=True)

    def update_progress_table(progress_data, failed_data):
        # Clear the previous table
        with term.cbreak(), term.hidden_cursor():
            print(term.home + term.clear, end='')

            table_separator = "=" * 80
            header = f"{'Name':<40} {'Progress':<20} {'Size':<10}"

            print(table_separator)
            print(header)
            print(table_separator)

            for item in progress_data:
                name, progress, size = item
                print(f"{name:<40} {progress:<20} {size:.2f} MB")

            for item in failed_data:
                name = item
                print(f"{RED}{name:<40} {'Failed':>30}{RESET}")

            print(table_separator)

    with ThreadPoolExecutor(max_workers=max_concurrent_downloads) as executor:
        futures = []
        progress_data = []

        for video_file in video_files:
            future = executor.submit(download_video_file, video_file, directory)
            futures.append(future)

            if len(futures) >= max_concurrent_downloads:
                for future in as_completed(futures):
                    file_name, size = future.result()
                    if size > 0:  # Successful download
                        completed_downloads += 1
                        total_size += size

                        progress = f"{GREEN}[{completed_downloads}/{len(video_files)}]{RESET}"
                        progress_data.append((file_name, progress, size / 1024 / 1024))

                    else:  # Failed download
                        failed_downloads.append(file_name)

                    if len(progress_data) > max_concurrent_downloads:
                        progress_data.pop(0)

                    update_progress_table(progress_data, failed_downloads)

                futures = []

        for future in as_completed(futures):
            file_name, size = future.result()
            if size > 0:  # Successful download
                completed_downloads += 1
                total_size += size

                progress = f"{GREEN}[{completed_downloads}/{len(video_files)}]{RESET}"
                progress_data.append((file_name, progress, size / 1024 / 1024))

            else:  # Failed download
                failed_downloads.append(file_name)

            if len(progress_data) > max_concurrent_downloads:
                progress_data.pop(0)

            update_progress_table(progress_data, failed_downloads)

    if failed_downloads:
        if always_continue or args.yes:
            print(f"{RED}WARNING: {len(failed_downloads)} files failed to download. Video may be incomplete.{RESET}")
        else:
            while True:
                choice = input(f"{RED}WARNING: {len(failed_downloads)} files failed to download. Video may be incomplete. Do you want to continue? (y/n/a): {RESET}").lower()
                if choice == 'y':
                    break
                elif choice == 'n':
                    print("Aborting the process.")
                    sys.exit(0)
                elif choice == 'a':
                    always_continue = True
                    break
                else:
                    print("Invalid choice. Please enter 'y', 'n', or 'a'.")

    print(f"{GREEN}Downloaded {completed_downloads} video files. Total size: {total_size/1024/1024:.2f} MB{RESET}")

    return always_continue


def merge_files(directory, merged_file, output_format):
    file_list = sorted([file for file in os.listdir(directory) if file.endswith(".ts")], key=lambda x: int(x.split("-")[-1].split(".")[0]))

    with open(merged_file, "wb") as outfile:
        for file_name in file_list:
            file_path = os.path.join(directory, file_name)
            with open(file_path, "rb") as infile:
                shutil.copyfileobj(infile, outfile)
            os.remove(file_path)

    if output_format != "ts":
        try:
            os.system(f"ffmpeg -i {merged_file} -c copy -copy_unknown {merged_file[:-3]}.{output_format}")
        except Exception as e:
            print(f"Error occurred while converting to {output_format}: {e}")
        finally:
            os.remove(merged_file)


def main():
    parser = argparse.ArgumentParser(description="Video file enumeration and download script.")
    parser.add_argument("url", help="Base URL for enumeration")
    parser.add_argument("-s", "--start", type=int, help="Starting number for enumeration (default: 0)")
    parser.add_argument("-p", "--progress-file", default="progress.txt", help="File to store progress (default: progress.txt)")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("-y", "--yes", action="store_true", help="Automatically answer 'yes' to download prompt")
    parser.add_argument("-m", "--merge", action="store_true", help="Merge downloaded files into one")
    parser.add_argument("-o", "--output", help="Output file name for merged file")
    parser.add_argument("-f", "--format", default="ts", help="Output format for merged file (default: ts)")
    parser.add_argument("-c", "--concurrent", type=int, default=5, help="Maximum number of concurrent downloads (default: 5)")
    args = parser.parse_args()

    base_url = args.url
    start_num = args.start or 0
    progress_file = args.progress_file
    debug = args.debug
    output_format = args.format.lower()
    max_concurrent_downloads = args.concurrent

    video_files = enumerate_urls(base_url, progress_file, start_num, debug)

    if video_files:
        total_size = sum(int(requests.head(url, timeout=10).headers.get("Content-Length", 0)) for url in video_files)
        print(f"Found {len(video_files)} video files. Total size: {total_size/1024/1024:.2f} MB")

        if args.yes:
            download_choice = True
        else:
            download_choice = input("Do you want to download the video files? (y/n): ").lower() == 'y'

        if download_choice:
            directory = f"downloads_{base_url.split('/')[-3]}"
            always_continue = download_video_files(video_files, directory, max_concurrent_downloads, args.yes)

            if args.merge or args.output:
                merged_file = args.output or f"{directory}_merged.ts"
                if not args.format:
                    available_formats = ["ts", "mp4", "mkv", "avi"]
                    print("Available output formats:")
                    for i, format in enumerate(available_formats, start=1):
                        print(f"{i}. {format}")
                    format_choice = input("Choose the output format (enter the number): ")
                    output_format = available_formats[int(format_choice) - 1]
                else:
                    output_format = args.format.lower()
                merge_files(directory, merged_file, output_format)
                print(f"Merged files into: {merged_file[:-3]}.{output_format}")
            elif not args.output:
                merge_choice = input("Do you want to merge the downloaded files into one? (y/n): ").lower() == 'y'
                if merge_choice:
                    available_formats = ["ts", "mp4", "mkv", "avi"]
                    print("Available output formats:")
                    for i, format in enumerate(available_formats, start=1):
                        print(f"{i}. {format}")
                    format_choice = input("Choose the output format (enter the number): ")
                    output_format = available_formats[int(format_choice) - 1]
                    merged_file = f"{directory}_merged.ts"
                    merge_files(directory, merged_file, output_format)
                    print(f"Merged files into: {merged_file[:-3]}.{output_format}")
        else:
            print("Download cancelled.")
    else:
        print("No video files found.")

if __name__ == "__main__":
    main()