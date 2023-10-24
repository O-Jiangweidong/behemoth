import os
import hashlib
import random
import string
import json

import aiologger

from typing import Callable, Any

from Crypto.Cipher import AES  # noqa
from Crypto.Util.Padding import pad, unpad # noqa

from aiologger.handlers.files import (
    AsyncTimedRotatingFileHandler, RolloverInterval
)
from aiologger.handlers.streams import AsyncStreamHandler

from aiologger.formatters.base import Formatter

from apps.settings import settings


def get_logger() -> aiologger.Logger:
    # 配置日志
    logger = aiologger.Logger(name='behemoth')
    log_level = settings.APP.LOG_LEVEL
    log_formatter = Formatter('%(asctime)s %(levelname)s %(message)s')
    # 创建文件处理程序
    log_dir = os.path.join(settings.DATA_DIR, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    file_handler = AsyncTimedRotatingFileHandler(
        os.path.join(log_dir, 'app.log'), RolloverInterval.DAYS
    )
    file_handler.level = log_level
    file_handler.formatter = log_formatter
    # 创建屏幕处理程序
    stream_handler = AsyncStreamHandler()
    stream_handler.level = log_level
    stream_handler.formatter = log_formatter
    # 将处理程序添加到根记录器
    logger.add_handler(file_handler)
    logger.add_handler(stream_handler)
    return logger


def singleton(cls) -> Callable:
    instances: dict = {}

    def wrapper(*args, **kwargs) -> object:
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return wrapper


def random_string(
        length: int = 6, upper: bool = True, lower: bool = True
) -> str:
    letters = ''
    if lower:
        letters += string.ascii_lowercase
    if upper:
        letters += string.ascii_uppercase
    return ''.join(random.sample(letters, length))


def calc_file_md5(file_path):
    with open(file_path, 'rb') as file:
        md5_hash = hashlib.md5()
        while chunk := file.read(4096):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()


# 加密函数
def encrypt(plaintext, key):
    cipher = AES.new(key, AES.MODE_CBC)
    ciphertext = cipher.encrypt(pad(plaintext.encode(), AES.block_size))
    return cipher.iv + ciphertext


def decrypt(ciphertext, key):
    iv = ciphertext[:AES.block_size]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(ciphertext[AES.block_size:]), AES.block_size)
    return plaintext.decode()


def encrypt_json_file(file_path: str, content: Any, secret: str) -> None:
    encrypted_data: Any = encrypt(json.dumps(content), secret)

    with open(file_path, 'wb') as encrypted_file:
        encrypted_file.write(encrypted_data)


def decrypt_json_file(file_path: str, secret: str) -> None:
    with open(file_path, 'rb') as encrypted_file:
        encrypted_data = encrypted_file.read()

    decrypted_data = decrypt(encrypted_data, secret)
    data = json.loads(decrypted_data)
    return data
