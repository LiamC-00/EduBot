# Discord bot for the TU Delft Aerospace Engineering Python course
# Copyright (C) 2020 Delft University of Technology

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public
# License along with this program.
# If not, see <https://www.gnu.org/licenses/>.

"""Contains functions and classes for running :py:class:`EduBot`."""

import asyncio
import os
from typing import Optional

import click

try:
    from edubot.bot import EduBot
except ImportError as e:  # Edubot is not installed
    if not __package__:
        # run.py is being run locally as a script
        import sys
        import inspect

        filepath = inspect.getfile(inspect.currentframe())  # path of run.py
        sys.path.insert(0, os.path.join(os.path.dirname(filepath), ".."))
        from edubot.bot import EduBot
    else:
        # Something went very wrong, EduBot is not installed and run.py
        # is imported as a package. This is deffinitely not the intended
        # usage so we raise the exception
        raise e

TOKEN = os.getenv("DISCORD_TOKEN")


class BotRunner:
    """Runs :py:class:`EduBot` in the standard blocking manner."""

    def __init__(self, token: Optional[str] = TOKEN):
        self.validate_token(token)
        self.bot = EduBot()
        self.run(token)

    def run(self, token: str) -> None:
        """Runs the bot with the given ``token`` as a blocking call."""
        self.bot.run(token)

    # TODO find a better validation method later or remove completely
    @staticmethod
    def validate_token(token: str) -> None:
        """Ensures that the provided ``token`` is valid."""
        _error_msg = "No Discord API token could be retrieved"
        assert isinstance(token, str) and len(token) != 0, _error_msg


class InteractiveBotRunner(BotRunner):
    """Runs :py:class:`EduBot` in a non-blocking manner.

    This is suitable for running the bot with interactive consoles such
    as IPython. An example would be sending out direct-messages to all
    users currently in the Discord lobby::

        >>> TOKEN = os.getenv("DISCORD_TOKEN")
        >>> runner = InteractiveBotRunner(TOKEN)
        >>> users = filter(
        ...     lambda u: u is not runner.bot.user, runner.bot.users
        ... )
        >>> for user in users:
        >>>     task = runner.bot.dm(user, "Hello!")
        >>>     runner.create_task(task)

    Note:
        In the example above, :py:meth:`create_task` must be used to
        perform the call to the Discord API. Otherwise a coroutine
        object will be returned from simply calling methods of
        :py:class:`EduBot`.

    Caution:
        No clean-up action will be called after the interactive console
        is closed therefore no saving operations will take place. DO NOT
        USE THIS FOR ACTUAL SESSIONS!
    """

    def __init__(self, token: Optional[str] = TOKEN):
        self.loop = asyncio.get_event_loop()
        self.loop.set_debug(True)
        super().__init__(token)

    def run(self, token: str) -> asyncio.Task:
        """Retrieves the active event loop and runs the bot on it.

        By retrieving the event-loop (if it exists) with
        :py:func:`asyncio.get_event_loop`, we guarantee that the
        :py:class:`EduBot` will integrate into the already present
        event-loop of the interactive console (IPython).
        """
        self.create_task(self.bot.start(token))

    def create_task(self, coroutine: asyncio.coroutine) -> asyncio.Task:
        """Schedules a ``coroutine`` to be run by the event-loop.

        The purpose of this function is to simply reduce the amount of
        code that needs to be typed when a command needs to be issued
        from within the interactive console. All this method does is
        call :py:func:`asyncio.loop.create_task` on the given ``task``.
        """
        return self.loop.create_task(coroutine)


@click.command()
@click.option("--token", default=TOKEN, help="Specifies the Discord API Token")
def cli(token: str) -> BotRunner:
    """Command Line Interface (CLI) of :py:class:`EduBot`.

    Args:
        token: Discord API Token

    """
    return BotRunner(token)


def is_ipython() -> bool:
    """Determines if IPython is currently running.

    Note:
        Encapsulating the `get_ipython` call with this function avoids
        having to force developers/users to install IPython for the rest
        of the functionality to work.
    """
    try:
        from IPython import get_ipython

        return get_ipython()
    except ImportError:
        return False


if __name__ == "__main__":
    runner = InteractiveBotRunner(TOKEN) if is_ipython() else BotRunner(TOKEN)
    bot = runner.bot
