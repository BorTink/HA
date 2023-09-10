from aiogram.utils.helper import Helper, HelperMode, ListItem

class TestStates(Helper):
    mode = HelperMode.snake_case

    def add_state(self, telegram_id):
        return ListItem()
