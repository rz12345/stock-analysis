from app.repositories.recent_transcation import UsRecentTranscation
from app.repositories.web_data_sync import USWebData

if __name__ == "__main__":
    # Firebase realtime database 同步
    USWebData().do_process()
    
    # 發送 Line Notify    
    RecentTranscation = UsRecentTranscation()
    RecentTranscation.sendNotification()
