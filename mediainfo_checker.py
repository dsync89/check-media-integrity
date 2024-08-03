import subprocess
import json
import re

class MediaInfoChecker:
    @staticmethod
    def parse_duration(duration_str):
        """
        Parses a duration string and returns the duration in milliseconds.
        Handles formats like '2661.959000000' and '7 min 24 s'.
        """
        if isinstance(duration_str, (int, float)):
            return float(duration_str) * 1000

        # Match numerical format
        try:
            return float(duration_str) * 1000
        except ValueError:
            pass
        
        # Match textual format (e.g., '7 min 24 s')
        pattern = re.compile(r'((?P<minutes>\d+)\s*min)?\s*((?P<seconds>\d+)\s*s)?')
        match = pattern.match(duration_str.strip())
        if match:
            minutes = int(match.group('minutes')) if match.group('minutes') else 0
            seconds = int(match.group('seconds')) if match.group('seconds') else 0
            total_seconds = (minutes * 60) + seconds
            return total_seconds * 1000

        raise ValueError(f"Invalid duration format: {duration_str}")

    @staticmethod
    def check(filename):
        mediainfo_command = ['mediainfo', '--Output=JSON', filename]
        
        try:
            result = subprocess.run(mediainfo_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, mediainfo_command, output=result.stdout, stderr=result.stderr)
            
            mediainfo_output = json.loads(result.stdout)
            
            # Check for common signs of corruption
            video_tracks = [track for track in mediainfo_output.get('media', {}).get('track', []) if track.get('@type') == 'Video']
            audio_tracks = [track for track in mediainfo_output.get('media', {}).get('track', []) if track.get('@type') == 'Audio']
            
            if not video_tracks:
                raise Exception("No video stream found")
            
            if not audio_tracks:
                raise Exception("No audio stream found")
            
            # Example of checking for unusual duration (less than 1 second)
            duration_str = video_tracks[0].get('Duration', '0')
            try:
                duration = MediaInfoChecker.parse_duration(duration_str)
            except ValueError as e:
                raise Exception(str(e))
            
            if duration < 1000:  # Duration is in milliseconds
                raise Exception("Unusually short duration")
            
            return mediainfo_output
        
        except subprocess.CalledProcessError as e:
            raise Exception(f"MediaInfo command failed: {e.stderr}")
        except json.JSONDecodeError:
            raise Exception("Failed to parse MediaInfo output")
        except Exception as e:
            raise Exception(f"Corruption detected: {str(e)}")