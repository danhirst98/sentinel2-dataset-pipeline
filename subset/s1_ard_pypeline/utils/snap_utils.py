import logging
import platform
import subprocess
from os import path

from packaging import version

from subset.s1_ard_pypeline import get_config


def gpt_path():
    """
    Returns the full path to the gpt executable for this platform and system

    :return: path to the gpt executable
    """
    return path.join(bin_path(), executable_name("gpt"))


def snap_path():
    """
    Returns the full path to the snap64 executable for this platform and system.

    :return: path to the snap executable
    """
    exe = "snap"
    # the snap exe has 64 on the end of it under windows for some reason.
    if platform.system() == "Windows":
        exe = exe + "64"

    return path.join(bin_path(), executable_name(exe))


def config_path():
    """
    returns the full path to the snap config directory
    :return: path to the snap config directory
    """
    return path.join(get_config("Snap", "path"), "etc")


def bin_path():
    """
    Returns the full path to the bin folder on this system.

    Note: This must have been set in the `s1_ard_pypeline.config` already

    :return: full path to the bin directory
    """
    return path.join(get_config("Snap", "path"), "bin")


def executable_name(name):
    """
    Append .exe to the executable name if we are on a windows machine.

    :return: the input name with .exe on the end if required
    """
    if platform.system() == "Windows":
        return name + ".exe"
    else:
        return name


def fetch_snap_module_list():
    """
    Run snap and get it to output a module list for us.

    :return: A list of modules this snap install has.
    """
    output = subprocess.check_output([snap_path(), '--nosplash', '--nogui', '--modules', '--list'], timeout=60)
    # now to parse the output and make sure we have what we need.
    return _parse_snap_module_output(output)


def match_module_lists(actual_list, wanted):
    """
    Validate that a list of modules is at least what we want.

    See also fetch_snap_module_list for how to get the input actual_list.

    :param actual_list: List of modules that are installed in snap.
    :param wanted: List of modules and minimum versions that must exist
    :return: True or False if the actual_list meets the wanted requirements
    """
    actual_dict = _modules_to_dictionary(actual_list)
    match = True
    for expected in wanted:
        actual = actual_dict.get(expected['name'])
        if not actual:
            logging.error(f"expected: {expected} but could not find it.")
            match = False
        else:
            expected_version = version.parse(expected['version'])
            actual_version = version.parse(actual['version'])
            if actual_version < expected_version:
                logging.error(f"expected: {expected} found: {actual}")
                match = False
    return match


def _modules_to_dictionary(modules):
    """
    Map a list of modules in to a dictionary by name.

    :param modules: list of modules to convert
    :return: a dictionary of the input modules by name
    """
    result = {}

    for mod in modules:
        result[mod['name']] = mod

    return result


def _parse_snap_module_output(output):
    """
    Parse the output from snap to extract a list of modules and versions.

    :param output: byte array of stdout from snap.
    :return: a list of module information
    """
    result = []
    for line in output.splitlines(keepends=False):
        # skip the header rows and anything that is blank
        if line.startswith(b'Code Name') or line.startswith(b'------') or line == b'':
            continue

        parts = line.split()
        if len(parts) == 3:
            result.append({
                "name": parts[0].decode("utf-8"),
                "version": parts[1].decode("utf-8"),
                "state": parts[2].decode("utf-8"),
            })
    return result
