"""Counts the number of lines of code in .py and .ipynb files in a project.

Args:
    choice (str): The type of output to return. Can be "sum", "pandas", or "json".
    root_path (str): The path to the root directory of the project.
    ignore_dirs (list): A list of directories to ignore when counting lines of code.

Returns:
    int, pandas.DataFrame, or dict: Chosen by user, shows amount of code rows.
        
"""
# ^^^^ was written by chatGPT + edited

from subprocess import Popen, PIPE
from sys import argv
import json
import nbformat
import numpy as np
import pandas as pd


VALIDS = ["sum","pandas","json"]

def check_valids(choice:str):
    """
    Checks for invalid choice

    Args:
        choice (str): chosen choice :D

    Raises:
        TypeError: if not a valid choice then return is impossible
    """
    if choice not in VALIDS: # check invalid input
        error_text = f'code_line_counter only takes {VALIDS} arguments! "{choice}" was given.'
        raise TypeError(error_text)


# input pythonCodeString.split("\n")
def count_rows(split_code:list) -> int:
    """_summary_

    Args:
        split_code (list): strings of source code

    Returns:
        int: code row amount
    """
    code_row_count = 0
    comment_toggle = False # for checking docstrings
    for line in split_code:
        try:
            if '"""' in line.strip()[:3]: # for ignoring docstrings
                if comment_toggle is True:
                    comment_toggle = False
                else:
                    comment_toggle = True
            elif comment_toggle or line.strip()[0] =='#':
                pass
            else:
                code_row_count += 1
        except IndexError: # Means an empty row
            pass
    return code_row_count


def count_nb_code_rows(cell:object) ->int:
    """
    Count code rows in a notebook code cell.

    Args:
        cell (object): ``.ipynb`` file's cell 

    Returns:
        int: code row amount
    """
    code_rows_in_nb = 0
    if cell['cell_type'] == 'code':
        code_rows_in_nb += count_rows(cell['source'].split('\n'))
    return code_rows_in_nb


def count_py_code_rows(file:str) ->int:
    """
    Extracts ``.py``-file contents and counts code rows.

    Args:
        file (str): path to ``.py``-file

    Returns:
        int: code row amount
    """
    with open(file, 'r',encoding="utf-8") as file_object:
        contents = file_object.readlines()
    return count_rows(contents)


def count_sum(jupyter_notebook:object)->int:
    """
    Count code rows in a notebook.
    Tool for double layered mapping.

    Args:
        jupyter_notebook (object): notebook object

    Returns:
        int: code row amount
    """
    return sum(map(count_nb_code_rows, jupyter_notebook['cells']))


def get_files(root_path:str) -> list:
    """
    Gets all the files in a git project

    Args:
        root_path (str): path to the git project root file

    Returns:
        list: list of project file paths
    """
    pop_obj = Popen(f'git -C {root_path} ls-files', stdout=PIPE, stderr=PIPE)
    stdout, stderr = pop_obj.communicate()
    del stderr
    files_changed_list = stdout.decode("utf-8").splitlines()
    project_files = [root_path + file for file in files_changed_list]
    return project_files


def filter_files(file_paths:list, ignore_dirs):
    """
    Filters unwanted files and filetypes from list.

    Args:
        file_paths (list): Project filepaths

        ignore_dirs (list or None): Paths to directories to be ignored.

    Returns:
        list: list of remaining file_paths
    """
    # TODO Implement proper file type filter
    ignore_types=["csv","md","txt","pyc"]
    temp = []
    for file in file_paths:
        if file.split('.')[-1] not in ignore_types:
            temp.append(file)
    file_paths = []
    if ignore_dirs is not None:
        for file in temp:
            count_file = True
            for ignore_dir in ignore_dirs:
                if file in ignore_dir:
                    count_file = False
                    continue # aka skip
            if count_file:
                file_paths.append(file)
        return file_paths
    return temp


