# -*- coding: utf-8 -*-
"""
极简修复版 Markdown + LaTeX 公式渲染组件。
针对 QWebEngineView 在 Windows 下“滑动不实时刷新”问题进行全方位排查与修复。
"""

from __future__ import annotations

import json
import re
import sys
import markdown
from PyQt5.QtCore import Qt, QUrl, QTimer, QEvent
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QSizePolicy, QHBoxLayout, QPushButton
from PyQt5.QtWebEngineWidgets import QWebEngineView

# 第四优先级：做成可开关的原生窗口属性
USE_NATIVE_WEBENGINE_WINDOW = False

# --- 第六、七优先级：基于内部滚动容器的 HTML 模板 ---
BASE_HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script>
    window.MathJax = {{
        tex: {{
            inlineMath: [['\\(', '\\)']],
            displayMath: [['\\[', '\\]']],
            processEscapes: true,
            packages: {{'[+]': ['ams']}}
        }},
        options: {{ enableMenu: false }},
        svg: {{ fontCache: 'global' }},
        startup: {{ typeset: false }}
    }};
    </script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
    <style>
        :root {{
            --bg-color: {bg_color};
            --text-color: {text_color};
            --code-bg: {code_bg};
            --border-color: {border_color};
            --blockquote-bg: {blockquote_bg};
            --user-bg: {user_bg};
            --user-border: {user_border};
        }}
        html, body {{
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%; /* 禁止外层滚动 */
            overflow: hidden;
            background-color: var(--bg-color);
        }}
        
        /* 第六优先级：统一只让内部容器滚动 */
        #scroll-container {{
            width: 100%;
            height: 100vh;
            overflow-y: auto;
            overflow-x: hidden;
            box-sizing: border-box;
            background: var(--bg-color);
        }}
        
        #content {{
            box-sizing: border-box;
            padding: 16px 20px 28px 20px;
            min-height: 100%;
        }}
        
        body {{
            font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", Arial, sans-serif;
            font-size: 17px;
            line-height: 1.75;
            color: var(--text-color);
        }}
        
        .message {{
            margin-bottom: 20px;
            padding: 12px 16px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            box-sizing: border-box;
            max-width: 100%;
            overflow-wrap: break-word;
            word-break: break-word;
        }}
        
        .message.user {{ background: var(--user-bg); border-color: var(--user-border); margin-left: 5%; }}
        .message.assistant {{ background: var(--bg-color); margin-right: 5%; }}
        .message.system {{ background: var(--blockquote-bg); color: #ef4444; font-size: 0.9em; text-align: center; border-style: dashed; }}
        
        pre {{ background-color: var(--code-bg); padding: 14px; border-radius: 8px; overflow-x: auto; border: 1px solid var(--border-color); }}
        code {{ font-family: "Cascadia Code", "Consolas", monospace; font-size: 0.9em; }}
        table {{ border-collapse: collapse; max-width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid var(--border-color); padding: 8px 12px; }}
        
        mjx-container {{ max-width: 100%; overflow-x: auto; overflow-y: hidden; outline: none !important; }}
    </style>
</head>
<body>
    <div id="scroll-container">
        <div id="content"></div>
    </div>
    <script>
        // 第七优先级：主动拦截 wheel 并驱动容器滚动
        document.addEventListener('wheel', function(e) {{
            const scroller = document.getElementById('scroll-container');
            if (!scroller) return;

            scroller.scrollTop += e.deltaY;

            requestAnimationFrame(function() {{
                scroller.offsetHeight; // force reflow
                scroller.dispatchEvent(new Event('scroll'));
                window.dispatchEvent(new Event('resize'));
            }});
            e.preventDefault(); // 阻止默认双重滚动
        }}, {{ passive: false }});
    </script>
</body>
</html>
"""

THEMES = {
    "light": {
        "bg_color": "#ffffff", "text_color": "#111827", "code_bg": "#f3f4f6", 
        "border_color": "#e5e7eb", "blockquote_bg": "#f9fafb", "user_bg": "#eff6ff", "user_border": "#bfdbfe"
    },
    "dark": {
        "bg_color": "#0f172a", "text_color": "#f1f5f9", "code_bg": "#1e293b", 
        "border_color": "#334155", "blockquote_bg": "#1e293b", "user_bg": "#1e293b", "user_border": "#3b82f6"
    }
}

def protect_math(md_text: str) -> tuple[str, list[str]]:
    math_blocks = []
    def repl(match):
        math_blocks.append(match.group(0))
        return f"@@MATH_BLOCK_{len(math_blocks) - 1}@@"
    pattern = r"(\\\[.*?\\\]|\\\(.*?\\\))"
    protected = re.sub(pattern, repl, md_text, flags=re.DOTALL)
    return protected, math_blocks

def restore_math(html: str, math_blocks: list[str]) -> str:
    for i, formula in enumerate(math_blocks):
        html = html.replace(f"@@MATH_BLOCK_{i}@@", formula)
    return html

def md_to_html(md_text: str) -> str:
    protected, math_blocks = protect_math(md_text)
    body = markdown.markdown(protected, extensions=["extra", "tables", "fenced_code", "sane_lists"], output_format="html5")
    return restore_math(body, math_blocks)

class MarkdownFormulaViewer(QWidget):
    def __init__(self, parent=None, theme="light"):
        super().__init__(parent)
        self._theme = theme
        self._page_ready = False
        self._pending_messages = []
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.web_view = QWebEngineView(self)
        
        # 第四优先级：朴素设置，移除可能破坏刷新链路的属性
        self.web_view.setUpdatesEnabled(True)
        self.web_view.setVisible(True)
        self.web_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        if USE_NATIVE_WEBENGINE_WINDOW:
            self.web_view.setAttribute(Qt.WA_NativeWindow, True)
            self.web_view.setAttribute(Qt.WA_DontCreateNativeAncestors, False)
            
        self.web_view.setContextMenuPolicy(Qt.NoContextMenu)
        self.web_view.loadFinished.connect(self._on_load_finished)
        
        # 第八优先级：使用纯色不透明背景
        self.setStyleSheet("background: white;")
        self.web_view.setStyleSheet("background: white;")
        self.web_view.page().setBackgroundColor(QColor("#ffffff"))
        
        # 第五优先级：安装事件过滤器进行滚轮调试
        self.web_view.installEventFilter(self)
        
        layout.addWidget(self.web_view, 1) # stretch=1
        
        # 兜底：鼠标悬停或追加消息时触发的 Watchdog
        self.repaint_timer = QTimer(self)
        self.repaint_timer.setInterval(150)
        self.repaint_timer.timeout.connect(self._tick_repaint)
        
        self._init_page()

    def eventFilter(self, obj, event):
        if obj is self.web_view and event.type() == QEvent.Wheel:
            print("[Debug] Wheel event reached QWebEngineView")
            self._start_temp_watchdog(1000)
            
            # 第五优先级：检测 JS 内部的滚动状态
            QTimer.singleShot(50, self.debug_scroll_state)
            QTimer.singleShot(150, self.debug_scroll_state)
            
        return super().eventFilter(obj, event)

    def debug_scroll_state(self):
        if not self._page_ready: return
        self.web_view.page().runJavaScript("""
        ({
          scrollerTop: document.getElementById('scroll-container') ? document.getElementById('scroll-container').scrollTop : -1,
          bodyScrollHeight: document.body.scrollHeight,
          docScrollHeight: document.documentElement.scrollHeight,
          innerHeight: window.innerHeight,
          activeElement: document.activeElement ? document.activeElement.tagName : null
        })
        """, lambda res: print("WEB_SCROLL_STATE:", res))

    def _init_page(self):
        self._page_ready = False
        theme_vars = THEMES.get(self._theme, THEMES["light"])
        html = BASE_HTML_TEMPLATE.format(**theme_vars)
        self.web_view.setHtml(html, QUrl("https://cdn.jsdelivr.net/"))

    def append_markdown(self, md_text: str, role: str = "assistant", scroll: bool = True):
        html_body = md_to_html(md_text)
        if not self._page_ready:
            self._pending_messages.append((html_body, role, scroll))
            return
        self._append_html_to_page(html_body, role, scroll)
        self._start_temp_watchdog(2000)

    def set_markdown(self, md_text: str):
        self.clear()
        if "---" in md_text:
            parts = md_text.split("---")
            for part in parts:
                p = part.strip()
                if not p: continue
                role = "user" if "👤" in p else ("assistant" if "🤖" in p else "system")
                clean_p = p.replace("### 👤 我\n", "").replace("### 🤖 AI 助教\n", "").replace("> ❌ ", "")
                self.append_markdown(clean_p, role=role, scroll=False)
            self._run_js("const s = document.getElementById('scroll-container'); if(s) s.scrollTop = s.scrollHeight;")
        else:
            self.append_markdown(md_text, scroll=True)

    def clear(self):
        self._run_js("document.getElementById('content').innerHTML = '';")

    def set_theme(self, theme: str):
        if theme in THEMES:
            self._theme = theme
            self._init_page()

    def force_refresh(self):
        self.web_view.page().runJavaScript("""
        (function() {
            const scroller = document.getElementById('scroll-container');
            if (scroller) {
                scroller.offsetHeight;
                scroller.dispatchEvent(new Event('scroll'));
            }
            window.dispatchEvent(new Event('resize'));
            document.body && document.body.offsetHeight;
        })();
        """)
        self.web_view.update()
        self.web_view.repaint()

    def _append_html_to_page(self, html_body: str, role: str, scroll: bool):
        html_json = json.dumps(html_body, ensure_ascii=False)
        role_json = json.dumps(role, ensure_ascii=False)
        js = f"""
        (function() {{
            const html = {html_json};
            const role = {role_json};
            const content = document.getElementById('content');
            const wrapper = document.createElement('div');
            wrapper.className = 'message ' + role;
            wrapper.innerHTML = html;
            content.appendChild(wrapper);

            function scrollBottom() {{
                const scroller = document.getElementById('scroll-container');
                if (scroller) {{
                    scroller.scrollTop = scroller.scrollHeight;
                    // 强制刷新
                    scroller.style.transform = 'translateZ(0)';
                    scroller.offsetHeight;
                    scroller.dispatchEvent(new Event('scroll'));
                    window.dispatchEvent(new Event('resize'));
                }}
            }}

            if (window.MathJax && MathJax.typesetPromise) {{
                MathJax.typesetPromise([wrapper]).then(() => {{
                    requestAnimationFrame(() => {{
                        if ({'true' if scroll else 'false'}) scrollBottom();
                    }});
                }});
            }} else {{
                if ({'true' if scroll else 'false'}) scrollBottom();
            }}
        }})();
        """
        self._run_js(js)

    def _tick_repaint(self):
        if not self.isVisible(): return
        self.web_view.page().runJavaScript(
            "window.dispatchEvent(new Event('resize')); document.body && document.body.offsetHeight;"
        )
        self.web_view.update()
        self.web_view.repaint()

    def _start_temp_watchdog(self, ms: int):
        self.repaint_timer.start()
        QTimer.singleShot(ms, self.repaint_timer.stop)

    def _run_js(self, js: str):
        if self._page_ready:
            self.web_view.page().runJavaScript(js)

    def _on_load_finished(self, ok: bool):
        self._page_ready = ok
        if ok:
            for item in self._pending_messages:
                self._append_html_to_page(*item)
            self._pending_messages.clear()
            self.web_view.update()
