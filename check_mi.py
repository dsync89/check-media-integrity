#!/usr/local/bin/python3

# Copyright (C) 2024

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
__author__ = "Fabiano Tarlao, D.Sync"
__copyright__ = "Copyright 2018, Fabiano Tarlao, Copyright 2024, D.Sync"
__credits__ = ["Fabiano Tarlao"]
__license__ = "GPL3"
__version__ = "0.9.5"
__maintainer__ = "D.Sync"
__status__ = "Beta"

import logging
from queue import Empty
from multiprocessing import Pool, Queue, Process

import sys
import os
import argparse
import time

# import checkers for different type of files
from zero_checker import ZeroChecker
from ffmpeg_checker import FFmpegChecker
from mediainfo_checker import MediaInfoChecker
from pdf_checker import PDFChecker
from magick_checker import MagickChecker
from pil_checker import PILChecker

from csv_writer import CSVWriter
from timed_logger import TimedLogger

LICENSE = "Copyright (C) 2018 Fabiano Tarlao.\n" \
          "Copyright (C) 2024 D.Sync.\n" \
          "This program comes with ABSOLUTELY NO WARRANTY.\n" \
          "This is free software, and you are welcome to redistribute it under GPLv3 license conditions.\n" \
          "You should have received a copy of the GNU General Public License along with this program.\n" \
          "If not, see <https://www.gnu.org/licenses/>."

UPDATE_SEC_INTERVAL = 5  # sec
UPDATE_MB_INTERVAL = 500  # minimum MBytes of data between output log/messages

# The following extensions includes only the most common ones, you can add other extensions BUT..
# ..BUT, you have to double check Pillow, Imagemagick or FFmpeg to support that format/container
# please in the case I miss important extensions, send a pull request or create an Issue

PIL_EXTENSIONS = ['jpg', 'jpeg', 'jpe', 'png', 'bmp', 'gif', 'pcd', 'tif', 'tiff', 'j2k', 'j2p', 'j2x', 'webp']
PIL_EXTRA_EXTENSIONS = ['eps', 'ico', 'im', 'pcx', 'ppm', 'sgi', 'spider', 'xbm', 'tga']

MAGICK_EXTENSIONS = ['psd', 'xcf']

PDF_EXTENSIONS = ['pdf']

# this ones are managed by libav or ffmpeg
VIDEO_EXTENSIONS = ['avi', 'mp4', 'mov', 'mpeg', 'mpg', 'm2p', 'mkv', '3gp', 'ogg', 'flv', 'f4v', 'f4p', 'f4a', 'f4b']
AUDIO_EXTENSIONS = ['mp3', 'mp2']

MEDIA_EXTENSIONS = []

CONFIG = None

CSV_HEADER = [("check_result", "file_name", "error_message", "file_size[bytes]")]

import textwrap as _textwrap

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class MultilineFormatter(argparse.HelpFormatter):
    def _fill_text(self, text, width, indent):
        text = self._whitespace_matcher.sub(' ', text).strip()
        paragraphs = text.split('|n ')
        multiline_text = ''
        for paragraph in paragraphs:
            formatted_paragraph = _textwrap.fill(paragraph, width, initial_indent=indent,
                                                 subsequent_indent=indent) + '\n\n'
            multiline_text = multiline_text + formatted_paragraph
        return multiline_text


