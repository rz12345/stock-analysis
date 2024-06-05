import requests

class LineNotify:

    def sendMessage(token, msg):
        headers = {
            "Authorization": "Bearer " + token, 
            "Content-Type" : "application/x-www-form-urlencoded"
        }

        payload = {'message': msg}
        r = requests.post("https://notify-api.line.me/api/notify", headers = headers, params = payload)        
        if r.status_code == 200:
            print('LINE Notify 通知發送成功')
        else:
            print(f'LINE Notify 通知發送失敗,錯誤代碼: {response.status_code}')
            
        return r.status_code