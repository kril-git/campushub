from typing import NamedTuple


class PersonalRecordShort(NamedTuple):
    uuid: str
    surname: str
    given_name: str
    phone: str

    def format_line(self, i: int) -> str:
        return f"{i}, {self.uuid}, {self.surname}, {self.given_name}, {self.phone}\n"