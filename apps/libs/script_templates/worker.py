import argparse
import os

from typing import Optional
from argparse import Namespace


class BaseScript(object):
    def __init__(self) -> None:
        self._commands: list = []
        self._access_key: Optional[str] = None
        self._secret_id: Optional[str] = None
        self._worker_id: Optional[str] = None
        self._task_id: Optional[str] = None
        self._commands_path: Optional[str] = None

    async def _process_cmd_line_args(self):
        parser = argparse.ArgumentParser(description='Async Command Line Argument Parsing')
        parser.add_argument('-v', '--verbose', help='No help')
        parser.add_argument(
            '-s', '--credential', help='Interacting credential with JumpServer'
        )
        parser.add_argument(
            '-c', '--commands_path', help='Command collection path for script execution'
        )
        parser.add_argument(
            '-w', '--worker_id', help='Identification of the working machine executing the script'
        )
        parser.add_argument(
            '-t', '--task_id', help='Task ID for executing this script'
        )

        args: Namespace = parser.parse_args()
        creds: list = str(args.credential).split('/')
        if len(creds) != 2:
            raise Exception('Incorrect credential parameter [credential]')
        if not os.path.exists(args.commands_path):
            raise Exception('Command collection file does not exist [commands_path]')
        if not args.worker_id:
            raise Exception('The working machine ID cannot be empty [worker_id]')
        if not args.task_id:
            raise Exception('Task ID cannot be empty [task_id]')

        self._access_key, self._secret_id = creds
        self._commands_path = args.commands_path
        self._worker_id = args.worker_id
        self._task_id = args.task_id

    async def run(self):
        try:
            await self._process_cmd_line_args()
        except Exception as error:
            print(f'Failed to execute script: {error}')
