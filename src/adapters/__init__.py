# Adapters module
from src.adapters.telegram import TelegramAdapter
from src.adapters.max import MaxAdapter
from src.adapters.vk import VKAdapter, vk_bot

__all__ = ["TelegramAdapter", "VKAdapter", "vk_bot", "MaxAdapter"]
