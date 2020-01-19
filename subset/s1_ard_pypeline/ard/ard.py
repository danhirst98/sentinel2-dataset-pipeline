import gzip
import logging
import os
import platform
import shutil
import subprocess
from asynchronousfilereader import AsynchronousFileReader
from datetime import datetime
from zipfile import ZipFile

"""
This contains the generic steps of a processing pipeline.

How to run a snap graph, remove a file, etc.
"""


class ProcessError(Exception):
    """
    An error type for problems with processing the data.
    """
    pass


def process_chain(process, name):
    """
    Execute a series of processing steps.

    :param process: The list of things to process. if any return False processing will stop.
    :param name: The name of this process. Used for making the logging clearer.
    :return: Nothing.
    """

    # flatten the process list first. It is very easy to end up with lists in the process list when building it up.
    # To make things more user friendly we flatten the list out depth first.
    flattened = flatten_list(process)

    logging.warning(f"Processing {name} started.")
    start_time = datetime.now()
    for i, step in enumerate(flattened):
        logging.warning(f"Processing step {i + 1} of {len(flattened)}")
        step_start_time = datetime.now()
        try:
            step()
        except ProcessError as e:
            step_stop_time = datetime.now()
            logging.error(
                f"Processing failed on step {i + 1} of {len(flattened)} after {step_stop_time - step_start_time} {e}"
            )
            raise ProcessError(f"Could not process chain {name}", e)
        step_stop_time = datetime.now()
        logging.warning(f"completed step {i + 1} in {step_stop_time - step_start_time}")

    logging.warning(f"Processing {name} ended. Duration: {datetime.now() - start_time}")


def flatten_list(to_flatten):
    """
    Recursively flatten a list.
    Note the order preservation.
    e.g: [a, [b, [c], d], e] => [a, b, c, d, e]

    :param to_flatten: input list to flatten
    :return: flattened list
    """

    result = []
    for entry in to_flatten:
        if entry:
            if isinstance(entry, list):
                result = result + flatten_list(entry)
            else:
                result.append(entry)
    return result


def graph(name):
    """
    Graph names should be in the graph folder and end with .xml. This will make sure.

    Note: If you are using sub folders of the graph folder it is up to you to correctly handle the directory separator

    :param name: name of the graph
    :return: the name of the graph in the folder with .xml on the end.
    """
    if not name.endswith(".xml"):
        name = name + ".xml"

    # if it already starts with graphs take it off and add it back on to make sure
    # we get the right separator for this platform.
    if name.startswith("graphs"):
        name = name[7:]

    return os.path.join("graphs", name)


def gpt(graph_path, args):
    """
    Run the graph processing tool in snap with the provided graph and arguments.

    The args will be processed to the required format for snap. Do not include the -P on the front

    :param graph_path: path to the snap graph to process.
    :param args: a dictionary of arguments to pass to snap.
    :return: None
    """
    logging.info(f"starting graph {graph_path}")
    command = [graph_path]

    for key, value in args.items():
        command.append(f"-P{key}={value}")

    _run_snap_command(command)


def delete_file(file):
    """
    Remove a file from the file system.

    :param file: the path to the file to delete.
    :return: None
    """
    logging.info(f"deleting {file}")
    try:
        os.remove(file)
    except FileNotFoundError as e:
        logging.critical(e)
        raise ProcessError(f"File {file} could not be found")


def delete_dir(directory):
    """
    Remove a folder from the file system.

    :param directory: the path to the folder to delete.
    :return: None
    """
    logging.info(f"deleting {directory}")
    try:
        shutil.rmtree(directory)
    except FileNotFoundError as e:
        logging.critical(e)
        raise ProcessError(f"Directory {directory} could not be found")


def delete_dim(name):
    """
    Delete a dim product from the disk. This will remove both the .dim and .data folders.

    :param name: name of the dim file to remove
    :return: None
    """
    if name.endswith(".dim"):
        name = name[:-4]
    elif name.endswith(".data"):
        name = name[:-5]

    delete_file(name + ".dim")
    delete_dir(name + ".data")
    return True


def unzip_product(file, destination):
    """
    Unzip the target file using the python unzip utility.

    If the expected target product already exists it will skip unzipping the file again.

    :param file: the target file to unzip
    :param destination: where the file should be unzipped
    :return: None
    """
    product_id = os.path.basename(file)
    if product_id.endswith(".zip"):
        product_id = product_id[:-4] + ".SAFE"

    expected = os.path.join(destination, product_id)
    if os.path.exists(expected) and os.path.isdir(expected):
        logging.warning(f"Skipping unzip of {file} as it already appears to be in {destination}.")
        logging.warning(f"If this is incorrect manually remove directory {expected}")
    else:
        logging.info(f"Unzipping {file} to {destination}")
        with ZipFile(file, 'r') as zipObj:
            zipObj.extractall(path=destination)

    return True


def convert_to_tif(source, target):
    """
    A common specialisation of the gpt call to convert an input to GeoTIFF.

    :param source: source file path to convert
    :param target: target file path.
    :return: None
    """

    _run_snap_command(["Write", f"-Pfile={target}", "-PformatName=GeoTIFF", f"-Ssource={source}"])


def gzip_file(source, target):
    """
    Gzip a file

    :param source: path to the file to gzip
    :param target: path to put the results
    :return: None
    """
    try:
        logging.info(f"GZip compressing {source} to {target}")
        with open(source, 'rb') as f_in:
            with gzip.open(target, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    except FileNotFoundError as e:
        logging.critical(e)
        raise ProcessError(f"File {source} could not be found")


def _run_snap_command(command):
    """
    Run a snap command. Internal use.

    :param command: the list of arguments to pass to snap
    :return: None
    """

    # if we need to prepend the snap executable
    full_command = [r"C:\Program Files\snap\bin\gpt.exe"] + command

    '''
    if command[0] != snap_utils.gpt_path():
        full_command = [str(snap_utils.gpt_path())] + command
    else:
        full_command = command
    '''
    # on linux there is a warning message printed by snap if this environment variable is not set.
    base_env = os.environ.copy()
    if "LD_LIBRARY_PATH" not in base_env and platform.system() != "Windows":
        base_env["LD_LIBRARY_PATH"] = "."

    logging.debug(f"running {full_command}")

    process = subprocess.Popen(full_command, env=base_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    snap_logger_out = logging.getLogger("snap_stdout")
    snap_logger_err = logging.getLogger("snap_stderr")
    std_out_reader = AsynchronousFileReader(process.stdout)
    std_err_reader = AsynchronousFileReader(process.stderr)

    def pass_logging():
        while not std_out_reader.queue.empty():
            line = std_out_reader.queue.get().decode()
            snap_logger_out.info(line.rstrip('\n'))
        while not std_err_reader.queue.empty():
            line = std_err_reader.queue.get().decode()
            snap_logger_err.info("stderr:" + line.rstrip('\n'))

    while process.poll() is None:
        pass_logging()

    std_out_reader.join()
    std_err_reader.join()

    if process.returncode != 0:
        raise ProcessError("Snap returned non zero exit status")
