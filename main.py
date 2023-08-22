import asyncio

from consolemenu import ConsoleMenu
from consolemenu.items import FunctionItem, SubmenuItem

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
    a1 = bot_manager.add_members_to_target_group()
    start_adding_members = FunctionItem("Start Adding members", loop.run_until_complete, [a1])

    # A SelectionMenu constructs a menu from a list of strings
    scrap_type_submenu = ConsoleMenu("Extract members")

    a2 = bot_manager.scrape_source_group()
    a3 = bot_manager.scrap_from_messages()

    normal_scrap_submenu = FunctionItem("Scrap members (normal and recommended)", loop.run_until_complete, [a2])
    message_scrap_submenu = FunctionItem("Scrap from messages(for groups with hidden members)", loop.run_until_complete,[a3])

    extract_members_item = SubmenuItem("Extract members", scrap_type_submenu, menu)

    scrap_type_submenu.append_item(normal_scrap_submenu)
    scrap_type_submenu.append_item(message_scrap_submenu)

    menu.append_item(add_phone_number_item)
    menu.append_item(add_api_credentials_item)
    menu.append_item(extract_members_item)
    menu.append_item(start_adding_members)

    menu.show()


if __name__ == "__main__":
    main()
