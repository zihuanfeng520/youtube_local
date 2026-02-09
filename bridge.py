import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import sys

# 設定埠號 (可以自己改)
PORT = 8080

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        # 處理瀏覽器的預檢請求 (CORS Preflight)
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Youtube-Client-Name, X-Youtube-Client-Version, X-Goog-Visitor-Id')
        self.end_headers()

    def do_POST(self):
        # 1. 讀取網頁發來的請求
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        # 2. 解析目標網址 (我們約定把目標網址放在 URL 的 query 裡，例如 /?url=...)
        # 但為了簡單，我們直接固定轉發給 YouTube
        target_url = "https://www.youtube.com/youtubei/v1" + self.path
        
        print(f"🔄 [本地轉發] -> {self.path}")

        try:
            # 3. 幫你向 YouTube 發送請求 (Python 沒有 CORS 限制！)
            req = urllib.request.Request(
                target_url, 
                data=post_data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "X-Youtube-Client-Name": "3",
                    "X-Youtube-Client-Version": "19.29.35"
                }
            )
            
            with urllib.request.urlopen(req) as response:
                resp_data = response.read()
                
                # 4. 把 YouTube 的回應傳回給你的 HTML
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*') # 這行是關鍵！騙瀏覽器說是合法的
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(resp_data)
                
        except Exception as e:
            print(f"❌ 錯誤: {e}")
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(str(e).encode())

print(f"🚀 NewPipe 本地橋接器已啟動！")
print(f"📡 監聽地址: http://localhost:{PORT}")
print(f"👉 請不要關閉這個視窗，現在去打開你的 HTML 吧！")

# 允許位址重用，防止重啟時報錯
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), ProxyHandler) as httpd:
    httpd.serve_forever()