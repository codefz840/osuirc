from typing import TYPE_CHECKING, Any, Dict
import asyncio

if TYPE_CHECKING:
    from ..client import IrcClient


class User(object):
    def __init__(self, client: "IrcClient", username: str, user_id: int = None) -> None:
        self.__client = client
        self.username = username

        if username == 'BanchoBot':
            self.user_id = 3
            return

        self.user_id = user_id
        asyncio.run(self.__client.send_command("WHOIS " + username))

    def __repr__(self) -> str:
        return f"<User {self.username}>"

    def __str__(self) -> str:
        return self.username

    async def send(
        self, message: str, *, action: bool = False, ignore_limit: bool = False
    ):
        await self.__client.send(
            self.username, message, action=action, ignore_limit=ignore_limit
        )
