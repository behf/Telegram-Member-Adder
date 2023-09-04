import asyncio
import logging
from typing import List, Union

from pyrogram import Client
from pyrogram.enums import UserStatus
from pyrogram.errors import ChannelInvalid, PeerIdInvalid, PeerFlood, UserNotMutualContact, UserPrivacyRestricted, \
    ChatWriteForbidden, ChatAdminRequired, UserKicked

import utils
from Config import Config
from models.member import Member
from models.member_status import MemberStatus


class TelegramAccount(Client):

    def __init__(self, api_id: int, api_hash: str, phone_number: str, device: dict):
        self.logger = logging.getLogger(f"member-adder.{__name__}")
        self.logger.debug(f"Initiating {phone_number}")
        # Set attributes
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.device_model = device["device_model"]
        self.system_version = device["system_version"]
        self.app_version = "0.1.0"
        self.workdir = "session"

        # Call parent Client class initializer
        super().__init__(
            name=phone_number,
            api_id=api_id,
            api_hash=api_hash,
            phone_number=phone_number,
            device_model=self.device_model,
            system_version=self.system_version,
            app_version=self.app_version,
            workdir=self.workdir,
        )

    async def login(self):

        # Start client session
        await self.start()

        # Check if login successful
        if await self.get_me():
            self.logger.info(f"Successfully Logged in with {self.phone_number}")
        else:
            self.logger.warning(f"Login to {self.phone_number} Failed.")
        await asyncio.sleep(0.1)

    async def am_i_a_member(self, source_group_id: Union[int, str], target_group_id: Union[int, str]) -> bool:
        try:
            await self.get_chat(source_group_id)
        except ValueError:
            self.logger.warning(f"Account {self.phone_number} is not a member in {source_group_id} Source Group")
            return False

        try:
            await self.get_chat(target_group_id)
            return True
        except (ValueError, ChannelInvalid):
            self.logger.warning(f"Account {self.phone_number} is not a member in {target_group_id} Target Group")
            return False

    async def scrap_group_members_from_messages(
            self,
            group_id: Union[int, str],
            limit: int,
            offset_id: int,
            status_list: List[UserStatus],
    ):
        set_of_users = set()

        config = Config()
        source_group_id = group_id
        target_group_id = config.target_group

        wait_time = 0.025
        counter = 0

        self.logger.info(
            f"{self.phone_number} has to scrap {limit} messages. it would take "
            f"{utils.seconds_to_human_readable(int(limit * wait_time))} if there were no limitations")

        self.logger.info(f"{self.phone_number} scrapping offset_id:{offset_id} limit:{limit}")

        async for message in self.get_chat_history(chat_id=source_group_id, limit=limit, offset_id=offset_id):
            user = message.from_user

            if not user or not utils.is_user_status_ok(user, status_list):
                continue

            counter += 1

            set_of_users.add(Member(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
            ))

            await asyncio.sleep(wait_time)

            if counter % 400 == 0:
                all_members = utils.get_other_scrapped_members(
                    source_group_id=source_group_id,
                    target_group_id=target_group_id,
                    phone_number=self.phone_number,
                )

                uniq = set_of_users - all_members

                self.logger.debug(f"{self.phone_number} extracted {len(set_of_users)}"
                                  f" users {len(uniq)} unique users,storing...")

                utils.write_members_partial(
                    members=list(uniq),
                    source_group_id=source_group_id,
                    target_group_id=config.target_group,
                    account_phone=self.phone_number,
                )
                if counter % 2000 == 0:
                    self.logger.info(f"{self.phone_number} users: {len(set_of_users)} unique users: {len(uniq)} "
                                     f"Elapsed time: "
                                     f"{utils.seconds_to_human_readable(int(counter * wait_time))} "
                                     f"Estimated Remaining time: "
                                     f"{utils.seconds_to_human_readable(int((limit - counter) * wait_time))}")

        self.logger.debug(f"{self.phone_number} finished scrapping.")

        all_members = utils.get_other_scrapped_members(
            source_group_id=source_group_id,
            target_group_id=target_group_id,
            phone_number=self.phone_number,
        )

        return set_of_users - all_members

    async def add_member_to_target_group(
            self,
            target_group_id: Union[int, str],
            source_group_id: Union[int, str],
            source_members: List[Member],
            target_group_members: List[int],
            adding_method: str,
            wait_time: int,
    ):
        is_ok = True

        for member in source_members:

            if member.status != MemberStatus.NOT_PROCESSED:
                continue

            if member.user_id in target_group_members:
                member.status = MemberStatus.SKIPPED_ALREADY_MEMBER
                continue

            try:

                await self.add_chat_members(chat_id=target_group_id, user_ids=getattr(member, adding_method))
                self.logger.warning(f"{self.name}: Added {member.user_id}")
                member.status = MemberStatus.ADDED_TO_GROUP

            except UserPrivacyRestricted:
                self.logger.warning(f"{self.name}: {member.user_id} has privacy restricted")
                member.status = MemberStatus.SKIPPED_PRIVACY

            except UserNotMutualContact:
                self.logger.warning(f"{self.name}: You must be in their contacts to add {member.user_id}")
                member.status = MemberStatus.SKIPPED_HAS_LEFT

            except PeerFlood:
                self.logger.warning(f"{self.name}: Account restricted. can't add {member.user_id}")
                member.status = MemberStatus.SKIPPED_ADDER_RESTRICTED
                is_ok = False

            except PeerIdInvalid:
                self.logger.warning("Make sure you meet the peer before interacting with it")
                member.status = MemberStatus.SKIPPED_PEER_INVALID

            except TypeError:
                self.logger.warning(f"User {member.user_id} has no username")
                member.status = MemberStatus.SKIPPED_HAVE_NOT_USERNAME

            except ChatWriteForbidden:
                self.logger.warning(f"{self.phone_number} has no rights to send messages in this chat!!")
                member.status = MemberStatus.SKIPPED_NO_MESSAGE_RIGHTS
                is_ok = False

            except ChatAdminRequired:
                self.logger.warning(f"{self.phone_number} has not admin rights in this chat")
                member.status = MemberStatus.SKIPPED_NO_ADMIN_RIGHTS
                is_ok = False

            except UserKicked:
                self.logger.warning(f"{self.phone_number}: user {member.user_id} has been kicked from group")
                member.status = MemberStatus.SKIPPED_USER_KICKED

            except Exception:
                self.logger.exception(f"{self.name}: Error adding {member.user_id}")
                member.status = MemberStatus.SKIPPED_OTHER_REASONS

            utils.write_members_partial(
                members=source_members,
                source_group_id=source_group_id,
                target_group_id=target_group_id,
                account_phone=self.phone_number,
            )

            if not is_ok:
                self.logger.warning(f"{self.phone_number}: Logging out of this account because it cannot add members")
                return

            await asyncio.sleep(wait_time)
