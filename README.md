# 🖥️ Download Organizer Automation

A Python script that automatically organizes your **Downloads** folder by sorting files into categorized subfolders.

## 🚀 Features
- **Automatically moves files** to respective folders based on their types.
- **Supported categories:**
  - 📸 **Images** (`.jpg`, `.png`, `.gif`, etc.)
  - 🎥 **Videos** (`.mp4`, `.avi`, `.mkv`, etc.)
  - 🎵 **Music** (`.mp3`, `.wav`, `.flac`, etc.)
  - 📂 **Archives** (`.zip`, `.rar`, `.7z`, etc.)
  - 📄 **Documents** (`.pdf`, `.docx`, `.txt`, etc.)
  - 🖥️ **Applications** (`.exe`, `.dmg`, `.apk`, etc.)
- **Customizable:** Modify or add new categories as per your need.
- **Runs on startup** (Optional setup for automation).

## 🛠 Installation
```sh
git clone https://github.com/Caramelizeed/DownloadOrganizer.git
cd DownloadOrganizer
pip install -r requirements.txt
```

## ▶️ Usage
```sh
python organizer.py
```
The script will automatically scan and sort the files in your **Downloads** folder.

## ⚙️ Customization
Modify `FILE_TYPES` dictionary in `organizer.py` to add new categories or extensions.

## 📜 License
This project is open-source and available under the MIT License.
