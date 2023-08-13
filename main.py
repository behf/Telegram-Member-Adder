import asyncio

from consolemenu import ConsoleMenu
from consolemenu.items import FunctionItem

import utils
from bot_manager import BotManager


def main():
    utils.create_required_directories()
    utils.add_phone_list()

    bot_manager = BotManager()

    menu = ConsoleMenu("Telegram Member Adder")

    # A FunctionItem runs a Python function when selected
    add_phone_number_item = FunctionItem("Add Phone number", utils.add_phone_number)
    add_api_credentials_item = FunctionItem("Add API-ID and API-HASH", utils.add_api_id_hash)

    loop = asyncio.get_event_loop()
    a1 = loop.create_task(bot_manager.start_adding())
    start_adding_members = FunctionItem("Start Adding members", loop.run_until_complete, [a1])

    menu.append_item(add_phone_number_item)
    menu.append_item(add_api_credentials_item)
    menu.append_item(start_adding_members)

    menu.show()


if __name__ == "__main__":
    main()
