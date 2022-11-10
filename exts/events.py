import disnake
from disnake.ext import commands

class Events(commands.Cog, name="기타 이벤트 탐지기"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener("on_ready")
    async def _ready(self) -> None:
        print(self.bot.user)
        print(self.bot.user.id)
        print("Loid is ready to count.")
    

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Events(bot))