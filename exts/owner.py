import os

import disnake
from disnake.ext import commands

class Owner(commands.Cog, name="쉬운 관리"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="reload")
    async def _reload(self, ctx: commands.Context) -> None:
        files = os.listdir(path)
        path = path.replace(".", "").replace("/", ".")
        result = {"failed_count": 0, "success_count": 0, "total": 0}
        for f in files:
            if not f.endswith(".py"):
                continue
            try:
                self.bot.reload_extension(f"{path}.{f[:-3]}")
            except Exception as e:
                result["failed_count"] += 1
                result[f[:-3]] = "Failed"
                print(f"Extension {f[:-3]} was failed to load for:\n{e}")
            else:
                result["success_count"] += 1
                result[f[:-3]] = "Success"
            finally:
                result["total"] += 1
        await ctx.reply(f"""
<:congrat:949665168017743922> > 전체 확장에 대해 다시 불러오기 작업을 수행했습니다.
정상적으로 불러온 확장 : {result['success_count']}개
불러오기에 실패한 확장 : {result['failed_count']}개
        """)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Owner(bot))