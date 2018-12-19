import argparse
import csv
import json
import logging
import logging.config
import os
import re

import chardet
from tasks import insert_person_db


def setup_logging(
        default_path='logging.json',
        default_level=logging.INFO,
        env_key='LOG_CFG'
):
    """
    Setup logging configuration
    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


class Producer(object):
    """
    Class that represents the Producer of tasks sent to the broker
    """

    def __init__(self):
        self.logger = logging.getLogger('producer')

    def __get_csv_fullnames_emails(self, filepath: str) -> tuple:
        """
        Generator function that reads a CSV file and returns fullname and email if found.

        - Email is checked against a regex and 254 char limit (http://www.rfc-editor.org/errata_search.php?rfc=3696&eid=1690)
        - Fullname is the first value in a row that doesnt match the email regex and is under 256 chars
          (should be enough for a fullname).

        ** If one of both is not found then the row is filtered out.
        :param filepath: abs path of CSV location
        :return: tuple (fullname, email)
        """

        try:
            # Guess the encoding first
            rawdata = open(filepath, "rb").read(1024)
            result = chardet.detect(rawdata)
            self.logger.info(f'Encoding detected for {filepath}: {result}')
            with open(filepath, encoding=result['encoding'], newline='', mode='r') as f:
                try:
                    # Sniff the file to guess the dialect (separator, newline, etc)
                    dialect = csv.Sniffer().sniff(f.readline())  # TODO check that the line is not too big
                    # Reset the position of reading
                    f.seek(0)

                    reader = csv.reader(f, dialect=dialect)

                    for row in reader:
                        fullname = None
                        email = None

                        for val in row:
                            val = val.strip()
                            if email is None and re.match(r"[^@]+@[^@]+\.[^@]+", val) and len(val) <= 254:
                                self.logger.debug(f'Found email: {val}')
                                email = val
                            elif fullname is None and len(val) <= 256:  # Check the length of fullname
                                self.logger.debug(f'Found fullname: {val}')
                                fullname = val

                            if fullname is not None and email is not None:
                                yield fullname, email
                                break  # We have found both
                except csv.Error:  # File appears not to be in CSV format; move along
                    self.logger.exception(f'Generic error reading the CSV file: {filepath}')

        except UnicodeDecodeError:
            self.logger.exception(msg='')
        except FileNotFoundError:
            self.logger.exception('CSV file was not found')

    def process_csv(self, path):
        """
        Reads an arbitrary CSV file and sends tasks to a worker process that inserts (fullname, email) into
        a database table if found.
        :return:
        """
        count = 0
        for count, (fullname, email) in enumerate(self.__get_csv_fullnames_emails(path), start=1):
            insert_person_db.apply_async(kwargs={'fullname': fullname, 'email': email})
            self.logger.info(f'Task sent to broker: FULLNAME:{fullname} - EMAIL: {email}')
        if count == 0:
            self.logger.info(f'No fullnames/emails found in {path}')


if __name__ == '__main__':
    setup_logging()
    parser = argparse.ArgumentParser(
        description='Reads an arbitrary CSV file from the filesystem and sends tasks to a worker process that inserts (fullname, email) \
        into a database table if found.')
    parser.add_argument('-p', '--path', type=str, help='path of the CSV file to process')

    args = parser.parse_args()

    p = Producer()
    p.process_csv(args.path)
