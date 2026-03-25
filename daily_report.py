import os
import requests
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from googletrans import Translator

# ================= 配置区 =================
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_RECEIVER = os.getenv('EMAIL_RECEIVER')
# ==========================================

translator = Translator()

def translate_text(text):
    if not text: return "无内容"
    try:
        return translator.translate(text, dest='zh-cn').text
    except:
        return text

def get_news(query=None, count=30, category='general'):
    """获取新闻：支持全球热门或关键词搜索"""
    print(f"🚀 正在获取新闻 (Query: {query if query else category})...")
    if query:
        # 搜索特定关键词（如镇江）
        url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&pageSize={count}&apiKey={NEWS_API_KEY}"
    else:
        # 获取全球头条
        url = f"https://newsapi.org/v2/top-headlines?language=en&pageSize={count}&apiKey={NEWS_API_KEY}"
    
    try:
        res = requests.get(url, timeout=20).json()
        return res.get('articles', [])
    except:
        return []

def format_section(articles, title):
    """格式化新闻板块"""
    html = f"<h2 style='color: #2c3e50; border-left: 5px solid #3498db; padding-left: 10px;'>{title}</h2>"
    if not articles:
        html += "<p>暂无更新</p>"
        return html
    
    for i, art in enumerate(articles):
        en_title = art.get('title', 'No Title')
        cn_title = translate_text(en_title)
        html += f"""
        <div style='margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px;'>
            <div style='font-weight: bold; color: #333;'>{i+1}. {cn_title}</div>
            <div style='font-size: 12px; color: #999; margin-top: 5px;'>英文原题: {en_title}</div>
            <a href='{art['url']}' style='color: #3498db; font-size: 12px; text-decoration: none;'>查看原文 →</a>
        </div>
        """
        if (i+1) % 5 == 0: time.sleep(1) # 减缓翻译频率，防止被封
    return html

def main():
    start_time = time.time()
    
    # 1. 获取 30 条全球新闻
    global_articles = get_news(count=30)
    # 2. 获取 10 条镇江本地新闻 (搜索关键词: Zhenjiang)
    local_articles = get_news(query='Zhenjiang', count=10)

    # 3. 构造 HTML 邮件
    header = f"""
    <div style='max-width: 650px; margin: auto; font-family: sans-serif;'>
        <div style='background: #3498db; color: white; padding: 20px; text-align: center; border-radius: 10px;'>
            <h1 style='margin: 0;'>王浩，早安！</h1>
            <p style='margin: 5px 0 0 0;'>📅 {time.strftime('%Y-%m-%d')} | 全球与镇江资讯快报</p>
        </div>
    """
    
    global_html = format_section(global_articles, "🌍 全球热点简报 (30条)")
    local_html = format_section(local_articles, "🏙️ 镇江本地资讯 (10条)")
    
    footer = f"<p style='text-align: center; color: #bdc3c7; font-size: 12px;'>耗时 {int(time.time()-start_time)}s | 祝你今天元气满满！</p></div>"
    
    full_content = header + global_html + local_html + footer

    # 4. 发送邮件
    msg = MIMEText(full_content, 'html', 'utf-8')
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = Header(f"早安王浩 | 今日全球与镇江资讯简报", 'utf-8')

    try:
        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, [EMAIL_RECEIVER], msg.as_string())
        server.quit()
        print("✅ 邮件已成功发送至 1890925@qq.com")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

if __name__ == "__main__":
    main()
