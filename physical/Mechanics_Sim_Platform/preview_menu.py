# -*- coding: utf-8 -*-
"""
主菜单预览 Demo
"""

import sys
import os

# 确保可以导入项目中的模块
platform_dir = os.path.dirname(os.path.abspath(__file__))
if platform_dir not in sys.path:
    sys.path.insert(0, platform_dir)

from PyQt5.QtWidgets import QApplication, QMainWindow
from ui.pages.page_menu import HomePage

class DemoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("主菜单 UI 预览")
        self.resize(1120, 720)
        
        self.home_page = HomePage()
        self.setCentralWidget(self.home_page)
        
        # 打印点击的路由
        self.home_page.route_selected.connect(lambda r: print(f"Selected route: {r}"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 使用 Fusion 样式获得更一致的跨平台外观
    app.setStyle("Fusion")
    
    demo = DemoWindow()
    demo.show()
    sys.exit(app.exec_())
