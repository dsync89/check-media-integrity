import csv

class CSVWriter:
    def __init__(self, filename=None, delimiter='\t'):
        self.filename = filename
        self.delimiter = delimiter

        with open(self.filename, mode='w', newline='') as out_file:
            pass

    def write_line(self, data):
        with open(self.filename, mode='a', newline='') as out_file:
            out_writer = csv.writer(out_file, delimiter=self.delimiter, quotechar='', quoting=csv.QUOTE_NONE, escapechar='\\')
            out_writer.writerow(data)        

    def write(self, data):
        if not self.filename:
            raise ValueError("Filename must be set before saving data.")
        with open(self.filename, mode='a', newline='') as out_file:
            out_writer = csv.writer(out_file, delimiter=self.delimiter, quotechar='', quoting=csv.QUOTE_NONE, escapechar='\\')
            for entry in data:
                out_writer.writerow(list(entry))
