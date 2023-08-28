import datetime
import json
import pathlib
import random
import re
from collections import Counter
from typing import List, Dict, Tuple

from pyrogram import Client
from pyrogram.enums import UserStatus
from pyrogram.types import User

from Config import Config
from models.MemberEncoder import MemberEncoder, MemberDecoder
from models.member import Member


def read_devices() -> List[Dict]:
    with open("src/device.json") as f_devices:
        devices = json.load(f_devices)
    return devices


def get_random_device() -> Dict:
    devices = read_devices()
    return random.choice(devices)


def prepare_accounts_info():
    config = Config()
    for phone_number in config.phone_numbers:
        dic = random.choice(config.api_credentials)
        dic["phone_number"] = phone_number
        dic["device"] = get_random_device()
        d = {k.lower(): v for k, v in dic.items()}
        yield d


def create_required_directories():
    # Create session folder if it doesn't exist
    session_path = pathlib.Path('session')
    session_path.mkdir(exist_ok=True)

    # Create groups folder if it doesn't exist
    groups_path = pathlib.Path("src/groups")
    groups_path.mkdir(parents=True, exist_ok=True)


def write_members(extracted_members: Dict[str, List[Member]], source_group_id: int, target_group_id: int) -> None:
    with open(f'src/groups/{abs(source_group_id)}_{abs(target_group_id)}.json', 'w', encoding="utf-8") as f:
        json.dump(extracted_members, f, indent=4, ensure_ascii=False, cls=MemberEncoder)


def write_members_partial(
        members: List[Member],
        source_group_id: int,
        target_group_id: int,
        account_phone: str,
) -> None:
    all_members_dict = read_scrapped_members(source_group_id=source_group_id, target_group_id=target_group_id)
    all_members_dict[account_phone] = members
    write_members(extracted_members=all_members_dict, source_group_id=source_group_id, target_group_id=target_group_id)


def get_source_group_id() -> int:
    config = Config()
    source_group_id = config.source_group

    while True:

        source_input = input(f"Enter source group ID ({source_group_id}): ")
        source_input = source_input or source_group_id

        if is_valid_group_id(source_input):
            config.source_group = int(source_input)
            return int(source_input)
        else:
            print("Invalid Group ID")


def get_target_group_id() -> int:
    config = Config()
    target_group_id = config.target_group

    while True:

        target_input = input(f"Enter target group ID ({target_group_id}): ")
        target_input = target_input or target_group_id

        if is_valid_group_id(target_input):
            return int(target_input)
        else:
            print("Invalid Group ID")


def add_group_ids() -> Tuple[int, int]:
    source_group_id = get_source_group_id()
    target_group_id = get_target_group_id()

    config = Config()
    config.source_group = source_group_id
    config.target_group = target_group_id

    return source_group_id, target_group_id


def is_valid_group_id(group_id) -> bool:
    pattern = re.compile("-?[0-9]+")
    match = pattern.match(str(group_id))
    return bool(match)


def get_valid_api_id() -> id:
    while True:
        api_id = input("Enter API ID:")
        if is_valid_api_id(api_id):
            return int(api_id)
        else:
            print("Invalid format")


def get_valid_api_hash() -> str:
    while True:
        api_hash = input("Enter API Hash:")
        if is_valid_api_hash(api_hash):
            return api_hash
        else:
            print("Invalid format")


def is_valid_api_id(api_id) -> bool:
    pattern = re.compile(r"\d+")
    match = pattern.match(api_id)
    return bool(match)


def is_valid_api_hash(api_hash) -> bool:
    pattern = re.compile("^[a-f0-9]+$")
    match = pattern.match(api_hash)
    return bool(match)


def add_api_id_hash() -> None:
    while True:
        api_id = get_valid_api_id()
        api_hash = get_valid_api_hash()

        config = Config()

        api_credentials = config.api_credentials
        api_credential = {"API_ID": api_id, "API_HASH": api_hash}
        api_credentials.append(api_credential)

        config.api_credentials = api_credentials

        reply = input("Do you want to add more API-ID and API-HASH?(N/y)?")
        if reply.lower().startswith("n") or reply == "":
            break


def get_valid_phone_number() -> str:
    while True:
        phone_number = input("Enter phone number with country code:")
        if is_valid_phone_number(phone_number):
            return phone_number
        else:
            print("phone number format is not correct!")


def is_valid_phone_number(phone_number: str) -> bool:
    pattern = re.compile(r"\+\d+")
    match = pattern.match(phone_number)
    return bool(match)


def add_phone_number() -> None:
    while True:
        phone_number = get_valid_phone_number()

        config = Config()

        phone_numbers = config.phone_numbers
        phone_numbers.append(phone_number)

        config.phone_numbers = phone_numbers

        if input("Do you want to add more phone numbers(N/y)?").lower().startswith("n"):
            break


