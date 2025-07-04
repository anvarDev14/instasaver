import logging
import os

from environs import Env

# Logging sozlamasi
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# environs kutubxonasidan foydalanish
env = Env()
env.read_env()

# .env fayl ichidan ma'lumotlarni o'qiymiz
BOT_TOKEN = env.str("BOT_TOKEN")
ADMINS = env.list("ADMINS", subcast=int, default=[])
IP = env.str("ip", default="localhost")

def update_env_admins(admins: list):
    """ADMINS ro'yxatini .env faylida yangilash."""
    try:
        env_path = ".env"
        if not os.path.exists(env_path):
            raise FileNotFoundError(".env file not found")

        with open(env_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        found = False
        with open(env_path, "w", encoding="utf-8") as file:
            for line in lines:
                if line.strip().startswith("ADMINS="):
                    file.write(f"ADMINS={','.join(map(str, admins))}\n")
                    found = True
                else:
                    file.write(line)
            if not found:
                file.write(f"ADMINS={','.join(map(str, admins))}\n")

        # Config'ni qayta yuklash
        global ADMINS
        env.read_env(override=True)
        ADMINS = env.list("ADMINS", subcast=int, default=[])
        logger.info(f".env updated with ADMINS: {ADMINS}")
    except FileNotFoundError:
        logger.error("Error: .env file not found")
        raise
    except PermissionError:
        logger.error("Error: No permission to write to .env file")
        raise
    except Exception as e:
        logger.error(f"Error updating .env file: {e}")
        raise

# Ma'lumotlarni konsolda chiqarish (tekshirish uchun)
logger.info(f"BOT_TOKEN: {BOT_TOKEN}")
logger.info(f"ADMINS: {ADMINS}")
logger.info(f"IP: {IP}")