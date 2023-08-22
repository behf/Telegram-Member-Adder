from models.member_status import MemberStatus


class Member:
    def __init__(
            self,
            member=None,
            user_id=None,
            username=None,
            first_name=None,
            last_name=None,
            status=MemberStatus.NOT_PROCESSED,
            processed_by=None,
    ):
        if member is not None:
            self.initialize_with_chat_member(member)
        else:
            self.initialize_with_attributes(
                user_id,
                username,
                first_name,
                last_name,
                status,
                processed_by,
            )

    def initialize_with_chat_member(self, member):
        self.user_id = member.user.id
        self.username = member.user.username
        self.first_name = member.user.first_name
        self.last_name = member.user.last_name
        self.status = MemberStatus.NOT_PROCESSED
        self.processed_by_phone = None

    def initialize_with_attributes(
            self,
            user_id,
            username,
            first_name,
            last_name,
            status=MemberStatus.NOT_PROCESSED,
            processed_by=None,
    ):
        self.user_id = user_id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.status = status
        self.processed_by_phone = processed_by

    def __repr__(self):
        return f"Member(user_id={self.user_id}, username={self.username}, status={self.status})"

    def __hash__(self):
        return hash(self.user_id)

    def __eq__(self, other):
        return self.user_id == other.user_id
