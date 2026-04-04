from app.repositories.recent_transcation import TwRecentTranscation
from app.repositories.web_data_sync import TWWebData

if __name__ == "__main__":
    # Firebase realtime database 同步
    TWWebData().do_process()
    
    # 發送 Line Notify
    RecentTranscation = TwRecentTranscation()
    RecentTranscation.sendNotification()