#  MIT License
#
#  Copyright (c) 2022 Mathieu Imfeld
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
#

"""
Declare an abstract base class for command implementations involving a resource
"""

from abc import ABC, abstractmethod

import argparse
from configparser import ConfigParser


class AbstractResourceCommands(ABC):

    """
    Abstract base class useful for abstract resource commands
    """

    @staticmethod
    @abstractmethod
    def list(args: argparse.Namespace, config: ConfigParser) -> int:
        """
        List resources

        Returns:
            An exit code, 0 when successful. Non-zero otherwise
        """
        pass

    @staticmethod
    @abstractmethod
    def get(args: argparse.Namespace, config: ConfigParser) -> int:
        """
        Get an individual resource specified by its id
        Args:
            args: The parsed command line arguments. Requires 'id' to be present
            config: The application configuration

        Returns:
            An exit code, 0 when successful. Non-zero otherwise
        """
        pass

    @staticmethod
    @abstractmethod
    def create(args: argparse.Namespace, config: ConfigParser) -> int:
        """
        Create a resource
        Args:
            args: The parsed command line arguments
            config: The application configuration

        Returns:
            An exit code, 0 when successful. Non-zero otherwise
        """
        pass

    @staticmethod
    @abstractmethod
    def modify(args: argparse.Namespace, config: ConfigParser) -> int:
        """
        Modify a resource
        Args:
            args: The parsed command line arguments. Requires 'id' to be present
            config: The application configuration

        Returns:
            An exit code, 0 when successful. Non-zero otherwise
        """
        pass

    @staticmethod
    @abstractmethod
    def remove(args: argparse.Namespace, config: ConfigParser) -> int:
        """
        Remove a resource
        Args:
            args: The parsed command line arguments. Requires 'id' to be present
            config: The application configuration

        Returns:
            An exit code, 0 when successful. Non-zero otherwise
        """
        pass
