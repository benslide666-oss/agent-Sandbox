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

def translate_safe(text):
    """翻译函数，带长度截断和错误处理"""
    if not text: return "点击原文链接查看详情。"
    try:
        # 截取前 200 个字符进行翻译，确保摘要在 50 字左右
        clean_text = text[:200].replace('\n', ' ')
        res = translator.translate(clean_text, dest='zh-cn').text
        return res[:60] + "..." if len(res) > 60 else res
    except:
        return text[:50] + "..."

def fetch_news(query=None, count=30):
    """获取新闻数据"""
    print(f"🚀 正在检索: {query if query else '全球热点'}...")
    if query:
        # 精准定位：镇江 + 江苏，按相关性排序
        url = f"https://newsapi.org/v2/everything?q={query}&sortBy=relevancy&pageSize={count}&apiKey={NEWS_API_KEY}"
    else:
        url = f"https://newsapi.org/v2/top-headlines?language=en&pageSize={count}&apiKey={NEWS_API_KEY}"
    
    try:
        response = requests.get(url, timeout=20).json()
        return response.get('articles', [])
    except Exception as e:
        print(f"❌ 抓取出错: {e}")
        return []

def format_news_html(articles, section_title):
    """构造新闻板块 HTML"""
    html = f"""
    <div style='margin-top: 30px;'>
        <h2 style='color: #d35400; border-bottom: 2px solid #e67e22; padding-bottom: 5px;'>{section_title}</h2>
    """
    if not articles:
        html += "<p style='color: #888;'>今日该板块暂无深度更新。</p>"
        return html
    
    for i, art in enumerate(articles):
        title_en = art.get('title', 'No Title')
        desc_en = art.get('description') or art.get('content') or "Details in original link."
        
        # 翻译标题和摘要
        title_cn = translate_safe(title_en)
        desc_cn = translate_safe(desc_en)
        
        html += f"""
        <div style='margin-bottom: 20px; padding: 10px; background: #fdfefe; border-radius: 5px;'>
            <div style='font-weight: bold; font-size: 16px; color: #2c3e50;'>{i+1}. {title_cn}</div>
            <div style='font-size: 13px; color: #7f8c8d; margin: 8px 0;'><b>摘要：</b>{desc_cn}</div>
            <div style='font-size: 11px; color: #bdc3c7;'>Source: {art.get('source', {}).get('name')} | <a href='{art['url']}' style='color: #3498db;'>阅读原文</a></div>
        </div>
        """
        # 40条翻译量大，增加微小延迟防止接口屏蔽
        time.sleep(0.6)
        print(f"已处理 {section_title} 第 {i+1} 条")
        
    html += "</div>"
    return html

def main():
    start_time = time.time()
    
    # 1. 抓取全球 30 条
    global_news = fetch_news(count=30)
    # 2. 抓取镇江 10 条 (精准定位关键词)
    local_news = fetch_news(query='"Zhenjiang" AND "Jiangsu"', count=10)

    # 3. 组装邮件内容
    mail_html = f"""
    <div style='max-width: 700px; margin: auto; font-family: "Microsoft YaHei", sans-serif; line-height: 1.6;'>
        <div style='background: #2c3e50; color: white; padding: 25px; text-align: center; border-radius: 10px 10px 0 0;'>
            <h1 style='margin: 0; font-size: 24px;'>王浩，早安！今日资讯已送达</h1>
            <p style='margin: 10px 0 0 0;'>📅 {time.strftime('%Y-%m-%d')} | 覆盖全球视野与家乡动态</p>
        </div>
        <div style='padding: 20px; border: 1px solid #eee; border-top: none;'>
    """
    
    mail_html += format_news_html(global_news, "🌍 全球纵览 (Top 30)")
    mail_html += format_news_html(local_news, "🏙️ 镇江动态 (Local 10)")
    
    mail_html += f"""
            <div style='margin-top: 40px; text-align: center; color: #bdc3c7; font-size: 12px;'>
                <p>程序自动翻译自国际信源，摘要约 50 字。</p>
                <p>© 2026 王浩的 AI 秘书 | 任务耗时 {int(time.time() - start_time)}s</p>
            </div>
        </div>
    </div>
    """

    # 4. SMTP 发送
    msg = MIMEText(mail_html, 'html', 'utf-8')
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = Header(f"早安王浩 | 今日全球 30 条 & 镇江 10 条新闻简报", 'utf-8')

    try:
        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, [EMAIL_RECEIVER], msg.as_string())
        server.quit()
        print("✅ 深度简报已成功发送！")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    main()
