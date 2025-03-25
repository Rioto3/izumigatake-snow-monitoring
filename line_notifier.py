import os
import json
import logging
import requests
from dotenv import load_dotenv

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("line_notify.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("line_notifier")

class LineMessenger:
    def __init__(self, channel_access_token):
        self.channel_access_token = channel_access_token
        self.headers = {
            'Authorization': f'Bearer {channel_access_token}',
            'Content-Type': 'application/json'
        }
    
    def send_message_with_image(self, user_id, message, image_url):
        """Push APIを使用してメッセージと画像を送信"""
        try:
            # LINE Messaging APIのエンドポイント
            url = 'https://api.line.me/v2/bot/message/push'
            
            # メッセージデータ
            data = {
                "to": user_id,
                "messages": [
                    {
                        "type": "text",
                        "text": message
                    },
                    {
                        "type": "image",
                        "originalContentUrl": image_url,
                        "previewImageUrl": image_url
                    }
                ]
            }
            
            # メッセージを送信
            response = requests.post(url, headers=self.headers, json=data)
            
            if response.status_code == 200:
                logger.info(f"LINE message sent successfully to {user_id}")
                return True
            else:
                logger.error(f"Failed to send LINE message: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending LINE message: {str(e)}", exc_info=True)
            return False
    
    def send_to_all_users(self, user_ids, message, image_url):
        """複数ユーザーにメッセージと画像を送信"""
        success = True
        for user_id in user_ids:
            if not self.send_message_with_image(user_id, message, image_url):
                success = False
                logger.warning(f"Failed to send message to {user_id}")
        return success

def load_latest_data(data_dir="./data/weather_data"):
    """最新のデータをJSONから読み込む"""
    try:
        filepath = os.path.join(data_dir, "latest_data.json")
        if not os.path.exists(filepath):
            logger.error(f"Latest data file not found: {filepath}")
            return None
            
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        return data
        
    except Exception as e:
        logger.error(f"Error loading latest data: {str(e)}", exc_info=True)
        return None

def main():
    # 環境変数の読み込み
    load_dotenv()
    
    # LINE APIトークン
    line_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    if not line_token:
        logger.error("LINE_CHANNEL_ACCESS_TOKEN not set in environment variables")
        return
        
    # LINE ユーザーID
    line_user_ids_str = os.getenv('LINE_USER_IDS', '')
    line_user_ids = [user_id.strip() for user_id in line_user_ids_str.split(',') if user_id.strip()]
    if not line_user_ids:
        logger.error("LINE_USER_IDS not set in environment variables")
        return
    
    # GitHubの情報
    github_username = os.getenv('GITHUB_USERNAME', 'Rioto3')
    github_repo = os.getenv('GITHUB_REPO', 'izumigatake-snow')
    github_branch = os.getenv('main')
    
    if not github_username or not github_repo:
        logger.error("GitHub configuration not set in environment variables")
        return
    
    # 最新データの読み込み
    data = load_latest_data()
    if not data:
        logger.error("Failed to load latest data")
        return
    
    # 画像のURL作成
    image_rel_path = os.path.relpath(data['image_path'], './')
    image_url = f"https://github.com/Rioto3/izumigatake-snow-monitoring/blob/main/data/images/full_screenshot.png?raw=true"
    
    
    # メッセージ作成
    message = (
        f"ほれい！雪積もってるか？？"
    )
    
    # メッセージ送信
    messenger = LineMessenger(line_token)
    success = messenger.send_to_all_users(line_user_ids, message, image_url)
    
    if success:
        print(f"LINE通知送信完了: {len(line_user_ids)}ユーザー")
    else:
        print("LINE通知の送信に一部失敗しました。ログを確認してください。")

if __name__ == "__main__":
    main()