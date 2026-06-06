#!/usr/bin/env python
"""
PWA 本地服务器
启动后手机连接同一 WiFi，扫码或输入地址即可打开。
"""

import http.server
import socketserver
import socket
import os
import sys

PORT = 8080

# 切换到 pwa 目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 如果没有图标，生成简单的 PNG 图标
def ensure_icons():
    for size in [192, 512]:
        fname = f'icon-{size}.png'
        if not os.path.exists(fname):
            try:
                from PIL import Image, ImageDraw, ImageFont
                img = Image.new('RGB', (size, size), '#1a73e8')
                draw = ImageDraw.Draw(img)
                # 画闪电符号
                draw.rectangle([size*0.3, size*0.1, size*0.7, size*0.55], fill='#ffd600')
                draw.polygon([
                    (size*0.35, size*0.55), (size*0.2, size*0.9),
                    (size*0.5, size*0.55), (size*0.55, size*0.55),
                    (size*0.65, size*0.1), (size*0.5, size*0.45),
                ], fill='#1a73e8')
                img.save(fname, 'PNG')
                print(f'Created {fname}')
            except ImportError:
                # PIL not available, create minimal PNG
                create_minimal_png(fname, size)

def create_minimal_png(fname, size):
    """用纯 Python 创建最简 PNG"""
    import struct, zlib

    def chunk(ctype, data):
        c = ctype + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0))

    # 蓝色背景 + 黄色闪电形状
    raw = b''
    for y in range(size):
        raw += b'\x00'  # filter none
        for x in range(size):
            # Blue BG, Yellow lightning in center
            cx, cy = x - size/2, y - size/2
            in_lightning = (abs(cx) < size*0.15 and cy < size*0.2 and cy > -size*0.45)
            if in_lightning:
                raw += b'\xff\xd6\x00'  # Yellow
            else:
                raw += b'\x1a\x73\xe8'  # Blue

    idat = chunk(b'IDAT', zlib.compress(raw))
    iend = chunk(b'IEND', b'')

    with open(fname, 'wb') as f:
        f.write(sig + ihdr + idat + iend)
    print(f'Created {fname} ({size}x{size})')


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]
    finally:
        s.close()


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress logs


if __name__ == '__main__':
    ensure_icons()

    ip = get_local_ip()
    print()
    print('='*55)
    print('  PWA 电气计算工具 - 本地服务器')
    print('='*55)
    print()
    print(f'  手机扫码或浏览器打开:')
    print(f'  ==>  http://{ip}:{PORT}  <==')
    print()
    print('  添加到桌面:')
    print('  - Android Chrome: 菜单 -> 添加到主屏幕')
    print('  - iPhone Safari:  分享 -> 添加到主屏幕')
    print()
    print('  按 Ctrl+C 停止服务器')
    print('='*55)

    with socketserver.TCPServer(("0.0.0.0", PORT), QuietHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n服务器已停止')
