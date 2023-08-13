import json

from pyrogram.types import ChatMember
from models.member_status import MemberStatus


class Member:
    def __init__(self, member: ChatMember):
        self.user_id: int = member.user.id
        self.username: str = member.user.username
        self.first_name: str = member.user.first_name
        self.last_name: str = member.user.last_name
        self.status: MemberStatus = MemberStatus.NOT_PROCESSED
        self.processed_by_phone: str = None

    def __init__(self, user_id, username, first_name, last_name, status, processed_by):
        self.user_id: int = user_id
        self.username: str = username
        self.first_name: str = first_name
        self.last_name: str = last_name
        self.status: MemberStatus = status
        self.processed_by_phone: str = processed_by