def read_phone_list() -> List[str]:
    with open("src/phones.txt") as f:
        lines = f.readlines()
    phone_list = [line.rstrip('\n') for line in lines]
    return phone_list


def add_phone_list() -> None:
    config = Config()
    phone_numbers = set(config.phone_numbers)
    phone_numbers.update(read_phone_list())
    config.phone_numbers = list(phone_numbers)


def has_phone_numbers() -> bool:
    config = Config()
    return bool(config.phone_numbers)


def has_api_credentials() -> bool:
    config = Config()
    return bool(config.api_credentials)


def check_data_is_enough() -> bool:
    if not has_phone_numbers():
        print("You haven't Added any phone numbers yet, Use #1 in the menu to add your phone numbers")
        return False
    if not has_api_credentials():
        print("You haven't Added any API-ID and API_HASH yet, Use #2 in the menu to add your API ID/HASH")
        return False
    return True


def is_scrapped(source_group_id: int, target_group_id: int) -> bool:
    group_filename = pathlib.Path(f"src/groups/{abs(source_group_id)}_{abs(target_group_id)}.json")
    return group_filename.exists()


def read_scrapped_members(source_group_id: int, target_group_id: int) -> Dict[str, List[Member]]:
    group_filename = pathlib.Path(f"src/groups/{abs(source_group_id)}_{abs(target_group_id)}.json")
    with open(file=group_filename, mode='r', encoding="utf-8") as f:
        list_of_members = json.load(f, cls=MemberDecoder)
    return list_of_members


def print_state(members: List[Member]) -> None:
    status_counts = Counter(member.status for member in members)
    print(status_counts)


async def get_target_group_member_ids(group_id: int, client: Client) -> List[int]:
    members = []
    async for member in client.get_chat_members(chat_id=group_id):
        members.append(member.user.id)
    return members


def ask_for_rescrap(source_group_id: int, target_group_id: int) -> bool:
    group_scrap_path = pathlib.Path(f"src/groups/{abs(source_group_id)}_{abs(target_group_id)}.json")
    if not group_scrap_path.exists():
        return True
    inpt = input("we have scraped this group before, Do you want to scrap it again?(Yes/no)")

    if inpt.lower().startswith('n'):
        return False
    return True


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def get_adding_method() -> str:
    config = Config()
    options = ["username", "id"]
    options = [option.capitalize() if option in config.adding_method else option for option in options]

    answer = input(f"How do you want to add members[{'/'.join(options)}]?")
    if answer.lower().startswith("u"):
        config.adding_method = "username"
    elif answer.lower().startswith("i"):
        config.adding_method = "user_id"

    return config.adding_method


def get_member_last_seen_status() -> List[UserStatus]:
    config = Config()
    statuses = [
        UserStatus.ONLINE,
        UserStatus.RECENTLY,
        UserStatus.LAST_WEEK,
        UserStatus.LAST_MONTH,
        UserStatus.LONG_AGO,
    ]

    while True:
        reply = input(
            f"""
            1- Online
            2- Last seen recently
            3- Last seen within a week
            4- Last seen within a month
            5- Last seen a long time ago
            Choose the online status of members to be scrapped[{statuses.index(config.last_seen)+1}]:
        """)
        if reply == '':
            config.last_seen = statuses[statuses.index(config.last_seen)]
            return statuses[:statuses.index(config.last_seen)+1]
        try:
            reply = int(reply)
        except ValueError:
            print("Invalid input, Please enter a number!")
        else:
            config.last_seen = statuses[reply-1]
            return statuses[:reply]


def calculate_user_last_seen(user: User) -> UserStatus:
    if user.status == UserStatus.OFFLINE:
        return calculate_time_difference(user.last_online_date)
    return user.status


def is_user_status_ok(user: User, status_list: List[UserStatus]) -> bool:
    status = calculate_user_last_seen(user)
    return status in status_list


def calculate_time_difference(input_datetime):
    # Get the current date and time
    current_datetime = datetime.datetime.now()

    # Calculate the difference between the input datetime and the current datetime
    time_difference = current_datetime - input_datetime

    # Define time intervals for "Recently," a week, and a month
    recently_interval = datetime.timedelta(days=3)
    one_week = datetime.timedelta(weeks=1)
    one_month = datetime.timedelta(days=30)

    # Compare the time difference with the intervals
    if time_difference <= recently_interval:
        return UserStatus.RECENTLY
    elif time_difference <= one_week:
        return UserStatus.LAST_WEEK
    elif time_difference <= one_month:
        return UserStatus.LAST_MONTH
    else:
        return UserStatus.LONG_AGO
