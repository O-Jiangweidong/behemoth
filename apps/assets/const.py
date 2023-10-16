from gettext import gettext as _

from common.special import Choice


TASK_WORKER = 'task_worker'


class PlatformCategory(Choice):
    mysql = 'mysql'


class Protocol(Choice):
    ssh = 'ssh'
    mysql = 'mysql'

