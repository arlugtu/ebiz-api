import os


def delete_file(file_path):

    try:
        os.remove(file_path)
    except:
        pass