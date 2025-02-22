import time

class TimedLogger:
    def __init__(self, UPDATE_MB_INTERVAL, UPDATE_SEC_INTERVAL, logger):
        self.previous_time = 0
        self.previous_size = 0
        self.start_time = 0
        self.UPDATE_MB_INTERVAL = UPDATE_MB_INTERVAL
        self.UPDATE_SEC_INTERVAL = UPDATE_SEC_INTERVAL
        self.logger=logger

    def start(self):
        self.start_time = self.previous_time = time.time()
        return self

    def print_log(self, num_files, num_bad_files, total_file_size, wait_min_processed=None, force=False):
        if wait_min_processed is None:
            wait_min_processed = self.UPDATE_MB_INTERVAL

        if not force and (total_file_size - self.previous_size) < wait_min_processed * (1024 * 1024):
            return
        cur_time = time.time()
        from_previous_delta = cur_time - self.previous_time
        if from_previous_delta > self.UPDATE_SEC_INTERVAL or force:
            self.previous_time = cur_time
            self.previous_size = total_file_size

            from_start_delta = cur_time - self.start_time
            speed_MB = total_file_size / (1024 * 1024 * from_start_delta)
            speed_IS = num_files / from_start_delta
            processed_size_MB = float(total_file_size) / (1024 * 1024)

            self.logger.info(f"Number of bad/processed files: {num_bad_files} / {num_files}, size of processed files: {processed_size_MB:.1f} MB")
            self.logger.info(f"Processing speed: {speed_MB:.1f} MB/s, or {speed_IS:.1f} files/s")
