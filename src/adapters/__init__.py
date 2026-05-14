# Adapters module
from src.adapters.telegram import TelegramAdapter
from src.adapters.vk import VKAdapter, vk_bot
from src.adapters.max import MaxAdapter

__all__ = ["TelegramAdapter", "VKAdapter", "vk_bot", "MaxAdapter"]
