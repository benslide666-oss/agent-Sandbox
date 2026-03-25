import os
import requests
import time
from googletrans import Translator

# ================= 配置区 =================
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
PUSHPLUS_TOKEN = os.getenv('PUSHPLUS_TOKEN')
# ==========================================

translator = Translator()

def translate_text(text):
    """翻译函数"""
    if not text: return "No content"
    try:
        return translator.translate(text, dest='zh-cn').text
    except:
        return text

def get_bbc_news(count=5):
    """专门抓取 BBC News 的新闻源"""
    print("🚀 正在抓取 BBC News...")
    # 注意这里使用了 sources=bbc-news
    url = f"https://newsapi.org/v2/top-headlines?sources=bbc-news&apiKey={NEWS_API_KEY}"
    try:
        res = requests.get(url, timeout=15).json()
        return res.get('articles', [])[:count] # 只要前 count 条
    except:
        return []

def format_bbc_section(articles):
    """针对雅思学习优化的 BBC 排版"""
    html = "<h2 style='color: #b71c1c; border-left: 5px solid #b71c1c; padding-left: 10px;'>🇬🇧 BBC World News (IELTS Prep)</h2>"
    
    for i, art in enumerate(articles):
        en_title = art.get('title', '')
        cn_title = translate_text(en_title)
        en_desc = art.get('description', '')
        cn_desc = translate_text(en_desc)
        
        html += f"""
        <div style='margin-bottom: 25px; background: #fdfdfd; padding: 10px; border: 1px solid #eee;'>
            <div style='font-weight: bold; font-size: 15px; color: #000;'>{i+1}. {en_title}</div>
            <div style='font-size: 14px; color: #555; margin-top: 4px;'>{cn_title}</div>
            <p style='font-size: 13px; color: #666; font-style: italic; margin-top: 10px;'>
                <b>Summary:</b> {en_desc}<br>
                <span style='color: #888;'><b>中文摘要：</b>{cn_desc}</span>
            </p>
            <a href='{art['url']}' style='color: #b71c1c; text-decoration: none; font-size: 12px;'>📖 Read Full Article</a>
        </div>
        """
        time.sleep(0.5) # 防止翻译请求过快
    return html

def main():
    # 1. 获取 BBC 新闻
    bbc_articles = get_bbc_news(5) # 每天看 5 条最地道的英语新闻
    if not bbc_articles:
        print("未能抓取到 BBC 新闻")
        return

    # 2. 构造内容
    header = f"<h1 style='text-align: center;'>子超，早安！</h1>"
    header += f"<p style='text-align: center; color: #888;'>{time.strftime('%Y-%m-%d')} BBC 英语精选</p>"
    
    bbc_html = format_bbc_section(bbc_articles)
    full_content = header + bbc_html

    # 3. 推送
    print("📨 正在推送至微信...")
    payload = {
        "token": PUSHPLUS_TOKEN,
        "title": "🇬🇧 今日 BBC 英语新闻精选",
        "content": full_content,
        "template": "html"
    }
    res = requests.post('http://www.pushplus.plus/send', json=payload)
    print(f"✅ 完成！响应: {res.text}")

if __name__ == "__main__":
    main()