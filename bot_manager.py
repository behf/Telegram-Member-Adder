import asyncio
import logging
from typing import List

from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import (
    UserPrivacyRestricted,
    UserBannedInChannel,
    BotMethodInvalid,
    FloodWait,
    UserNotMutualContact, PeerFlood, PeerIdInvalid,
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

            members = account.get_chat_members(source_group_id)

            async for chat_member in members:

                if index == 0 and not chat_member.status == ChatMemberStatus.ADMINISTRATOR:
                    # Only first account scrapes and adds to contacts
                    extracted_member = Member(member=chat_member)
                    extracted_members.append(extracted_member)
                else:
                    # Other accounts just iterate without appending
                    pass

        utils.write_extracted_members(extracted_members=extracted_members, source_group_id=source_group_id)

        return extracted_members

    async def add_members_to_target_group(self, target_group_id: int, members: List[Member]) -> None:
        member_index = 0
        config = Config()

        target_group_members = await utils.get_target_group_member_ids(target_group_id, self.accounts[0])

        while member_index < len(members):

            for account in self.accounts:

                try:
                    member = members[member_index]
                except IndexError:
                    break

                print(f"trying for {member.user_id} {member.first_name}")
                member_index += 1

                if member.status != MemberStatus.NOT_PROCESSED:
                    continue
                if member.user_id in target_group_members:
                    member.status = MemberStatus.SKIPPED_ALREADY_MEMBER
                    continue

                try:

                    await account.add_chat_members(chat_id=target_group_id, user_ids=member.username)
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

                except PeerIdInvalid:
                    logger.warning("Make sure you meet the peer before interacting with it")
                    member.status = MemberStatus.SKIPPED_PEER_INVALID

                except TypeError:
                    logger.warning(f"User {member.user_id} has no username")
                    member.status = MemberStatus.SKIPPED_HAVE_NOT_USERNAME

                except Exception as e:
                    logger.exception(f"{account.name}: Error adding {member.user_id}", exc_info=e)

                utils.print_state(members)

                await asyncio.sleep(25 / len(self.accounts))

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

        if utils.is_scrapped(source_group_id):
            members = utils.read_scrapped_members(source_group_id)
        else:
            members = await self.scrape_source_group(source_group_id)
        await self.add_members_to_target_group(target_group_id, members)

        print("Members added successfully!")
