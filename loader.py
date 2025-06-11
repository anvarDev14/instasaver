import os

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from utils.db_api.channel import ChannelDB
from utils.db_api.database import Database
from utils.db_api.lang import LanDB
from data import config
from utils.db_api.users import UserDatabase

bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

lang_db = LanDB(path_to_db=os.path.join("data", "main.db"))
user_db = UserDatabase(path_to_db=os.path.join("data", "users.db"))
channel_db = ChannelDB(path_to_db=os.path.join("data", "channel.db"))
