from pyrogram import Client
from pyrogram.errors import ChannelInvalid


class TelegramAccount(Client):

    def __init__(self, api_id: int, api_hash: str, phone_number: str, device: dict):

        print(f"Initiating {phone_number}")

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
            print(f"Successfully Logged in with {self.phone_number}")
        else:
            print(f"Login to {self.phone_number} Failed.")

    async def am_i_a_member(self, source_group_id: int, target_group_id: int) -> bool:
        try:
            await self.get_chat(source_group_id)
        except ValueError:
            print(f"Account {self.phone_number} is not a member in {source_group_id} Source Group")
            return False

        try:
            await self.get_chat(target_group_id)
            return True
        except (ValueError, ChannelInvalid):
            print(f"Account {self.phone_number} is not a member in {target_group_id} Target Group")
            return False
