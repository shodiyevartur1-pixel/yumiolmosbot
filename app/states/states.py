from aiogram.fsm.state import State, StatesGroup


class TransferStates(StatesGroup):
    waiting_wallet_id = State()
    waiting_amount = State()
    confirm = State()


class WithdrawStates(StatesGroup):
    waiting_game_id = State()
    waiting_amount = State()
    confirm = State()


class AdminBroadcastStates(StatesGroup):
    waiting_content = State()
    confirm = State()


class AdminAddChannelStates(StatesGroup):
    waiting_username = State()


class AdminRemoveChannelStates(StatesGroup):
    waiting_choice = State()


class AdminChangeChannelStates(StatesGroup):
    waiting_choice = State()
    waiting_new_username = State()


class AdminSetReferralBonusStates(StatesGroup):
    waiting_value = State()


class AdminSetMinWithdrawStates(StatesGroup):
    waiting_value = State()


class AdminAddBalanceStates(StatesGroup):
    waiting_user = State()
    waiting_amount = State()


class AdminSubtractBalanceStates(StatesGroup):
    waiting_user = State()
    waiting_amount = State()


class AdminSearchUserStates(StatesGroup):
    waiting_query = State()


class AdminBanStates(StatesGroup):
    waiting_user = State()


class AdminUnbanStates(StatesGroup):
    waiting_user = State()


class AdminAddAdminStates(StatesGroup):
    waiting_user = State()
