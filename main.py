from bs4 import BeautifulSoup
import re
import requests
import os
import subprocess
from pathlib import Path
from tqdm import tqdm
import time
from concurrent.futures import ThreadPoolExecutor
import shutil
from dotenv import load_dotenv

load_dotenv()

DOWNLOAD_DIR = "download"
TEMP_DIR = "temp"

# Configuration
MAX_SIMULTANEOUS_DOWNLOADS = 3

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def get_media_modes(mediaid):
    headers = {
        'Accept':  '*/*',
        'Referer': 'https://progetto-mood.it/',
        'Cookie': f'csrftoken={os.environ["CSRFTOKEN"]}; mssessionid={os.environ["MSESSIONID"]}; SERVERID136356={os.environ["SERVERID"]}',
    }
    url = f'https://nudgis.progetto-mood.it/api/v2/medias/modes/?oid={mediaid}&html5=webm_ogg_ogv_oga_mp4_m4a_mp3_m3u8&yt=yt&embed=embed'
    response = requests.get(url, headers=headers)
    return response.json()

def extract_video_info(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0',
        'Cookie': f'MoodleSession={os.environ["MOODLE_SESSION"]}',
    }
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        name_element = soup.select_one('.pl-0 > h2:nth-child(1)')
        subject_element = soup.select_one('li.breadcrumb-item:nth-child(4) > a:nth-child(1)')
        
        if not name_element or not subject_element:
            return None

        iframes = soup.find_all('iframe', class_='nudgis-iframe')
        for iframe in iframes:
            src = iframe.get('src')
            match = re.search(r'mediaid=([^&]+)', src)
            if match:
                return (name_element.text.strip(), subject_element.text.strip(), match.group(1))
    except Exception:
        return None
    return None

def download_m3u8(url, temp_path, filename):
    command = [
        "yt-dlp", "-N", "32", "-P", temp_path, "-o", filename,
        "--external-downloader", "aria2c", "--external-downloader-args", "aria2c:-j 16 -x 16",
        url
    ]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def download_media(video_info, media_modes):
    video_name, subject, mediaid = video_info
    
    # Logic change: Create a unique subfolder per download to avoid filename collisions
    specific_temp = os.path.join(TEMP_DIR, mediaid)
    if not os.path.exists(specific_temp):
        os.makedirs(specific_temp)

    base_dir = os.path.join(DOWNLOAD_DIR, subject)
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)

    best_quality = media_modes['names'][0]
    media_url_m3u8 = media_modes[best_quality]['resource']['url']
    audio_url_m3u8 = media_modes['audio']['tracks'][0]['url']

    print(f"[Starting] {video_name}")
    
    # Download using a unique temp path
    download_m3u8(media_url_m3u8, specific_temp, "media.mp4")
    download_m3u8(audio_url_m3u8, specific_temp, "audio.mp3")

    # Join
    output_file = os.path.join(base_dir, f"{video_name}.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", 
        "-i", os.path.join(specific_temp, "media.mp4"), 
        "-i", os.path.join(specific_temp, "audio.mp3"),
        "-c", "copy", "-map", "0:v:0", "-map", "1:a:0", "-shortest", output_file
    ], check=True)

    shutil.rmtree(specific_temp)
    print(f"[Finished] {video_name}")

def process_link(link):
    video_info = extract_video_info(link)
    if video_info:
        # Check if already exists
        if os.path.exists(f"{DOWNLOAD_DIR}/{video_info[1]}/{video_info[0]}.mp4"):
            return f"Skipped: {video_info[0]}"
        
        media_modes = get_media_modes(video_info[2])
        try:
            download_media(video_info, media_modes)
            return f"Success: {video_info[0]}"
        except Exception as e:
            return f"Error: {video_info[0]} - {str(e)}"
    return "Invalid link info"

def get_all_classes():
    # Example course url
    url = "https://progetto-mood.it/course/view.php?id=2"
    headers = {'Cookie': f'MoodleSession={os.environ["MOODLE_SESSION"]}'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    return [link["href"] for link in soup.find_all("a", class_="aalink stretched-link") if "href" in link.attrs]

if __name__ == "__main__":
    all_links = get_all_classes()
    links_to_process = all_links

    print(f"Starting parallel download with {MAX_SIMULTANEOUS_DOWNLOADS} workers...")

    with ThreadPoolExecutor(max_workers=MAX_SIMULTANEOUS_DOWNLOADS) as executor:
        list(tqdm(executor.map(process_link, links_to_process), total=len(links_to_process)))