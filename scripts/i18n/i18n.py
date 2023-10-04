import gettext
import getopt
import os
import sys
import subprocess
import tempfile

from typing import Optional


OK = 0


class I18n(object):
    def __init__(self) -> None:
        self.app_dir: str = self.get_app_dir()
        self.languages: list[str] = ['zh']

    @staticmethod
    def _prepare_check(*commands: list[str]) -> None:
        for command in commands:
            try:
                result = subprocess.run(
                    ['which', command], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )
                has_command = result.returncode == OK
            except subprocess.CalledProcessError:
                has_command = False
            if not has_command:
                err_msg = f'Commands [{commands}] do not exist，' \
                          f'Install these commands and run them again.'
                raise EnvironmentError(err_msg)

    @staticmethod
    def get_app_dir() -> str:
        project_dir: str = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )
        return os.path.join(project_dir, 'apps')

    def _collect_python_file(self) -> list[str]:
        python_files: list[str] = []
        for root, dirs, files in os.walk(self.app_dir):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        return python_files

    @staticmethod
    def _execute_commands(commands: list[str], encoding: str = 'utf-8') -> tuple:
        try:
            p = subprocess.run(commands, capture_output=True, close_fds=os.name != "nt")
        except OSError as err:
            raise OSError(f'Command execution failure: {err}')
        return (
            p.stdout.decode(encoding),
            p.stderr.decode(encoding, errors="replace"), p.returncode,
        )

    def generate_i18n(self) -> None:
        self._prepare_check('xgettext', 'msguniq', 'msgmerge')
        print('Start generating internationalized translated text files')

        python_files = self._collect_python_file()
        with tempfile.NamedTemporaryFile(mode="w+") as writer:
            writer.write('\n'.join(python_files))
            writer.flush()
            domain = "behemoth"
            for language in self.languages:
                output_dir = os.path.join(self.app_dir, 'locales', language, 'LC_MESSAGES')
                os.makedirs(output_dir, exist_ok=True)
                x_gettext_commands = [
                    'xgettext', '-d', domain, '--language=Python', '--keyword=gettext',
                    '--keyword=_', f'--output={os.path.join(output_dir, f"{domain}.po")}',
                    '--from-code=UTF-8', '--add-comments=Translators', '--package-name=v0.1',
                    '--msgid-bugs-address=weidong.jiang@fit2cloud.com', '--no-location',
                    '--copyright-holder='
                ]
                x_gettext_commands.extend(['--files-from', writer.name])
                self._execute_commands(x_gettext_commands)

        msg_uniq_commands = [
            'msguniq', '--to-code=utf-8',
            '/Users/jiangweidong/resources/jumpserver_pr/jumpserver/apps/locale/django.pot'
        ]
        msg_merge_commands = [
            'msgmerge', '-q', '--backup=none', '--previous', '--update',
            '/Users/jiangweidong/resources/jumpserver_pr/jumpserver/apps/locale/zh/LC_MESSAGES/django.po',
            '/Users/jiangweidong/resources/jumpserver_pr/jumpserver/apps/locale/django.pot'
        ]

    def compile_i18n(self) -> None:
        # TODO command -> msgfmt messages.po -o messages.mo
        print('开始编译国际化二进制文件')

    def parse_input(self) -> None:
        try:
            opts, __ = getopt.getopt(sys.argv[1:], 'cg', ['compile', 'generate'])
        except getopt.GetoptError as err:
            print(f'输入有误，错误: {err}')
            sys.exit(2)

        for opt, arg in opts:
            if opt in ("-c", "--compile"):
                self.compile_i18n()
            elif opt in ("-g", "--generate"):
                self.generate_i18n()
            else:
                print('输入有误!')

    def run(self) -> None:
        self.parse_input()


client = I18n()
client.run()
