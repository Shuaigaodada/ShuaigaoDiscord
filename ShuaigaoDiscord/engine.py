import os
import re
import sys
import time
import json
import asyncio
import traceback
import validators
import subprocess
from loguru import logger
from typing import List, Dict
from interactions import SlashContext, Message

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
    async def search(query: str, max_results: int = 5) -> List[VideoData]:
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
    async def download(video: VideoData, server: str, user: str) -> str: # return path
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
        
    class playlist:
        @staticmethod
        async def download(message: Message, url: str, server: str, user: str, name: str) -> List[str]:
            # yt-dlp -f bestaudio --external-downloader aria2c -o "指定目录/%(title)s.%(ext)s" [播放列表URL]
            if not validators.url(url):
                logger.error(f"Invalid url: {url}")
                await message.edit(content="提供的 URL 无效，请检查后重试。")
                return []
            
            engine = os.path.abspath(__file__)
            root = os.path.dirname(engine)
            download_path = os.path.join(root, "src", "servers", server, user, name)
            os.makedirs(download_path, exist_ok=True)
            download_path = os.path.join(download_path, "%(title)s.%(ext)s")
            command = [
                "yt-dlp", "-f", "ba",
                "-x", "--audio-format", "mp3",
                "--external-downloader", "aria2c",
                "--external-downloader-args", "-x16 -k1M",
                "--postprocessor-args", "-threads 8",
                "-i", "-o", download_path, url
            ]
            # test: 
            # yt-dlp -f ba -x --audio-format mp3 -i -o "/home/laogao/Project/ShuaigaoDiscord/ShuaigaoDiscord/src/servers/081932/3218952/%(title)s.%(ext)s" https://www.youtube.com/playlist?list=PLTZI-S6ZpPkFTzE-X2JOec-56IWGDSPoj
            start_time = time.perf_counter()
            process = subprocess.Popen(
                command,
                stdout = subprocess.PIPE,
                stderr = subprocess.STDOUT,
                text = True
            )
            pattern = re.compile(r"\[download\] Downloading item (\d+) of (\d+)")
            mp3_pattern = re.compile(r"\[ExtractAudio\] Destination: (.+?\.mp3)")
            exists_pattern = re.compile(r"\[download\] (.+?\.mp3) has already been downloaded")

            output_files = []

            async def handle_output():
                await message.edit(content="开始导入歌单...")
                for line in process.stdout:
                    print(line, end="", flush=True)

                    mp3_match = mp3_pattern.search(line)
                    exists_match = exists_pattern.search(line)
                    match = pattern.search(line)

                    if mp3_match:
                        output_files.append(mp3_match.group(1))
                    if exists_match:
                        output_files.append(exists_match.group(1))
                    if match:
                        current_item, total_items = map(int, match.groups())
                        await Youtube.playlist._progress_update(message, current_item, total_items)
            try:
                await message.edit(content="开始导入")
                await handle_output()
                process.wait()
                await message.edit(content="已导入完成，重新调用 `/playlist` 命令来播放音乐")
                return output_files
            except Exception as error:
                logger.error(error)
                traceback.print_exc()
                await message.edit(content=f"导入过程中发生错误: {error}")
                return []
            finally:
                logger.info(f"Downloaded '{url}' playlist took {time.perf_counter() - start_time:.2f}s")

        @staticmethod
        async def _progress_update(message: Message, current: int, total: int, length: int = 20) -> None:
            progress: int = int((current / total) * length)
            percent_complete: int = int((current / total) * 100)
            progress_bar: str = "🟩" * progress + "⬛" * (length - progress)
            # 更新消息以显示百分比和进度条
            await message.edit(content=f"导入进度：{percent_complete}% ({current}/{total})\n{progress_bar}")
