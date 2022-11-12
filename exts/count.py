import asyncio
import re
from typing import Any, List, Optional

import aiohttp
import aiomysql
import disnake
from disnake.ext import commands

class Counter(commands.Cog, name="욕설 감지기"):
    class View(disnake.ui.View):
        class Strict(disnake.ui.View):
            class StrictSelect(disnake.ui.StringSelect):
                def __init__(self, data: dict) -> None:
                    texts = ["꺼짐", "간단", "보통", "엄격"]
                    super().__init__(
                        placeholder=f"새로운 감지 모드를 지정해주세요. 현재 '{texts[int(data['mode'])]}'",
                        min_values=1,
                        max_values=1,
                        options=[
                            disnake.SelectOption(label="꺼짐", value="0", description="로이드가 더 이상 스트라이크를 감지하지 않습니다.", emoji="🚫"),
                            disnake.SelectOption(label="간단", value="1", description="스트라이크를 정확히 포함하는 경우에만 감지합니다.", emoji="❓"),
                            disnake.SelectOption(label="보통 (기본값)", value="2", description="스트라이크 내부 혹은 주변에 특수문자 및 숫자가 있는 경우에는 감지합니다.", emoji="❗"),
                            disnake.SelectOption(label="엄격", value="3", description="스트라이크 내부 혹은 주변에 어떠한 문자가 있더라도 감지합니다.", emoji="‼️")
                        ],
                        disabled=False,
                        row=0
                    )
                
                async def callback(self, inter: disnake.MessageInteraction):
                    o = await aiomysql.connect(**inter.bot.config.mysql)
                    c = await o.cursor(aiomysql.DictCursor)
                    await c.execute(f"UPDATE `settings` SET `mode` = '{self.values[0]}' WHERE `guild` = '{inter.guild.id}'")
                    o.close()
                    await inter.response.edit_message(content=f"{str(self.options[int(self.values[0])].emoji)} > 설정 완료! 이제 감지 모드는 `{self.options[int(self.values[0])].label}`입니다.", view=None)
                    self.view.stop()


            def __init__(self, ctx: commands.Context, msg: disnake.Message, data: dict) -> None:
                super().__init__(timeout=30)
                self.ctx = ctx
                self.msg = msg
                self.data = data
                self.add_item(self.StrictSelect(data))
            
            async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
                return self.ctx.author == inter.author
            
            async def on_timeout(self):
                await self.msg.delete()

            @disnake.ui.button(
                label="취소하기",
                style=disnake.ButtonStyle.red,
                emoji="🆖",
                disabled=False,
                row=1
            )
            async def _cancel(self, button: disnake.Button, inter: disnake.MessageInteraction) -> None:
                await inter.response.pong()
                await self.msg.delete()
                self.stop()
        

        class Respond(disnake.ui.View):
            class RespondSelect(disnake.ui.StringSelect):
                def __init__(self, data: dict) -> None:
                    texts = ["매너 모드", "약하게", "적당하게", "시끄럽게"]
                    super().__init__(
                        placeholder=f"새로운 응답 유형을 지정해주세요. 현재 '{texts[int(data['respond'])]}'",
                        min_values=1,
                        max_values=1,
                        options=[
                            disnake.SelectOption(label="매너 모드", value="0", description="로이드가 스트라이크를 감지하더라도 알리지 않습니다. 카운트는 추가됩니다.", emoji="🔇"),
                            disnake.SelectOption(label="약하게", value="1", description="로이드가 스트라이크를 감지하면 해당 메시지에 반응을 추가합니다.", emoji="🔉"),
                            disnake.SelectOption(label="적당하게 (기본값)", value="2", description="로이드가 스트라이크를 감지하면 유저를 멘션하며 스트라이크 감지를 알립니다.", emoji="🔊"),
                            disnake.SelectOption(label="시끄럽게", value="3", description="로이드가 스트라이크를 감지하면 스트라이크 감지를 알리고, 해당 메시지를 삭제합니다.", emoji="📣")
                        ],
                        disabled=False,
                        row=0
                    )
                
                async def callback(self, inter: disnake.MessageInteraction):
                    o = await aiomysql.connect(**inter.bot.config.mysql)
                    c = await o.cursor(aiomysql.DictCursor)
                    await c.execute(f"UPDATE `settings` SET `respond` = '{self.values[0]}' WHERE `guild` = '{inter.guild.id}'")
                    o.close()
                    await inter.response.edit_message(content=f"{str(self.options[int(self.values[0])].emoji)} > 설정 완료! 이제 `{self.options[int(self.values[0])].label}` 상태로 스트라이크에 반응합니다.", view=None)
                    self.view.stop()


            def __init__(self, ctx: commands.Context, msg: disnake.Message, data: dict) -> None:
                super().__init__(timeout=30)
                self.ctx = ctx
                self.msg = msg
                self.data = data
                self.add_item(self.RespondSelect(data))
            
            async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
                return self.ctx.author == inter.author
            
            async def on_timeout(self):
                await self.msg.delete()

            @disnake.ui.button(
                label="취소하기",
                style=disnake.ButtonStyle.red,
                emoji="🆖",
                disabled=False,
                row=1
            )
            async def _cancel(self, button: disnake.Button, inter: disnake.MessageInteraction) -> None:
                await inter.response.pong()
                await self.msg.delete()
                self.stop()


        def __init__(self, ctx: commands.Context, msg: disnake.Message) -> None:
            super().__init__(timeout=60)
            self.ctx = ctx
            self.msg = msg
            self.views = {"strict": self.Strict, "respond": self.Respond}
        
        async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
            return inter.author == self.ctx.author
        
        async def on_timeout(self):
            await self.msg.delete()

        @disnake.ui.string_select(
            placeholder="변경할 설정을 선택해주세요.",
            min_values=1,
            max_values=1,
            options=[
                disnake.SelectOption(label="감지 모드 변경하기", value="strict", description="로이드의 스트라이크 감지 민감도를 설정합니다.", emoji="🚨"),
                disnake.SelectOption(label="응답 유형 변경하기", value="respond", description="로이드가 스트라이크를 감지했을 때의 응답을 조정합니다.", emoji="💬"),
            ],
            disabled=False,
            row=0
        )
        async def _whatToChange(self, select: disnake.ui.StringSelect, inter: disnake.MessageInteraction) -> None:
            o = await aiomysql.connect(**inter.bot.config.mysql)
            c = await o.cursor(aiomysql.DictCursor)
            await c.execute(f"SELECT * FROM `settings` WHERE `guild` = '{inter.guild.id}'")
            rows = await c.fetchall()
            data = rows[0]
            view = self.views[select.values[0]](self.ctx, self.msg, data)
            await inter.response.edit_message(view=view)
            o.close()
            await view.wait()
            self.stop()
        
        @disnake.ui.button(
            label="취소하기",
            style=disnake.ButtonStyle.red,
            emoji="🆖",
            disabled=False,
            row=1
        )
        async def _cancel(self, button: disnake.Button, inter: disnake.MessageInteraction) -> None:
            await inter.response.pong()
            await self.msg.delete()
            self.stop()


    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    async def find(self, content: str, mode: int) -> Optional[List[str]]:
        if content.startswith("https://") or content.startswith("http://"):
            return
        
        if mode < 1:
            return

        content = content.lower()
        if mode >= 2:
            exp = re.compile(r"[^a-zA-Zㄱ-ㅎㅏ-ㅣ가-힣]")
            removes = exp.findall(content)
            async for rem in self.async_list(removes):
                content = content.replace(rem, "")
        async for word in self.async_list(self.words):
            async for detection in self.async_list(self.words[word]):
                if detection in content:
                    return [word, detection]
                if mode >= 3:
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
        await self.load_settings()
    
    async def load_settings(self) -> None:
        await self.bot.wait_until_ready()
        self.settings = {}
        o = await aiomysql.connect(**self.bot.config.mysql)
        c = await o.cursor(aiomysql.DictCursor)
        await c.execute("SELECT * FROM `settings`")
        rows = await c.fetchall()
        async for row in self.async_list(rows):
            self.settings[int(row["guild"])] = {"mode": int(row["mode"]), "respond": int(row["respond"])}

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
        
        if msg.content.startswith("?total") or msg.content.startswith("?strike add") or msg.content.startswith("?strike remove"):
            return

        result = await self.find(msg.clean_content, self.settings[msg.guild.id]["mode"])
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
        rsp = self.settings[msg.guild.id]["respond"]
        if rsp == 1:
            await msg.add_reaction("<:absolute:1002916291226644572>")
        elif rsp >= 2:
            await msg.channel.send(f"""
🌟 > {msg.author.mention}님이 카운트를 추가합니다!
감지된 스트라이크 : {result[0]}
            """)
            if rsp == 3:
                await msg.delete()
        else:
            pass
    
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
**이 작업은 영구적이며, 실행 이후에는 실행 이전으로 되돌릴 수 없습니다!**
이를 이해했으며, 초기화 작업을 실행하시겠다면 `{self.bot.user.name}`를 입력하세요.
작업 요청은 30초 후에 만료됩니다. 즉시 취소하려면 `취소`를 입력하세요.
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

    @commands.command(name="settings", aliases=["option", "config"])
    @commands.is_owner()
    async def _settings(self, ctx: commands.Context) -> None:
        msg = await ctx.reply(f"⚙️ > 현재 {ctx.guild.name} 서버의 설정을 변경하고 있습니다...")
        view = self.View(ctx, msg)
        await msg.edit(view=view)
        await view.wait()
        await self.load_settings()

    @commands.group(name="strike")
    @commands.is_owner()
    async def words(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            raise commands.BadArgument

    @words.command(name="list")
    @commands.is_owner()
    async def _wordList(self, ctx: commands.Context) -> None:
        content = ""
        async for word in self.async_list(self.words):
            content += f"\n{word} 단어에 추가된 스트라이크 목록 ({len(self.words[word])}개) :\n"
            async for detection in self.async_list(self.words[word]):
                content += f"{detection}\n"
        
        async with aiohttp.ClientSession() as cs:
            async with cs.post("https://hastebin.com/documents", data=content) as r:
                res = await r.json()
                await ctx.reply(f"📜 > 현재 캐싱된 스트라이크 목록을 보려면 아래 링크를 확인하세요.\nhttps://hastebin.com/{res['key']}")

    @words.command(name="reload")
    @commands.is_owner()
    async def _reloadWord(self, ctx: commands.Context) -> None:
        await self.prepare()
        await ctx.reply(f"🔄 > 스트라이크 목록을 다시 불러왔으며, 캐싱했습니다.")

    @words.command(name="add")
    @commands.is_owner()
    async def _addWord(self, ctx: commands.Context, word: str, detect: str) -> None:
        o = await aiomysql.connect(**self.bot.config.mysql)
        c = await o.cursor(aiomysql.DictCursor)
        await c.execute(f"INSERT INTO `detects` VALUES ('{detect}', '{word}')")
        o.close()
        await ctx.reply("<:popcorn_k:949665093044535336> > 스트라이크 추가에 성공했습니다! 변경 사항을 적용하려면 `?strike reload` 명령을 수행하세요.")
    
    @words.command(name="remove")
    @commands.is_owner()
    async def _removeWord(self, ctx: commands.Context, detect: str) -> None:
        o = await aiomysql.connect(**self.bot.config.mysql)
        c = await o.cursor(aiomysql.DictCursor)
        await c.execute(f"DELETE FROM `detects` WHERE `detection` = '{detect}'")
        o.close()
        await ctx.reply("<:popcorn_k:949665093044535336> > 스트라이크를 삭제했습니다! 변경 사항을 적용하려면 `?strike reload` 명령을 수행하세요.")


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Counter(bot))
