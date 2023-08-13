import asyncio
import logging
from typing import List

from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import (
    UserPrivacyRestricted,
    UserBannedInChannel,
    BotMethodInvalid,
    FloodWait,
    UserNotMutualContact, PeerFlood,
)

import utils
from Config import Config
from models.member import Member
from models.member_status import MemberStatus
from models.telegram_account import TelegramAccount

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class BotManager:

    def __init__(self):
        self.accounts: List[TelegramAccount] = []

    async def login(self):
        for account in self.accounts:
            await account.login()
            # Print separator
        print((40 * "*").center(60))

    async def scrape_source_group(self, source_group_id: int) -> List[Member]:
        extracted_members = []

        for index, account in enumerate(self.accounts):

            if utils.is_scrapped(source_group_id):
                # todo read from file
                pass
            members = account.get_chat_members(source_group_id)

            async for member in members:

                if index == 0 and not member.status == ChatMemberStatus.ADMINISTRATOR:
                    # Only first account scrapes and adds to contacts
                    extracted_member = Member(member=member)
                    extracted_members.append(extracted_member)
                else:
                    # Other accounts just iterate without appending
                    pass

        utils.write_extracted_members(extracted_members=extracted_members, source_group_id=source_group_id)

        return extracted_members

    async def add_members_to_target_group(self, target_group_id: int, members: List[Member]):
        member_index = 0
        config = Config()

        while member_index < len(members):

            for account in self.accounts:

                member = members[member_index]

                try:
                    await account.add_chat_members(chat_id=target_group_id, user_ids=member.user_id)
                    logger.info(f"{account.name}: Added {member.user_id}")
                    member.status = MemberStatus.ADDED_TO_GROUP

                except UserPrivacyRestricted:
                    logger.warning(f"{account.name}: {member.user_id} has privacy restricted")
                    member.status = MemberStatus.SKIPPED_PRIVACY

                except UserNotMutualContact:
                    logger.warning(f"{account.name}: You must be in their contacts to add {member.user_id}")
                    member.status = MemberStatus.SKIPPED_HAS_LEFT

                except PeerFlood:
                    logger.warning(f"{account.name}: Account restricted. can't add {member.user_id}")
                    member.status = MemberStatus.SKIPPED_ADDER_RESTRICTED

                except Exception as e:
                    logger.exception(f"{account.name}: Error adding {member.user_id}", exc_info=e)

                member_index += 1

                if member_index >= len(members):
                    break

                await asyncio.sleep(45 / len(self.accounts))

                utils.write_extracted_members(members, config.source_group)

    async def start_adding(self):
        if not utils.check_data_is_enough():
            return

        self.accounts = utils.read_accounts()
        await self.login()

        source_group_id, target_group_id = utils.add_group_ids()

        for account in self.accounts:
            if not await account.am_i_a_member(source_group_id, target_group_id):
                self.accounts.remove(account)

        members = await self.scrape_source_group(source_group_id)
        await self.add_members_to_target_group(target_group_id, members)

        print("Members added successfully!")
