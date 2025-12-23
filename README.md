# Progetto Moodle Downloader

A high-performance Python utility designed to archive course videos from **progetto-moodle.it**. This tool automates the extraction of HLS streams and merges them into high-quality MP4 files using asynchronous processing.

## 🚀 Features

* **Automatic Scraping:** Parses Moodle course pages using `BeautifulSoup4` to identify and extract nested Nudgis video iframes.
* **Parallel Processing:** Implements `ThreadPoolExecutor` to handle multiple downloads simultaneously, significantly reducing total archival time.
* **API Reverse Engineering:** Interacts directly with the Nudgis V2 API to resolve media IDs into high-definition `.m3u8` manifests.
* **High-Speed Transfers:** Optimized with `yt-dlp` and `aria2c` integration for multi-connection segment fetching.
* **Automated Muxing:** Utilizes `FFmpeg` to combine discrete video and audio streams into a single, portable `.mp4` container.
* **Organized Storage:** Automatically sorts downloads into directories based on the subject name parsed from the Moodle breadcrumbs.

---

## 🛠 Prerequisites

### System Dependencies
The script calls these utilities via the command line. Ensure they are installed and added to your system's `PATH`:
* [yt-dlp](https://github.com/yt-dlp/yt-dlp)
* [FFmpeg](https://ffmpeg.org/)
* [aria2c](https://aria2.github.io/) (used as the external downloader for maximum speed)

### Python Environment
```bash
pip install beautifulsoup4 requests tqdm python-dotenv
```

## ⚙️ Configuration Guide

The script requires specific authentication tokens to bypass the Moodle and Nudgis (video provider) login screens. These are stored in a `.env` file to keep your credentials out of the source code.

### 1. Create the Environment File
Create a file named `.env` in the same directory as the script and paste the following template:

```env
# Moodle Authentication
MOODLE_SESSION=your_session_id_here

# Nudgis (Video API) Authentication
CSRFTOKEN=your_csrf_token_here
MSESSIONID=your_msession_id_here
SERVERID=your_server_id_here
```

### 2. How to Retrieve Cookies

To get these values, follow these steps in your browser (Chrome, Firefox, or Edge):

#### 1. Login: Go to progetto-mood.it and log in to your account.

#### 2. Open DevTools: Press F12 or Right-Click > Inspect and go to the Network tab.

#### 3. Find the Moodle Session: * Refresh the page.
- Click on the main request (usually view.php or the domain name).
- Look under Headers -> Request Cookies.
- Copy the value of MoodleSession.

#### 4. Find Nudgis Tokens:
- Open a course video.
- In the Network tab, search for modes.
- Click on the API request to nudgis.progetto-mood.it/api/v2/medias/modes/.
- Look at the Cookie section in the request headers to find csrftoken, mssessionid, and SERVERID.

### 🛠️ Script Constants

You can fine-tune the behavior of the downloader by modifying the following variables at the top of the script. These values control the folder structure and the speed of the archival process.

| Constant | Data Type | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `MAX_SIMULTANEOUS_DOWNLOADS` | `int` | `3` | Limits how many videos are processed in parallel via `ThreadPoolExecutor`. |
| `DOWNLOAD_DIR` | `str` | `"download"` | The root directory where final, merged `.mp4` files are saved. |
| `TEMP_DIR` | `str` | `"temp"` | The staging area for raw video/audio streams before `ffmpeg` muxing. |

---

### ⚡ Performance Tuning

The script is also hardcoded to use high-speed parameters within the `download_m3u8` function:
* **`-N 32`**: `yt-dlp` uses 32 threads for fragment downloads.
* **`-j 16 -x 16`**: `aria2c` is configured for 16 simultaneous connections and 16 connections per server.
