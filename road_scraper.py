import requests

url = "https://render-fastapi-b76g.onrender.com/api/v1/ffmpeg/capture_stream_screenshot"
params = {
    "url": "https://micos-sa.jwa.or.jp/tohoku/sendaishi_romen/real/camera/0006.m3u8",
    "output_file": "full_screenshot.png"
}

response = requests.get(url, params=params)

if response.status_code == 200:
    # 画像として保存
    with open("./data/images/full_screenshot.png", "wb") as f:
        f.write(response.content)
    print("スクリーンショット取得成功")
else:
    print(f"エラー: {response.status_code}")
    print(response.text)