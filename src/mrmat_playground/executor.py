import subprocess
import typing

from mrmat_playground import PlaygroundException


def execute(command: str, args: typing.List[str]) -> subprocess.CompletedProcess:
    """
    Execute a command with the provided parameters
    Args:
        command: The command to execute
        args: Parameters to the executable

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
                              encoding='UTF-8')
    except subprocess.CalledProcessError as cpe:
        raise PlaygroundException(status=cpe.returncode, msg=cpe.output) from cpe
