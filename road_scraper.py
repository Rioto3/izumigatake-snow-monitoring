import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image
import io
import json

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraping.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("road_monitor")

class RoadConditionScraper:
    def __init__(self, url, save_dir="./data"):
        self.url = url
        self.save_dir = save_dir
        self.image_save_dir = os.path.join(save_dir, "images")
        self.data_save_dir = os.path.join(save_dir, "weather_data")
        
        # 切り取りパラメータのデフォルト値
        
        # ディレクトリがなければ作成
        for directory in [self.save_dir, self.image_save_dir, self.data_save_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
        
    def scrape(self):
        try:
            logger.info(f"Scraping started: {self.url}")
            
            # ページの取得
            response = requests.get(self.url)
            response.encoding = 'shift_jis'
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch page: {response.status_code}")
                return None
            
            # BeautifulSoupでHTMLを解析
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 日時情報の取得
            date_time_text = soup.find(string=re.compile(r'\d+月\d+日\s+\d+時\d+分の気象状況'))
            if date_time_text:
                date_time = date_time_text.strip()
                logger.info(f"Found date and time: {date_time}")
            else:
                date_time = datetime.now().strftime("%m月%d日 %H時%M分の気象状況")
                logger.warning(f"Date and time not found, using current time: {date_time}")
            
            # 気温の取得
            temp_elem = soup.find('font', string=re.compile(r'気温：.*℃'))
            if temp_elem:
                temp = re.search(r'気温：([-\d.]+)℃', temp_elem.text).group(1)
                logger.info(f"Found temperature: {temp}°C")
            else:
                temp = "N/A"
                logger.warning("Temperature not found")
            
            # 路面温度の取得
            road_temp_elem = soup.find('font', string=re.compile(r'路面温度：.*℃'))
            if road_temp_elem:
                road_temp = re.search(r'路面温度：([-\d.]+)℃', road_temp_elem.text).group(1)
                logger.info(f"Found road temperature: {road_temp}°C")
            else:
                road_temp = "N/A"
                logger.warning("Road temperature not found")
            
            # 指定された座標で画像をキャプチャ
            image_path = self.capture_custom_crop()
            
            # データを保存
            self.save_weather_data(date_time, temp, road_temp, image_path)
            
            # 最新データをJSONとして保存（LINE通知用）
            self.save_latest_data(date_time, temp, road_temp, image_path)
            
            data = {
                "date_time": date_time,
                "temperature": temp,
                "road_temperature": road_temp,
                "image_path": image_path
            }
            
            return data
            
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}", exc_info=True)
            return None
        
    def capture_custom_crop(self):
        try:
            logger.info("Capturing full screenshot")
            
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=800,600")
            
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                driver.get(self.url)
                time.sleep(3)
                
                # 全画面スクリーンショットを保存
                screenshot = driver.get_screenshot_as_png()
                full_img = Image.open(io.BytesIO(screenshot))
                
                # デバッグ用に全画面を保存
                full_path = os.path.join(self.image_save_dir, "full_screenshot.png")
                full_img.save(full_path)
                logger.info(f"Full screenshot saved to: {full_path}")
                
                # 切り取り
                left = 472
                top = 0
                width = 655
                height = 376
                
                img = full_img.crop((left, top, left+width, top+height))
                
                # 固定ファイル名で保存
                filepath = os.path.join(self.image_save_dir, "road_condition.png")
                img.save(filepath)
                logger.info(f"Cropped image saved to: {filepath}")
                return filepath
                
            finally:
                driver.quit()
                    
        except Exception as e:
            logger.error(f"Error capturing screenshot: {str(e)}", exc_info=True)
            return None
    def save_weather_data(self, date_time, temp, road_temp, image_path=None):
        try:
            # ファイル名の生成（日付ごと）
            today = datetime.now().strftime("%Y%m%d")
            filepath = os.path.join(self.data_save_dir, f"weather_data_{today}.csv")
            
            # ファイルが存在しない場合はヘッダーを書き込む
            file_exists = os.path.isfile(filepath)
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(filepath, 'a', encoding='utf-8') as f:
                if not file_exists:
                    f.write("timestamp,original_date_time,temperature,road_temperature,image_path\n")
                f.write(f'"{timestamp}","{date_time}","{temp}","{road_temp}","{image_path or ""}"\n')
            
            logger.info(f"Weather data saved to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving weather data: {str(e)}", exc_info=True)
            return None
    
    def save_latest_data(self, date_time, temp, road_temp, image_path):
        """最新データをJSON形式で保存（LINE通知用）"""
        try:
            data = {
                "date_time": date_time,
                "temperature": temp,
                "road_temperature": road_temp,
                "image_path": image_path,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            filepath = os.path.join(self.data_save_dir, "latest_data.json")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Latest data saved to: {filepath}")
            return filepath
                
        except Exception as e:
            logger.error(f"Error saving latest data: {str(e)}", exc_info=True)
            return None

def main():
    url = "https://micos-sa.jwa.or.jp/tohoku/sendaishi_romen/real/v0006.html"

    
    # スクレイパーの初期化
    scraper = RoadConditionScraper(url)
    data = scraper.scrape()
    
    if data:
        print(f"スクレイピング完了: {data['date_time']}")
        print(f"気温: {data['temperature']}°C, 路面温度: {data['road_temperature']}°C")
        print(f"画像: {data['image_path']}")
    else:
        print("スクレイピングに失敗しました。ログを確認してください。")

if __name__ == "__main__":
    main()