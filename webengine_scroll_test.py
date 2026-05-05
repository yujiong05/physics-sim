# -*- coding: utf-8 -*-
"""
最小复现 Demo：验证 QWebEngineView 在长文本追加和滚动时的刷新情况。
"""

import os
import sys
import json
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtWebEngineWidgets import QWebEngineView

# 【重要测试开关】
# 测试时不依赖任何特殊 OpenGL 属性，只禁用 Chromium GPU，看是否依然不刷新。
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--disable-gpu "
    "--disable-gpu-compositing "
    "--disable-accelerated-2d-canvas "
    "--disable-features=CalculateNativeWinOcclusion,VizDisplayCompositor "
    "--enable-begin-frame-control"
)

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        html, body {
            margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background: #ffffff;
        }
        #scroll-container {
            width: 100%; height: 100vh; overflow-y: auto; overflow-x: hidden; box-sizing: border-box;
        }
        #content {
            padding: 20px; box-sizing: border-box; min-height: 100%; font-family: sans-serif;
        }
        .msg {
            margin-bottom: 15px; padding: 15px; background: #f3f4f6; border-radius: 8px;
        }
    </style>
</head>
<body>
    <div id="scroll-container">
        <div id="content"></div>
    </div>
    <script>
        document.addEventListener('wheel', function(e) {
            const scroller = document.getElementById('scroll-container');
            if(scroller) {
                scroller.scrollTop += e.deltaY;
                requestAnimationFrame(() => {
                    scroller.offsetHeight;
                    scroller.dispatchEvent(new Event('scroll'));
                    window.dispatchEvent(new Event('resize'));
                });
            }
            e.preventDefault();
        }, { passive: false });
    </script>
</body>
</html>
"""

class MinimalWebViewer(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.web_view = QWebEngineView(self)
        self.web_view.setUpdatesEnabled(True)
        self.web_view.loadFinished.connect(self.on_load)
        layout.addWidget(self.web_view, 1)
        
        self.web_view.setHtml(HTML_TEMPLATE, QUrl("https://cdn.jsdelivr.net/"))
        self.counter = 0

    def on_load(self, ok):
        if ok:
            print("Page loaded.")

    def add_message(self):
        self.counter += 1
        text = f"这是第 {self.counter} 条测试消息。<br>" * 10
        js = f"""
        (function() {{
            const div = document.createElement('div');
            div.className = 'msg';
            div.innerHTML = {json.dumps(text)};
            const scroller = document.getElementById('scroll-container');
            document.getElementById('content').appendChild(div);
            
            if(scroller) {{
                scroller.scrollTop = scroller.scrollHeight;
                scroller.style.transform = 'translateZ(0)';
                scroller.offsetHeight;
            }}
        }})();
        """
        self.web_view.page().runJavaScript(js)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(500, 600)
        
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        
        self.viewer = MinimalWebViewer()
        layout.addWidget(self.viewer, 1)
        
        btn = QPushButton("追加消息并滚动到底部")
        btn.clicked.connect(self.viewer.add_message)
        layout.addWidget(btn)
        
        self.setCentralWidget(main_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
