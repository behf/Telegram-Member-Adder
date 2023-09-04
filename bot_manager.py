import asyncio
import gc
import logging
from typing import List

from pyrogram.enums import ChatMemberStatus

import utils
from Config import Config
from models.member import Member
from models.telegram_account import TelegramAccount

logger = logging.getLogger(f"member-adder.{__name__}")


class BotManager:

    def __init__(self):
        self.accounts: List[TelegramAccount] = []

    async def login(self):
        for account in self.accounts:
            await account.login()

    async def start_bots(self):
        if not utils.check_data_is_enough():
            return False

        if len(self.accounts) > 0:
            logger.debug("already read accounts, cancelling")
            return True

        self.accounts = self.read_accounts()

        await self.login()
        return True

    @staticmethod
    def read_accounts() -> List[TelegramAccount]:
        accounts = []
        for info in utils.prepare_accounts_info():
            accounts.append(TelegramAccount(**info))
        return accounts

    async def scrape_source_group(self) -> None:
        if not await self.start_bots():
            return

        source_group_id, target_group_id = utils.add_group_ids()

        if not utils.ask_for_rescrap(source_group_id=source_group_id, target_group_id=target_group_id):
            return

        status_list = utils.get_member_last_seen_status()

        await self.check_all_accounts_are_a_member()

        members_list = []

        for index, account in enumerate(self.accounts):

            members = account.get_chat_members(source_group_id)

            async for chat_member in members:
                gc.disable()

                if index == 0 and not chat_member.status == ChatMemberStatus.ADMINISTRATOR:
                    if not utils.is_user_status_ok(chat_member.user, status_list):
                        continue
                    # Only first account scrapes and adds to contacts
                    extracted_member = Member(member=chat_member)
                    members_list.append(extracted_member)
                    gc.enable()
                else:
                    # Other accounts just iterate without appending
                    pass

        chunk_size = int(len(members_list) / len(self.accounts))

        dict_of_members = dict.fromkeys([account.phone_number for account in self.accounts])
        dict_of_members = dict(zip(dict_of_members.keys(), list(utils.chunks(members_list, chunk_size))))

        utils.write_members(
            extracted_members=dict_of_members,
            source_group_id=source_group_id,
            target_group_id=target_group_id,
        )
        logger.info(f"members of {source_group_id} scraped and stored in a file.")

    async def scrap_from_messages(self) -> None:

        if not await self.start_bots():
            return

        source_group_id, target_group_id = utils.add_group_ids()

        if not utils.ask_for_rescrap(source_group_id=source_group_id, target_group_id=target_group_id):
            return

        status_list = utils.get_member_last_seen_status()

        await self.check_all_accounts_are_a_member()

        async for message in self.accounts[0].get_chat_history(chat_id=source_group_id, limit=10):
            if message.id:
                last_message_id = message.id
                break

        offset_id = int(last_message_id / len(self.accounts))

        awaitables = []

        for multiplier, account in enumerate(self.accounts, 0):
            awaitables.append(account.scrap_group_members_from_messages(
                group_id=source_group_id,
                limit=offset_id,
                offset_id=last_message_id - (multiplier * offset_id),
                status_list=status_list,
            ))
        logger.info("Start to scrap members. this may take a few minutes.")

        list_of_set_of_members = await asyncio.gather(*awaitables)

        dict_of_members = dict.fromkeys([account.phone_number for account in self.accounts])
        dict_of_members = dict(zip(dict_of_members.keys(), [list(s) for s in list_of_set_of_members]))

        utils.write_members(
            extracted_members=dict_of_members,
            source_group_id=source_group_id,
            target_group_id=target_group_id,
        )
        logger.info(f"members of {source_group_id} scraped from messages and stored in a file.")

    async def add_members_to_target_group(self) -> None:
        if not await self.start_bots():
            return

        config = Config()

        source_group_id, target_group_id = utils.add_group_ids()

        if not utils.is_scrapped(source_group_id=source_group_id, target_group_id=target_group_id):
            print("Group not scrapped, Please scrap and retry")
            return

        wait_time = utils.get_wait_time()

        await self.check_all_accounts_are_a_member()

        adding_method = utils.get_adding_method()

        target_group_members = await utils.get_target_group_member_ids(target_group_id, self.accounts[0])
        members = utils.read_scrapped_members(source_group_id=source_group_id, target_group_id=target_group_id)

        await asyncio.gather(*[account.add_member_to_target_group(
            target_group_id=target_group_id,
            source_group_id=source_group_id,
            source_members=members[account.phone_number],
            target_group_members=target_group_members,
            adding_method=adding_method,
            wait_time=wait_time,
        ) for account
            in self.accounts])

        utils.write_members(
            extracted_members=members,
            source_group_id=config.source_group,
            target_group_id=target_group_id,
        )
        print("Finished adding members!")

    async def check_all_accounts_are_a_member(self):
        config = Config()

        for account in self.accounts:
            if not await account.am_i_a_member(config.source_group, config.target_group):
                self.accounts.remove(account)