def arg_parser():
    epilog_details = """- single file check ignores options -i,-m,-p,-e,-c,-t|n
    - strict_level: execution speed for level 0 > level 1 > level 2. Level 0 algorithm has low recall 
    and high precision, 1 has higher recall, 2 has the highest recall but could have more false positives|n 
    - with \'err_detect\' option you can provide the 'strict' shortcut or the flags supported by ffmpeg, e.g.:
    crccheck, bitstream, buffer, explode, or their combination, e.g., +buffer+bitstream|n
    - supported image formats/extensions: """ + str(PIL_EXTENSIONS) + """|n
    - supported image EXTRA formats/extensions:""" + str(PIL_EXTRA_EXTENSIONS + MAGICK_EXTENSIONS) + """|n
    - supported audio/video extensions: """ + str(VIDEO_EXTENSIONS + AUDIO_EXTENSIONS) + """|n
    - output CSV file, has the header raw, and one line for each bad file, providing: check status, file name, error message, 
    file size"""

    parser = argparse.ArgumentParser(description='Checks integrity of Media files (Images, Video, Audio).',
                                     epilog=epilog_details, formatter_class=MultilineFormatter)
    parser.add_argument('checkpath', metavar='P', type=str,
                        help='path to the file or folder')
    parser.add_argument('-c', '--csv', metavar='X', type=str,
                        help='save bad files details on csv file %(metavar)s', dest='csv_filename',
                        default=f"{time.strftime('%Y-%m-%d_%H-%M-%S')}.csv")
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('-r', '--recurse', action='store_true', help='recurse subdirs',
                        dest='is_recurse')
    parser.add_argument('-z', '--enable_zero_detect', metavar='Z', type=int,
                        help='detects when files contain a byte sequence of at least Z equal bytes. This case is '
                             'common for most file formats, jpeg too, you need to set high %(metavar)s values for this '
                             'check to make sense',
                        dest='zero_detect', default=0)
    parser.add_argument('-i', '--disable-images', action='store_true', help='ignore image files',
                        dest='is_disable_image')
    parser.add_argument('-m', '--enable-media', action='store_true', help='enable check for audio/video files',
                        dest='is_enable_media')
    parser.add_argument('-p', '--disable-pdf', action='store_true', help='ignore pdf files',
                        dest='is_disable_pdf')
    parser.add_argument('-e', '--disable-extra', action='store_true', help='ignore extra image extensions '
                                                                           '(psd, xcf,. and rare ones)',
                        dest='is_disable_extra')
    parser.add_argument('-x', '--err-detect', metavar='E', type=str,
                        help='execute ffmpeg decoding with a specific err_detect flag %(metavar)s, \'strict\' is '
                             'shortcut for +crccheck+bitstream+buffer+explode',
                        dest='error_detect', default='default')
    parser.add_argument('-l', '--strict_level', metavar='L', type=int,
                        help='uses different apporach for checking images depending on %(metavar)s integer value. '
                             'Accepted values 0,1 (default),2: 0 ImageMagick idenitfy, 1 Pillow library+ImageMagick, '
                             '2 applies both 0+1 checks',
                        dest='strict_level', default=1)
    parser.add_argument('-t', '--threads', metavar='T', type=int,
                        help='number of parallel threads used for speedup, default is one. Single file execution does'
                             'not take advantage of the thread option',
                        dest='threads', default=1)
    parser.add_argument('-T', '--timeout', metavar='K', type=int,
                        help='number of seconds to wait for new performed checks in queue, default is 120 sec, you need'
                             ' to raise the default when working with video files (usually) bigger than few GBytes',
                        dest='timeout', default=120)
    parser.add_argument('-b', '--log-bad-files-only', action='store_true',
                        help='log only bad files',
                        dest='log_bad_files_only')

    parse_out = parser.parse_args()
    parse_out.enable_csv = parse_out.csv_filename is not None
    return parse_out


def setup(configuration):
    global MEDIA_EXTENSIONS, PIL_EXTENSIONS
    enable_extra = not configuration.is_disable_extra
    enable_images = not configuration.is_disable_image
    enable_media = configuration.is_enable_media
    enable_pdf = not configuration.is_disable_pdf

    if enable_extra:
        PIL_EXTENSIONS.extend(PIL_EXTRA_EXTENSIONS)

    if enable_images:
        MEDIA_EXTENSIONS += PIL_EXTENSIONS
        if enable_extra:
            MEDIA_EXTENSIONS += MAGICK_EXTENSIONS

    if enable_pdf:
        MEDIA_EXTENSIONS += PDF_EXTENSIONS

    if enable_media:
        MEDIA_EXTENSIONS += VIDEO_EXTENSIONS + AUDIO_EXTENSIONS

def check_size(filename, zero_exception=True):
    statfile = os.stat(filename)
    filesize = statfile.st_size
    if filesize == 0 and zero_exception:
        raise SyntaxError("Zero size file")
    return filesize

def get_extension(filename):
    file_lowercase = filename.lower()
    return os.path.splitext(file_lowercase)[1][1:]

def is_target_file(filename):
    file_ext = get_extension(filename)
    return file_ext in MEDIA_EXTENSIONS

def check_file(filename, error_detect='default', strict_level=0, zero_detect=0, ffmpeg_threads=0):
    if sys.version_info[0] < 3:
        filename = filename.decode('utf8')

    file_lowercase = filename.lower()
    file_ext = os.path.splitext(file_lowercase)[1][1:]

    file_size = 'NA'

    try:
        file_size = check_size(filename)
        if zero_detect > 0:
            ZeroChecker.check(filename, CONFIG.zero_detect)

        if file_ext in PIL_EXTENSIONS:
            if strict_level in [1, 2]:
                PILChecker.check(filename)
            if strict_level in [0, 2]:
                MagickChecker.identify_check(filename)

        if file_ext in PDF_EXTENSIONS:
            if strict_level in [1, 2]:
                PDFChecker.check(filename)
            if strict_level in [0, 2]:
                MagickChecker.identify_check(filename)

        if file_ext in MAGICK_EXTENSIONS:
            if strict_level in [1, 2]:
                MagickChecker.check(filename)
            if strict_level in [0, 2]:
                MagickChecker.identify_check(filename)

        if file_ext in VIDEO_EXTENSIONS:
            # first check video metadata since this is faster using mediainfo            
            MediaInfoChecker.check(filename)
            logger.debug("Video metadata check OK using mediainfo, next check video stream for corruption using ffmpeg...")

            # then check for any video stream corruption using ffmpeg  
            FFmpegChecker.check(filename, error_detect=error_detect, threads=ffmpeg_threads)

    # except ffmpeg.Error as e:
    #     # print e.stderr
    #     return False, (filename, str(e), file_size)
    except Exception as e:
        # IMHO "Exception" is NOT too broad, io/decode/any problem should be (with details) an image problem
        return False, ("X", filename, str(e), file_size)

    return True, ("O", filename, None, file_size)


