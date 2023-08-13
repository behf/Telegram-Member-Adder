from json import JSONEncoder, JSONDecoder

from pyrogram.types import ChatMember

from models.member import Member
from models.member_status import MemberStatus


class MemberEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Member):
            return {
                "user_id": obj.user_id,
                "username": obj.username,
                "first_name": obj.first_name,
                "last_name": obj.last_name,
                "status": obj.status.name,
                "processed_by_phone": obj.processed_by_phone
            }
        if isinstance(obj, MemberStatus):
            return obj.value  # Serialize the enum value
        return super().default(obj)


class MemberDecoder(JSONDecoder):
    def __init__(self, *args, **kwargs):
        JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        if 'user_id' in obj:
            return Member(
                user_id=obj['user_id'],
                username=obj['username'],
                first_name=obj['first_name'],
                last_name=obj['last_name'],
                status=MemberStatus[obj['status']],
                processed_by=obj['processed_by_phone']
            )
        return obj
