import subprocess
import json

class FFmpegChecker: 
    @staticmethod
    def check(filename, error_detect='default', threads=0):
        ffmpeg_command = ['ffmpeg', '-v', 'error', '-i', filename, '-f', 'null', '-']

        if error_detect != 'default':
            if error_detect == 'strict':
                custom = '+crccheck+bitstream+buffer+explode'
            else:
                custom = error_detect
            ffmpeg_command.insert(3, '-err_detect')
            ffmpeg_command.insert(4, custom)
        
        if threads > 0: 
            ffmpeg_command.append('-threads')
            ffmpeg_command.append(str(threads))
        
        try:
            result = subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            lines = result.stdout.splitlines()
            json_output = json.dumps({i: line for i, line in enumerate(lines)}, separators=(',', ':'))
            if 'error' in result.stdout.lower():
                raise subprocess.CalledProcessError(result.returncode, ffmpeg_command, output=json_output, stderr=result.stderr)
        except subprocess.CalledProcessError as e:
            raise Exception(e.output)