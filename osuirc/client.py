import asyncio
import logging
from typing import Any, Dict, TypeVar, Union, Callable

from .handler import IrcHandler, MultiplayerHandler
from .objects.channel import Channel, MpChannel
from .objects.message import Message
from .objects.user import User
from .utils.errors import EmptyError
from .utils.events import BaseMatchEvent


MatchEvent = TypeVar("MatchEvent", bound=BaseMatchEvent)
log = logging.getLogger("IrcClient")


def get_channel_name(channel: Union[Channel, str]):
    if isinstance(channel, Channel):
        channel_name = channel.name
    elif isinstance(channel, str):
        channel_name = ["#", ""][channel[0] == "#"] + channel  # 如果輸入沒有開頭 `#` 會自動補上
    else:
        raise ValueError("channel 參數只支援 Channel、str 類別")
    return channel_name


class IrcClient:
    def __init__(
        self,
        nickname: str,
        password: str,
        *,
        debug: bool = False,
        prefix: str = "!",
        api_key: str = None,
    ) -> None:
        # static
        self.host: str = "cho.ppy.sh"
        self.port: int = 6667
        self.encoding: str = "UTF-8"
        self.nickname: str = nickname
        self.password: str = password
        self.api_key: str = api_key
        self.prefix: str = prefix
        self.debug: bool = debug
        self.limit: float = 1.0
        self.running: bool = False

        self.channels: Dict[str, Union[Channel, MpChannel]] = {}
        self.commands: Dict[str, Callable] = {}
        self.users_cache: Dict[str, User] = {}

        self.irc_message_handler = IrcHandler(self)
        self.mphandler = MultiplayerHandler(self)

        self._flag_welcome = asyncio.Event()
        self._flag_motd_start = asyncio.Event()
        self._flag_motd_end = asyncio.Event()

    async def run(self):
        self.running = True
        self.sendmsg_queue = asyncio.Queue()
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            await self.send_command(f"PASS {self.password}")
            await self.send_command(f"NICK {self.nickname}")
            await asyncio.gather(self.listen(), self.sender())
        except KeyboardInterrupt:
            self.stop()
        finally:
            log.info("Closed")

    def stop(self):
        self.running = False

    async def send_command(self, content: str):
        self.writer.write((content + "\r\n").encode(self.encoding))
        log.debug(f"SEND_COMMAND: {content=}")

    async def send(
        self, target, content: str, *, action: bool = False, ignore_limit: bool = False
    ):
        _content = f"\x01ACTION {content}\x01" if action else content
        send_message = self.send_command(f"PRIVMSG {target} :{_content}")

        if ignore_limit:
            await send_message
        else:
            self.sendmsg_queue.put_nowait(send_message)

    async def join(self, channel: Union[Channel, str]):
        await self.send_command(f"JOIN {get_channel_name(channel)}")

    async def part(self, channel: Union[Channel, str]):
        await self.send_command(f"PART {get_channel_name(channel)}")

    async def listen(self):
        while self.running:
            if raw := await self.reader.readline():
                payload = raw.decode(self.encoding).strip()
                asyncio.create_task(self.irc_message_handler(payload))
            else:
                raise EmptyError("空資料")

    async def sender(self):
        while self.running:
            task = await self.sendmsg_queue.get()
            await task
            await asyncio.sleep(self.limit)

    def get_channel(self, channel_name: str) -> Union[Channel, MpChannel]:
        # 正規化 channel_name
        if channel_name[0] != "#":
            if channel_name.lower() == self.nickname.lower():
                return Channel(self, channel_name)
            channel_name = "#" + channel_name

        channel = self.channels.get(channel_name)
        if channel is None:
            is_mproom = channel_name[:4] == "#mp_"
            channel = [Channel, MpChannel][is_mproom](self, channel_name)
            self.channels[channel_name] = channel
            log.debug(f"NEW_CHANNEL: {channel=}")

        return channel
    
    def get_user(self, username: str):
        user = self.users_cache.get(username)
        if user:
            return user
        user = User(self, username)
        self.users_cache[username] = user
        return user

    def command(self, name: str = None):
        def wapper(func):
            cmd_name = name or func.__name__
            self.commands[cmd_name] = func
        return wapper

    def mp_listen(self, event: MatchEvent):
        """
        ## MP處理擴充
        範例:
        ```PY
        from osuirc import IrcClient
        from osuirc.utils.events import *

        bot = IrcClient()
        @bot.mp_listen(event.AllPlayerReady)
        async def on_ready(event):
            await event.channel.send('!mp start 10')
        ```
        """

        def decorator(func: Callable[[MatchEvent], Any]):
            if mpevt := self.mphandler.ext_events.get(event):
                mpevt.add(func)
            else:
                self.mphandler.ext_events[event] = set([func])

        return decorator

    async def call_command(self, ctx: Message):
        if ctx.content[0] == "!":
            ctx_split = ctx.content.removeprefix(self.prefix).split()
            cmd = ctx_split[0]
            args = ctx_split[1:]

            if command := self.commands.get(cmd):
                return asyncio.create_task(command(ctx, *args))
        else:
            if ctx.author.username == "BanchoBot" and not ctx.is_private:
                return asyncio.create_task(self.mphandler(ctx))

    # Events

    async def on_ready(self):
        pass

    async def on_ping(self, message: str):
        pass

    async def on_message(self, ctx: Message):
        await self.call_command(ctx)

    async def on_join(self, user: str, channel: Union[Channel, MpChannel]):
        pass

    async def on_part(self, user: str, channel: Union[Channel, MpChannel]):
        pass

    async def on_quit(self, user: str, reason: str):
        pass
