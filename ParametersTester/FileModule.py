from Config import Filepaths
import os


def init_folders():
    create_folder(Filepaths.RESULTS_FOLDER)
    create_folder(Filepaths.CNFS_FOLDER)
    create_folder(Filepaths.SOLVERS_FOLDER)


def file_exist(file_path):
    return os.path.exists(file_path)


def solver_exist(solver_name):
    return os.path.exists(Filepaths.SOLVERS_FOLDER + '/' + solver_name)


def get_solver_file_path(solver_name):
    return Filepaths.SOLVERS_FOLDER + '/' + solver_name


def get_cnf_file_path():
    file_paths = list()
    data_list = os.walk(Filepaths.CNFS_FOLDER)
    for root, dirs, files in data_list:
        for file_name in files:
            file_paths.append('.'+root[1:]+'/'+file_name)
    return file_paths


def get_file_name(file_path):
    file_name = ''
    for ch in reversed(file_path):
        if ch != '/':
            file_name = ch + file_name
        else:
            return file_name


def create_file(file_path, data):
    file = open(file_path, 'w')
    file.write(data)
    file.close()


def create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)


def read_file(file_path):
    if os.path.exists(file_path):
        file = open(file_path, 'r')
        data = file.read()
        file.close()
        return data
    else:
        raise RuntimeError('FileModule.read_file: file doesn\'t exist.')


def get_solvers_names():
    file_paths = list()
    data_list = os.walk(Filepaths.SOLVERS_FOLDER)
    for root, dirs, files in data_list:
        for file_name in files:
            file_paths.append(file_name)
    return file_paths