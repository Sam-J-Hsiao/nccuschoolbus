from flask import Flask, render_template
import requests
import time
import html
import math

app = Flask(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'http://nccu.5284.com.tw/MQS/routeinfo.jsp?rid=16447',
    'X-Requested-With': 'XMLHttpRequest'
}

TTE_MAP = {
    '0': '進站中', '': '未發車', '-1': '未發車', 
    '-2': '交管不停', '-3': '末班已過', '-4': '今日未營運'
}

# 直接將政大2路的站牌 ID 與名稱寫死，不再依賴即時爬取 HTML
STATIC_STOPS_MAP = {
    "129749": "行政大樓",
    "129750": "百年樓",
    "127378": "藝文中心",
    "127376": "好漢坡",
    "215373": "自強一二三舍",
    "181248": "山居學習中心",
    "205983": "自強十舍",
    "205507": "研創中心",
    "205506": "六期運動場",
    "205508": "研創中心",
    "181249": "好漢坡",
    "181250": "藝文中心",
    "181251": "百年樓",
    "181252": "行政大樓"
}

def fetch_bus_data(route_id):
    """獲取動態資料並整理成去程與返程的列表"""
    current_timestamp = int(time.time() * 1000)
    url = f"http://nccu.5284.com.tw/MQS/RouteDyna?routeid={route_id}&nocache={current_timestamp}"
    
    go_stops = []
    back_stops = []
    update_time = ""

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        
        # 處理更新時間，只取時分秒部分
        raw_time = html.unescape(data.get('UpdateTime', ''))
        update_time = raw_time.split(' ')[1] if ' ' in raw_time else raw_time
        
        stops = data.get('Stop', [])
        
        for index, stop in enumerate(stops):
            n1_raw = stop.get('n1')
            if not n1_raw: continue
            
            arr_n1 = n1_raw.split(',')
            if len(arr_n1) < 8: continue
            
            stop_id = arr_n1[1]
            status_code = arr_n1[7]
            
            # 直接從我們寫死的字典中取得站牌名稱
            stop_name = STATIC_STOPS_MAP.get(stop_id, f"未知站牌({stop_id})")
            
            # 狀態判斷邏輯
            if status_code in TTE_MAP:
                status_text = TTE_MAP[status_code]
            else:
                tte = int(status_code)
                if 0 < tte < 180:
                    status_text = "將到站"
                else:
                    minutes = math.floor(tte / 60)
                    status_text = f"{minutes}分"

            stop_data = {'name': stop_name, 'status': status_text}
            
            # 根據陣列索引區分去程與返程 (前9站為去程，後5站為返程)
            if index < 9:
                go_stops.append(stop_data)
            else:
                back_stops.append(stop_data)
                
        return update_time, go_stops, back_stops
        
    except Exception as e:
        print(f"取得動態資料失敗: {e}")
        return "錯誤", [], []

# Flask 路由設定
@app.route('/')
def index():
    route_id = "16447" # 政大2路
    
    # 獲取即時動態 (不再需要傳入 stops_map)
    update_time, go_stops, back_stops = fetch_bus_data(route_id)
    
    # 將資料傳遞給 HTML 樣板進行渲染
    return render_template(
        'index.html', 
        update_time=update_time, 
        go_stops=go_stops, 
        back_stops=back_stops
    )

if __name__ == '__main__':
    # 啟動開發伺服器
    app.run(debug=True, port=5000)
