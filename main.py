import os
from typing import Optional

import aiomysql
import disnake
from disnake.ext import commands
from dotenv import load_dotenv


class Loid(commands.Bot):
    class Config:
        def __init__(self, path: str) -> None:
            load_dotenv(dotenv_path=path, override=True)
            self.token = os.getenv("LOID_TOKEN")
            self.webhook = os.getenv("LOID_WEBHOOK")
            self.mysql = {
                "host": os.getenv("LOID_MYSQL_HOST") or "localhost",
                "port": int(os.getenv("LOID_MYSQL_PORT")) or 3306,
                "user": os.getenv("LOID_MYSQL_USER") or "root",
                "password": os.getenv("LOID_MYSQL_PASSWORD"),
                "db": os.getenv("LOID_MYSQL_SCHEMA") or "loid",
                "autocommit": True,
            }


    def __init__(self) -> None:
        super().__init__(
            status=disnake.Status.dnd,
            activity=disnake.Activity(name="도와줘! 로이드맨!", type=disnake.ActivityType.competing),
            command_prefix="?",
            intents=disnake.Intents.all(),
            help_command=None,
        )
        self.config = self.Config("./.env")
    
    def preload(self, path: Optional[str] = "./exts") -> dict:
        files = os.listdir(path)
        path = path.replace("./", "").replace("/", ".")
        result = {"failed_count": 0, "success_count": 0, "total": 0}
        for f in files:
            if not f.endswith(".py"):
                continue
            try:
                self.load_extension(f"{path}.{f[:-3]}")
            except Exception as e:
                result["failed_count"] += 1
                result[f[:-3]] = "Failed"
                print(f"Extension {f[:-3]} was failed to load for:\n{e}")
            else:
                result["success_count"] += 1
                result[f[:-3]] = "Success"
            finally:
                result["total"] += 1
        return result

    def run(self) -> None:
        result = self.preload()
        print(f"There is/are {result['success_count']} (Total is {result['total']}) extension(s) loaded.")
        super().run(self.config.token)

    
bot = Loid()
bot.run()