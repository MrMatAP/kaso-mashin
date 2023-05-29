import pathlib
import subprocess
import typing

from kaso_mashin import PlaygroundException


def execute(command: str,
            args: typing.List[str],
            cwd: typing.Optional[pathlib.Path] = pathlib.Path.cwd()) -> subprocess.CompletedProcess:
    """
    Execute a command with the provided parameters
    Args:
        command: The command to execute
        args: Parameters to the executable
        cwd: Optional path in which to execute the command, defaults to the current process directory

    Returns:
        The completed process output from the subprocess module

    Raises:
        PlaygroundException when the executable cannot be found or tthe executable did not return with a successful
        exit code
    """
    try:
        args.insert(0, str(command))
        return subprocess.run(args=args,
                              capture_output=True,
                              check=True,
                              encoding='UTF-8',
                              cwd=cwd)
    except subprocess.CalledProcessError as cpe:
        raise PlaygroundException(status=cpe.returncode, msg=cpe.output) from cpe
