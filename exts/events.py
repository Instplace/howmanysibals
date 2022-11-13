from datetime import datetime, timezone
from typing import Any

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
    
    @commands.Cog.listener("on_member_remove")
    async def _removeMemberData(self, member: disnake.Member) -> None:
        if member.bot:
            return

        o = await aiomysql.connect(**self.bot.config.mysql)
        c = await o.cursor(aiomysql.DictCursor)
        await c.execute(f"DELETE FROM `counts` WHERE `user` = '{member.id}' AND `guild` = '{member.guild.id}'")
        o.close()

    @commands.Cog.listener("on_guild_join")
    async def _autoLeave(self, guild: disnake.Guild) -> None:
        if guild.get_member(541495678371889163) is None:
            return await guild.leave()
        
        o = await aiomysql.connect(**self.bot.config.mysql)
        c = await o.cursor(aiomysql.DictCursor)
        await c.execute(f"INSERT INTO `settings` VALUES ('{guild.id}', '2', '2')")
        o.close()
    
    @commands.Cog.listener("on_guild_remove")
    async def _removeGuildData(self, guild: disnake.Guild) -> None:
        o = await aiomysql.connect(**self.bot.config.mysql)
        c = await o.cursor(aiomysql.DictCursor)
        await c.execute(f"DELETE FROM `counts` WHERE `guild` = '{guild.id}'")
        await c.execute(f"DELETE FROM `settings` WHERE `guild` = '{guild.id}'")
        o.close()
    
    @commands.Cog.listener("on_command_error")
    async def _errorHandler(self, ctx: commands.Context, exc: Any) -> None:
        if isinstance(exc, commands.CommandNotFound):
            return
        elif any([
            isinstance(exc, commands.NotOwner),
            isinstance(exc, commands.MissingPermissions),
            isinstance(exc, commands.MissingAnyRole),
            isinstance(exc, commands.MissingRole),
        ]):
            embed = disnake.Embed(
                title="입력한 명령어는 승인된 유저만 사용할 수 있습니다.",
                description="""
당신에게 실행 권한이 주어지지 않은 명령어입니다.
권한이 있다고 확신한다면 개발자에게 문의하세요.
                """,
                color=0xFF3333,
                timestamp=datetime.now(timezone.utc),
            )
            embed.set_author(name="실행 권한 부족", icon_url=ctx.guild.icon.url)
            embed.set_thumbnail(url=ctx.author.display_avatar.replace(static_format="png", size=2048).url)
            embed.set_footer(text="도와줘요, 로이드맨!", icon_url=self.bot.user.display_avatar.url)
            await ctx.reply(embed=embed)
        elif isinstance(exc, commands.UserInputError):
            embed = disnake.Embed(
                title="필수 입력값이 잘못되었거나, 존재하지 않습니다.",
                description="""
필수로 지정된 입력값이 없거나, 입력한 값이 잘못되었습니다.
명령어 사용법이 익숙하지 않다면 개발자에게 문의하세요.
                """,
                color=0xFF3333,
                timestamp=datetime.now(timezone.utc),
            )
            embed.set_author(name="잘못된 입력값", icon_url=ctx.guild.icon.url)
            embed.set_thumbnail(url=ctx.author.display_avatar.replace(static_format="png", size=2048).url)
            embed.set_footer(text="도와줘요, 로이드맨!", icon_url=self.bot.user.display_avatar.url)
            await ctx.reply(embed=embed)
        else:
            embed = disnake.Embed(
                title="알 수 없는 오류가 발생했습니다.",
                description=f"""
개발자가 의도하지 않은 오류가 발생했습니다.
어련히 알아서 조치할테니 해결될 때까지 기다리세요.
```py
{exc}
```
                """,
                color=0x5555FF,
                timestamp=datetime.now(timezone.utc),
            )
            embed.set_author(name="예기치 못한 오류", icon_url=ctx.guild.icon.url)
            embed.set_thumbnail(url=ctx.author.display_avatar.replace(static_format="png", size=2048).url)
            embed.set_footer(text="도와줘요, 로이드맨!", icon_url=self.bot.user.display_avatar.url)
            await ctx.reply(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Events(bot))