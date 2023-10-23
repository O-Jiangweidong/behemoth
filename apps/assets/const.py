from gettext import gettext as _

from common.special import Choice


class WorkerCategory(Choice):
    worker = 'worker'


class PlatformCategory(Choice):
    mysql = 'mysql'


class Protocol(Choice):
    ssh = 'ssh'
    mysql = 'mysql'