def log_check_outcome(check_outcome_detail, is_ok, curr_file_num, total_file_num):
    logger.info(f"File {curr_file_num}/{total_file_num}: [{check_outcome_detail[0]}], file_path: {check_outcome_detail[1]}, detail: {check_outcome_detail[2]}, size[bytes]: {check_outcome_detail[3]}")

def worker(in_queue, out_queue, CONFIG):
    try:
        while True:
            full_filename = in_queue.get(block=True, timeout=2)
            is_success = check_file(full_filename, CONFIG.error_detect, strict_level=CONFIG.strict_level, zero_detect=CONFIG.zero_detect)
            out_queue.put(is_success)
    except Empty:
        logger.debug("Closing parallel worker, the worker has no more tasks to perform")
        return
    except Exception as e:
        logger.error("Parallel worker got unexpected error", str(e))
        sys.exit(1)


def main():
    global CONFIG
    CONFIG = arg_parser()
    setup(CONFIG)
    check_path = CONFIG.checkpath

    # initialize timed logger that print summary at the end of run
    timed_logger = TimedLogger(UPDATE_SEC_INTERVAL, UPDATE_MB_INTERVAL, logger)
    logger.info("==============================================")
    logger.info(f"TASK STARTED ON {time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info("==============================================")    
    timed_logger.start()    

    if CONFIG.log_bad_files_only:
        logger.info("Will only log BAD files only due to -b argument")
    else:
        logger.info("Will log GOOD and BAD files")

    logger.info("----------------------------------------------")
    logger.info(f"Files integrity check for: {check_path}")
    logger.info("----------------------------------------------")
    if os.path.isfile(check_path):
        # manage single file check
        check_result = check_file(check_path, CONFIG.error_detect)
        if not check_result[0]:
            check_outcome_detail = check_result[1]
            log_check_outcome(check_outcome_detail, False, 1, 1)
            sys.exit(1)
        else:
            if not CONFIG.log_bad_files_only:
                log_check_outcome(check_outcome_detail, True, 1, 1)
            logger.info("File", check_path, "is OK")
            sys.exit(0)

    # initialize csv writer only if it is not a single file
    csv_writer = CSVWriter(filename=os.path.join('logs', CONFIG.csv_filename))
    csv_writer.write(CSV_HEADER) # write header            

    # manage folder (searches media files into)

    # initializations
    count = 0
    count_bad = 0
    total_file_size = 0
    result_info = [] # [("file_name", "error_message", "file_size[bytes]")]

    task_queue = Queue()
    out_queue = Queue()
    pre_count = 0

    for root, sub_dirs, files in os.walk(check_path):        
        media_files = []
        for filename in files:
            if is_target_file(filename):
                media_files.append(filename)

        pre_count += len(media_files)

        for filename in media_files:
            full_filename = os.path.join(root, filename)
            task_queue.put(full_filename)

        if not CONFIG.is_recurse:
            break  # we only check the root folder

    logger.info(f"Found {pre_count} files in {check_path}")

    for i in range(CONFIG.threads):
        p = Process(target=worker, args=(task_queue, out_queue, CONFIG))
        p.start()

    # consume the outcome
    try:
        for j in range(pre_count):

            count += 1

            check_result = out_queue.get(block=True, timeout=CONFIG.timeout)
            file_size = check_result[1][3]
            check_outcome_detail = check_result[1]

            if file_size != 'NA':
                total_file_size += file_size
              

            if check_result[0]: # good files
                if not CONFIG.log_bad_files_only:
                    result_info.append(check_outcome_detail)
                    log_check_outcome(check_outcome_detail, True, count, pre_count)

            else:
                count_bad += 1
                result_info.append(check_outcome_detail)
                log_check_outcome(check_outcome_detail, False, count, pre_count)
                # print "RATIO:", count_bad, "/", count

            # visualization logs and stats
            timed_logger.print_log(count, count_bad, total_file_size)
    except Empty as e:
        logger.error("Waiting other results for too much time, perhaps you have to raise the timeout", e.message)

    logger.info("==============================================")
    logger.info(f"TASK COMPLETED ON {time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info("==============================================")
    timed_logger.print_log(count, count_bad, total_file_size, force=True)
    logger.info("==============================================")

    logger.info(f"Saving CSV format, file path: {CONFIG.csv_filename}")
    csv_writer.write(result_info)

    logger.info("----------------------------------------------")
    logger.info("File Statistics")
    logger.info("----------------------------------------------")    
    logger.info(f"Total Files: {count:>5}")
    logger.info(f"Good Files:  {count - count_bad:>5}")
    logger.info(f"Bad Files:   {count_bad:>5}")
    logger.info("----------------------------------------------")

if __name__ == "__main__":
    main()
