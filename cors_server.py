#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""带 CORS 头的静态文件服务器(用于向浏览器提供测试图片)"""
import http.server
import socketserver
import os

PORT = 8890
ROOT = "/home/z/my-project/github-hot-heybox"


class CORSHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        # Chrome Private Network Access 必需
        self.send_header("Access-Control-Allow-Private-Network", "true")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()


if __name__ == "__main__":
    os.chdir(ROOT)
    with socketserver.TCPServer(("0.0.0.0", PORT), CORSHandler) as httpd:
        print(f"serving at http://0.0.0.0:{PORT} with CORS")
        httpd.serve_forever()
