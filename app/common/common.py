import os
import time


def delete_file(file_path):

    try:
        os.remove(file_path)
    except:
        pass


def get_timestamp():

    return int(time.time())
