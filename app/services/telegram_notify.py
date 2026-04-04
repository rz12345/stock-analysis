import requests

class TelegramNotify:
    """
    透過 Telegram Bot API 發送訊息的靜態類別
    """
    API_BASE = 'https://api.telegram.org/bot{token}/sendMessage'
    MAX_LENGTH = 4096  # Telegram 單則訊息字元上限

    @staticmethod
    def sendMessage(bot_token: str, chat_id: str, message: str) -> bool:
        """
        發送訊息到指定的 Telegram chat

        Args:
            bot_token (str): Telegram Bot API token
            chat_id (str): 目標 chat/group/channel 的 ID
            message (str): 要發送的訊息內容

        Returns:
            bool: 是否全部發送成功
        """
        url = TelegramNotify.API_BASE.format(token=bot_token)

        # 訊息超過上限時分段發送
        chunks = [
            message[i:i + TelegramNotify.MAX_LENGTH]
            for i in range(0, len(message), TelegramNotify.MAX_LENGTH)
        ]

        for chunk in chunks:
            payload = {'chat_id': chat_id, 'text': chunk}
            response = requests.post(url, json=payload)
            if response.status_code != 200:
                print(f'Telegram 訊息發送失敗: {response.status_code}, {response.text}')
                return False

        return True
