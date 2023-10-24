import argparse
import asyncio
import os
import json

from typing import Optional
from argparse import Namespace

from Crypto.Cipher import AES  # noqa
from Crypto.Util.Padding import pad, unpad # noqa


class WorkerScript(object):
    def __init__(self) -> None:
        self._commands: list = []
        self._token: Optional[str] = None
        self._worker_id: Optional[str] = None
        self._task_id: Optional[str] = None
        self._commands_path: Optional[str] = None

    async def _process_cmd_line_args(self):
        parser = argparse.ArgumentParser(description='Async Command Line Argument Parsing')
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
        parser.add_argument(
            '-k', '--encryption_key', help='Key used to decrypt command collection file'
        )

        args: Namespace = parser.parse_args()
        if args.credential:
            raise Exception('Credential cannot be empty [credential]')
        if not os.path.exists(args.commands_path):
            raise Exception('Command collection file does not exist [commands_path]')
        if not args.worker_id:
            raise Exception('The working machine ID cannot be empty [worker_id]')
        if not args.task_id:
            raise Exception('Task ID cannot be empty [task_id]')
        if not args.encryption_key:
            raise Exception('Encryption_key cannot be empty [encryption_key]')

        self._token = args.credential
        self._commands_path = args.commands_path
        self._encryption_key = args.encryption_key
        self._worker_id = args.worker_id
        self._task_id = args.task_id

        await self.__decrypt_commands()

    async def __decrypt_commands(self) -> None:
        with open(self._commands_path, 'wb') as file:
            ciphertext = file.read()
        iv = ciphertext[:AES.block_size]
        cipher = AES.new(self._encryption_key, AES.MODE_CBC, iv)
        plaintext = unpad(cipher.decrypt(ciphertext[AES.block_size:]), AES.block_size)
        self._commands = json.loads(plaintext.decode())['commands']

    async def _run(self):
        pass

    async def run(self):
        try:
            await self._process_cmd_line_args()
            await self._run()
        except Exception as error:
            print(f'Failed to execute script: {error}')


if __name__ == '__main__':
    asyncio.run(WorkerScript().run())
