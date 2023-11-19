import os
import re
import sys
import time
import json
import assets
import asyncio
import traceback
import validators
import subprocess
from loguru import logger
from typing import List, Dict
from interactions import SlashContext, Message

class SearchEngine: pass
class VideoData:
    def __init__(self, title: str = "", url: str = "", description: str = None):
        self.title = title
        self.url = url
        self.description = description
        self.image: List[Dict[str, int]] = None
        self.duration: int | str = None
        self.uploader: str = None
    
    def load_data(self, data: Dict) -> "VideoData":
        self.title = data.get("title", "N/A")
        self.url = data.get("url", "N/A")
        self.description = data.get("description", "N/A")
        self.image = data.get("thumbnails", "N/A")
        self.duration = data.get("duration_string", "N/A")
        self.uploader = data.get("uploader", "N/A")
        return self
    
    async def fill_info(self):
        command = ["yt-dlp", "-J", self.url]
        try:
            result = subprocess.check_output(command).decode()
            data: Dict = json.loads(result)
            if data.get("entries"):
                self.load_data(data.get("entries"))
            else:
                self.load_data(data)
                self.duration = self.duration.split(":")
                self.duration = int(self.duration[0]) * 60 + int(self.duration[1])
            return
        except Exception as e:
            logger.error(e)
            raise e
            
    def check(self) -> bool:
        for attr, value in self.__dict__.items():
            if value is None:
                return True
        return False

    @staticmethod
    def load(data: Dict) -> "VideoData":
        return VideoData().load_data(data)
    
    def __repr__(self):
        return f"<VideoData {self.title} - {self.url}>"
    
    def get(self, key: str) -> str:
        return getattr(self, key)

    def to_dict(self):
        return {
            "title": self.title,
            "url": self.url,
            "description": self.description,
            "image": self.image,
            "duration": self.duration,
            "uploader": self.uploader
        }


class Youtube(SearchEngine):
    @staticmethod
    async def search(query: str, max_results: int = 5) -> List[VideoData]:
        logger.info(f"start searching {query} from {max_results} results.")
        start_time = time.perf_counter()
        command = [
            "yt-dlp",
            "ytsearch{}:{}".format(max_results, query),
            "-J", 
            "--default-search", "ytsearch",
            "--no-playlist", "--no-check-certificate", "--geo-bypass",
            "--flat-playlist", "--skip-download", "--quiet", "--ignore-errors"
        ]
        # https://www.youtube.com/watch?v=fuM1aVCGR8c&list=RDfuM1aVCGR8c&start_radio=1
        try:
            result = subprocess.check_output(command).decode()
            data: Dict = json.loads(result)
            videos: List[Dict] = data.get("entries", [])
            simplified_results: List[VideoData] = [VideoData.load(video) for video in videos]
            return simplified_results
        except Exception as error:
            logger.error(error)
            return []
        finally:
            logger.info(f"Searching for '{query}' took {time.perf_counter() - start_time:.2f}s")

    @staticmethod
    async def download(video: VideoData, server: str, quality: int) -> str: # return path
        if not validators.url(video.url):
            logger.error(f"{video.url} is not a real url")
            return ""
        engine = os.path.abspath(__file__)
        root = os.path.dirname(engine)
        download_path = os.path.join(root, "src", "servers", server, "temp", video.title + ".mp3")
        os.makedirs(os.path.dirname(download_path), exist_ok=True)
        
        if quality != 0:
            command = ["yt-dlp", "-F", video.url]
            try:
                result = subprocess.run(command, stdout=subprocess.PIPE, text=True)
                lines = result.stdout.split('\n')
                audio_formats = []
                for line in lines:
                    if "audio only" in line:
                        fields = line.split()
                        format_code = fields[0]
                        bitrate_str = re.search(r'\d+k', line)
                        bitrate = int(bitrate_str.group()[:-1]) if bitrate_str else 0
                        audio_formats.append((format_code, bitrate))

                audio_formats.sort(key=lambda x: x[1], reverse=True)
                format_code = audio_formats[quality][0] if len(audio_formats) > 1 else audio_formats[0][0]
            except Exception as error:
                logger.error(error)
                return

            
            command = [
                "yt-dlp", "-f", format_code,
                "--external-downloader", "aria2c",
                "-o", download_path, video.url
            ]
        else:
            command = [
                "yt-dlp", "-f", "bestaudio",
                "--external-downloader", "aria2c",
                "-o", download_path, video.url
            ]

        asset = assets.Assets()
        if video.title.strip(".mp3") in os.listdir(asset.server(server).join("temp")):
            return asset.server(server).join("temp", video.title + ".mp3")
        
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
        async def download(message: Message, url: str, server: str) -> List[str]:
            # yt-dlp -f bestaudio --external-downloader aria2c -o "指定目录/%(title)s.%(ext)s" [播放列表URL]
            if not validators.url(url):
                logger.error(f"Invalid url: {url}")
                await message.edit(content="提供的 URL 无效，请检查后重试。")
                return []

            download_path = os.path.join(server, "%(title)s.%(ext)s")
            command = [
                "yt-dlp", "-f", "ba",
                "-x", "--audio-format", "mp3",
                "--external-downloader", "aria2c",
                "--external-downloader-args", "-x16 -k1M",
                "--postprocessor-args", "-threads 8",
                "-i", "-o", download_path, url
            ]
            # test: 
            # yt-dlp -f 'ba' -x --audio-format mp3 -i -o "/home/laogao/Project/ShuaigaoDiscord/ShuaigaoDiscord/src/servers/081932/3218952/%(title)s.%(ext)s" https://www.youtube.com/playlist?list=PLTZI-S6ZpPkFTzE-X2JOec-56IWGDSPoj
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
                await message.edit(content="开始下载列表...")
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
                await message.edit(content="开始下载")
                await handle_output()
                process.wait()
                await message.edit(content="下载完成") # TODO show user next command
                return output_files
            except Exception as error:
                logger.error(error)
                traceback.print_exc()
                await message.edit(content=f"下载过程中发生错误: {error}")
                return []
            finally:
                logger.info(f"Downloaded '{url}' playlist took {time.perf_counter() - start_time:.2f}s")

        @staticmethod
        async def _progress_update(message: Message, current: int, total: int, length: int = 20) -> None:
            progress: int = int((current / total) * length)
            percent_complete: int = int((current / total) * 100)
            progress_bar: str = "🟩" * progress + "⬛" * (length - progress)
            # 更新消息以显示百分比和进度条
            await message.edit(content=f"下载进度：{percent_complete}% ({current}/{total})\n{progress_bar}")

        @staticmethod
        async def Import(url: str, path: str) -> None:
            code = "utf-8"
            logger.info(f"start importing {url}")
            command = [
                "yt-dlp",
                "--flat-playlist",
                "-J",
                url
            ]

            try:
                process = await asyncio.create_subprocess_exec(
                    *command, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                if stderr:
                    raise Exception(stderr.decode(code))
                data: Dict = json.loads(stdout.decode(code))
                videos_list: List[Dict] = data.get("entries", [])
                videos: Dict[str, Dict] = {v.get("title", "N/A"): VideoData.load(v).to_dict() for v in videos_list}
                videos["url"] = url

                with open(path, "w") as file:
                    json.dump(videos, file, ensure_ascii=False, indent=4)
                
                logger.info("import done")
            except subprocess.CalledProcessError as error:
                logger.error(error)
                

