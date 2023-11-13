import os
import sys
import time
import json
import validators
import subprocess
from loguru import logger
from typing import List, Dict

class SearchEngine: pass
class VideoData:
    def __init__(self, title: str, url: str):
        self.title = title
        self.url = url

    def __repr__(self):
        return f"<VideoData {self.title} - {self.url}>"
    
    def get(self, key: str) -> str:
        return getattr(self, key)


class Youtube(SearchEngine):
    @staticmethod
    def search(query: str, max_results: int = 5) -> List[VideoData]:
        logger.info(f"start searching {query} from {max_results} results.")
        start_time = time.perf_counter()
        command = [
            "yt-dlp",
            "ytsearch{}:{}".format(max_results, query),
            "--dump-json", 
            "--default-search", "ytsearch",
            "--no-playlist", "--no-check-certificate", "--geo-bypass",
            "--flat-playlist", "--skip-download", "--quiet", "--ignore-errors"
        ]
        # https://www.youtube.com/watch?v=fuM1aVCGR8c&list=RDfuM1aVCGR8c&start_radio=1
        try:
            result = subprocess.check_output(command).decode()
            videos: List[Dict] = [json.loads(line) for line in result.splitlines()]
            simplified_results: List[VideoData] = []
            for video in videos:
                simplified_results.append(VideoData(
                    video.get("title", "N/A"),
                    video.get("webpage_url", "N/A")
                ))
            return simplified_results
        except Exception as error:
            logger.error(error)
            return []
        finally:
            logger.info(f"Searching for '{query}' took {time.perf_counter() - start_time:.2f}s")

    @staticmethod
    def download(video: VideoData, server: str, user: str) -> str: # return path
        if not validators.url(video.url):
            logger.error(f"{video.url} is not a real url")
            return ""
        engine = os.path.abspath(__file__)
        root = os.path.dirname(engine)
        download_path = os.path.join(root, "src", "servers", server, user, video.title + ".mp3")
        os.makedirs(os.path.dirname(download_path), exist_ok=True)
        
        
        command = [
            "yt-dlp", "-f", "bestaudio",
            "--external-downloader", "aria2c",
            "-o", download_path, video.url
        ]
        
        start_time = time.perf_counter()
        try:
            sys.path.append(os.path.join(root, "src", "tools"))
            subprocess.check_call(command)
            return download_path
        except subprocess.CalledProcessError as error:
            logger.error(error)
            return ""
        finally:
            logger.info(f"Downloaded '{video.title}' took {time.perf_counter() - start_time:.2f}s")
        
        