def make_pandas_df(paths:list, rows:list) ->pd.DataFrame:
    """
    Makes pandas dataframe with filepaths code counts and filetypes.

    Args:
        paths (list): Filepaths

        rows (list): Code row count

    Returns:
        pd.DataFrame: Columns=["LinesOfCode","File","FileType"]
    """
    dataframe = pd.DataFrame()
    dataframe["LinesOfCode"] = rows
    dataframe["File"] = paths
    dataframe["FileType"] = [file.split('.')[-1] for file in paths]
    return dataframe


def get_notebooks(notebook_files:list) -> list:
    """
    Creates a list of  jupyter notebook objects using nbformat

    Args:
        notebook_files (list): ``.ipynb`` filepaths

    Returns:
        list: Jupyter Notebook objects
    """
    versions = np.zeros(len(notebook_files)) + 4
    books = list(map(nbformat.read, notebook_files, versions))
    return books

def get_notebooks(notebook_files:list) -> list:
    """
    Creates a list of  jupyter notebook objects using nbformat

    Args:
        notebook_files (list): ``.ipynb`` filepaths

    Returns:
        list: Jupyter Notebook objects
    """
    versions = np.zeros(len(notebook_files)) + 4
    books = list(map(nbformat.read, notebook_files, versions))
    return books


def sort_python_files(project_files:list) -> tuple:
    """
    Sorts python type files into 2 lists (``.py``,``.ipynb``)

    Args:
        project_files (list): all the filepaths in project

    Returns:
        tuple: (notebook_files, python_files)
    """
    notebook_files = []
    python_files = []
    for file in project_files:
        if ".ipynb" in file:
            notebook_files.append(file)
        elif ".py" in file:
            python_files.append(file)
    return notebook_files, python_files


def code_line_counter(choice:str, root_path = "", ignore_dirs=None):
    """Counts the number of lines of code in .py and .ipynb files in a project.

    Args:
        choice (str): The type of output to return. Can be "sum", "pandas", or "json".

        root_path (str): The path to the root directory of the project.

        ignore_dirs (list): A list of directories to ignore when counting lines of code.

    Returns:
        int, pandas.DataFrame, or dict: Chosen by user, shows amount of code rows.
    """
    # ^^^^ was written by chatGPT + edited


    choice = str(choice).lower()
    check_valids(choice)
    project_files =  get_files(root_path)
    project_files = filter_files(project_files, ignore_dirs)

    nb_files, py_files = sort_python_files(project_files)
    notebooks = get_notebooks(nb_files)

    code_rows_in_nb = list(map(count_sum,notebooks))
    code_rows_in_nb.extend(list(map(count_py_code_rows, py_files)))

    if choice == "sum": # Return sum of all project's python code in .py and .ipynb files
        return sum(code_rows_in_nb)

    if choice == "pandas":
        nb_files.extend(py_files)
        dataframe = make_pandas_df(nb_files, code_rows_in_nb)
        return dataframe

    if choice == "json":
        nb_files.extend(py_files)
        temp = {}
        for i, file in enumerate(nb_files):
            temp[file] = code_rows_in_nb[i]
        row_count_json = json.dumps(temp)
        return row_count_json
    return None

if __name__=='__main__':
    ROOT = "./" # HOX CHANGE WHEN MOVED TO DIFFERNET PROJECT!!!
    if len(argv) > 4 or len(argv) < 2:
        raise TypeError("Takes 1-3 arguments. choice:str, root_path:str, ignore_dirs:list")
    CHOICE = str(argv[1])
    if len(argv) == 2:
        result = code_line_counter(CHOICE, root_path = ROOT)
        print(result)
    elif len(argv) == 3:
        if '/' not in str(argv[2]).replace('\\','/').replace('//','/'): #PATH_TO_ROOT check
            raise TypeError("Second argument must be a path")
        result = code_line_counter(CHOICE, root_path = str(argv[2]))
        print(result)
    elif len(argv) == 4:
        if ',' in argv[3]: # ignore list check
            ignores = str(argv[3]).split(',')
            result = code_line_counter(CHOICE, root_path = str(argv[2]), ignore_dirs = ignores)
            print(result)
        else:
            raise TypeError("Third argument must have a ',' like: first_path,second_path")
