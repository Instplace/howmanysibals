import asyncio
import re
from typing import Any, List, Optional

import aiohttp
import aiomysql
import disnake
from disnake.ext import commands

class Counter(commands.Cog, name="욕설 감지기"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.mode = 2
    
    async def find(self, content: str) -> Optional[List[str]]:
        if content.startswith("https://") or content.startswith("http://"):
            return
        
        if self.mode < 1:
            return

        content = content.lower()
        if self.mode >= 2:
            exp = re.compile(r"[^a-zA-Zㄱ-ㅎㅏ-ㅣ가-힣]")
            removes = exp.findall(content)
            async for rem in self.async_list(removes):
                content = content.replace(rem, "")
        async for word in self.async_list(self.words):
            async for detection in self.async_list(self.words[word]):
                if detection in content:
                    return [word, detection]
                if self.mode >= 3:
                    w = re.compile(r"[a-zA-Zㄱ-ㅎㅏ-ㅣ가-힣]".join(detection))
                    result = w.findall(content)
                    if len(result) != 0:
                        return [word, detection]
        return None

    async def async_list(self, values: list) -> Any:
        for value in values:
            yield value
            await asyncio.sleep(0)
    
    async def cog_load(self) -> None:
        await self.prepare()

    async def prepare(self) -> None:
        await self.bot.wait_until_ready()
        self.words = {} # {"ssibal": ["ssiba1", "sslbal"]...}
        o = await aiomysql.connect(**self.bot.config.mysql)
        c = await o.cursor(aiomysql.DictCursor)
        await c.execute("SELECT * FROM `detects`")
        rows = await c.fetchall()
        registered = 0
        category = 0
        async for row in self.async_list(rows):
            if row["word"] not in self.words:
                self.words[row["word"]] = [row["detection"]]
                category += 1
            else:
                self.words[row["word"]].append(row["detection"])
            registered += 1
        async with aiohttp.ClientSession() as cs:
            webhook = disnake.Webhook.from_url(self.bot.config.webhook, session=cs, bot_token=self.bot.config.token)
            await webhook.send(f"Preparing: {category} categories and total {registered} words are registered.", username="로이드 포저", avatar_url=self.bot.user.display_avatar.url)
        o.close()

    @commands.Cog.listener("on_message")
    async def _detectWords(self, msg: disnake.Message) -> None:
        if msg.author.bot:
            return
        
        if msg.channel.type == disnake.ChannelType.private:
            return
        
        if msg.content.startswith("?word"):
            return

        result = await self.find(msg.clean_content)
        if not result:
            return
        
        async with aiohttp.ClientSession() as cs:
            webhook = disnake.Webhook.from_url(self.bot.config.webhook, session=cs, bot_token=self.bot.config.token)
            await webhook.send(f"""
Just found STRIKE from message.
Content : {msg.content}
Category : {result[0]}
Found : {result[1]}
            """, username="로이드 포저", avatar_url=self.bot.user.display_avatar.url)
        o = await aiomysql.connect(**self.bot.config.mysql)
        c = await o.cursor(aiomysql.DictCursor)
        await c.execute(f"INSERT INTO `counts` VALUES ('{result[0]}', '{msg.guild.id}', '{msg.author.id}')")
        o.close()
        await msg.channel.send(f"""
🌟 > {msg.author.mention}님이 카운트를 추가합니다!
감지된 스트라이크 : {result[0]}
        """)
    
    @commands.Cog.listener("on_member_remove")
    async def _removeData(self, member: disnake.Member) -> None:
        if member.bot:
            return

        o = await aiomysql.connect(**self.bot.config.mysql)
        c = await o.cursor(aiomysql.DictCursor)
        await c.execute(f"DELETE FROM `counts` WHERE `user` = '{member.id}' AND `guild` = '{member.guild.id}'")
        o.close()

    @commands.command(name="mode")
    @commands.is_owner()
    async def _changeMode(self, ctx: commands.Context, mode: Optional[str] = None) -> None:
        modes = {
            "꺼짐": 0,
            "간단": 1,
            "기본": 2,
            "엄격": 3
        }
        if mode is None:
            await ctx.reply(f"🌟 > 현재 감지 모드는 `{list(modes)[self.mode]}`입니다.")
        elif mode not in modes:
            await ctx.reply(f"🌟 > `{mode}`(은)는 잘못된 모드 설정입니다.\n`꺼짐`, `간단`, `기본`, `엄격` 중에서 하나를 입력하세요.")
        else:   
            self.mode = modes[mode]
            await ctx.reply(f"🌟 > 감지 모드가 `{mode}`으로 설정되었습니다.")

    @commands.command(name="total")
    @commands.is_owner()
    async def _totalCounts(self, ctx: commands.Context, word: str) -> None:
        o = await aiomysql.connect(**self.bot.config.mysql)
        c = await o.cursor(aiomysql.DictCursor)
        await c.execute(f"SELECT * FROM `counts` WHERE `word` = '{word}' AND `guild` = '{ctx.guild.id}'")
        rows = await c.fetchall()
        if not rows:
            await ctx.reply(f"<a:clap:949665959084458036> > 아직 {word} 스트라이크를 발견하지 못했습니다.")
        else:
            datas = {}
            async for row in self.async_list(rows):
                if row["user"] not in datas:
                    datas[row["user"]] = 1
                else:
                    datas[row["user"]] += 1
            content = "```\n"
            async for d in self.async_list(datas):
                user = ctx.guild.get_member(int(d))
                if not user:
                    continue
                content += f"{user.display_name} - {datas[d]}회\n"
            content += f"```\n🌟 > {ctx.guild.name} 서버 내 {word} 스트라이크의 감지 횟수는 총 **{len(rows)}회**입니다."
            await ctx.reply(content)
        o.close()

    @commands.command(name="reset")
    @commands.is_owner()
    async def _resetCounts(self, ctx: commands.Context) -> None:
        ask = await ctx.reply(f"""
🔄 > 정말로 **{ctx.guild.name}** 서버의 전체 스트라이크 감지를 초기화하시겠습니까?
**이 작업은 영구적이며, 실행 이후에는 되돌릴 수 없습니다!**
되돌릴 수 없음을 이해했으며, 초기화 작업을 실행하시겠다면 `{self.bot.user.name}`를 입력하세요.
        """)
        def check(msg: disnake.Message) -> bool:
            return msg.author == ctx.author and msg.channel == ctx.channel and msg.content in [msg.guild.me.name, "취소"]
        try:
            msg = await self.bot.wait_for("message", timeout=30, check=check)
        except:
            await ask.delete()
        else:
            if msg.content == "취소":
                return await ask.delete()
            o = await aiomysql.connect(**self.bot.config.mysql)
            c = await o.cursor(aiomysql.DictCursor)
            await c.execute(f"DELETE FROM `counts` WHERE `guild` = '{ctx.guild.id}'")
            o.close()
            await ask.delete()
            await ctx.reply(content=f":wastebasket: > **{ctx.guild.name}** 서버의 전체 스트라이크 감지를 초기화했습니다.")

    @commands.group(name="word")
    @commands.is_owner()
    async def words(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            raise commands.BadArgument

    @words.command(name="reload")
    @commands.is_owner()
    async def _reloadWord(self, ctx: commands.Context) -> None:
        await self.prepare()
        await ctx.reply(f"🔄 > 단어 목록을 다시 불러왔습니다.")

    @words.command(name="add")
    @commands.is_owner()
    async def _addWord(self, ctx: commands.Context, word: str, detect: str) -> None:
        o = await aiomysql.connect(**self.bot.config.mysql)
        c = await o.cursor(aiomysql.DictCursor)
        await c.execute(f"INSERT INTO `detects` VALUES ('{detect}', '{word}')")
        o.close()
        await ctx.reply("<:popcorn_k:949665093044535336> > 단어 추가에 성공했습니다! 변경 사항을 적용하려면 `?word reload` 명령을 수행하세요.")
    
    @words.command(name="remove")
    @commands.is_owner()
    async def _removeWord(self, ctx: commands.Context, detect: str) -> None:
        o = await aiomysql.connect(**self.bot.config.mysql)
        c = await o.cursor(aiomysql.DictCursor)
        await c.execute(f"DELETE FROM `detects` WHERE `detection` = '{detect}'")
        o.close()
        await ctx.reply("<:popcorn_k:949665093044535336> > 단어를 삭제했습니다! 변경 사항을 적용하려면 `?word reload` 명령을 수행하세요.")


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Counter(bot))
