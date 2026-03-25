import os
import requests
import time
from googletrans import Translator

# ================= 安全配置区 =================
# 从 GitHub Secrets 中自动读取密钥
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
PUSHPLUS_TOKEN = os.getenv('PUSHPLUS_TOKEN')
# ============================================

translator = Translator()

def translate_text(text):
    """翻译函数：将英文翻译为中文"""
    if not text or len(text.strip()) == 0:
        return "暂无摘要内容"
    try:
        # 尝试翻译，dest='zh-cn' 表示目标语言为简体中文
        # 使用 3.1.0a0 版本的 googletrans 比较稳定
        result = translator.translate(text, dest='zh-cn')
        return result.text
    except Exception as e:
        print(f"翻译出错: {e}")
        return text # 翻译失败则返回原文

def get_news_data(category, count=8):
    """获取指定类目的全球新闻（建议 count 设置为 8 以防内容过大）"""
    print(f"🚀 正在抓取 {category} 类目新闻...")
    url = f"https://newsapi.org/v2/top-headlines?category={category}&language=en&pageSize={count}&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(url, timeout=20)
        return response.json().get('articles', [])
    except Exception as e:
        print(f"获取新闻失败: {e}")
        return []

def format_news_section(articles, section_title):
    """格式化新闻板块：标题(中) + 摘要(中) + 链接"""
    html = f"<h2 style='color: #2c3e50; border-left: 5px solid #3498db; padding-left: 10px; margin-top: 30px;'>🌟 {section_title}</h2>"
    
    if not articles:
        return html + "<p>未能获取到相关新闻，请检查 API 状态。</p>"

    for i, art in enumerate(articles):
        # 翻译标题和摘要
        title_cn = translate_text(art.get('title', '无标题'))
        desc_cn = translate_text(art.get('description', '作者未提供内容摘要'))
        
        # 组装 HTML
        html += f"""
        <div style='margin-bottom: 20px; border-bottom: 1px dashed #eee; padding-bottom: 15px;'>
            <div style='font-weight: bold; font-size: 16px; color: #333;'>{i+1}. {title_cn}</div>
            <p style='font-size: 14px; color: #666; margin-top: 5px; line-height: 1.5;'><b>简要内容：</b>{desc_cn}</p>
            <a href='{art['url']}' style='color: #3498db; text-decoration: none; font-size: 13px;'>🔗 查看原文 (English)</a>
        </div>
        """
        # 控制频率，防止请求过快
        time.sleep(0.4)
        print(f"已处理 {section_title} 第 {i+1} 条...")
        
    return html

def get_daily_quote():
    """获取雅思每日金句（助力子超的语言提升）"""
    try:
        # 使用励志语录 API
        res = requests.get("https://api.quotable.io/random?tags=inspirational", timeout=5).json()
        en = res['content']
        cn = translate_text(en)
        return f"<div style='background: #f1f9ff; padding: 15px; border-radius: 8px; margin-bottom: 20px;'><b>💡 IELTS 每日金句：</b><br><i style='color: #555;'>{en}</i><br><span style='color: #2c3e50;'>{cn}</span></div>"
    except:
        return ""

def main():
    start_time = time.time()