import os
import requests
import smtplib
import time
import sys
from email.mime.text import MIMEText
from email.header import Header
from googletrans import Translator

# 配置区
EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_RECEIVER = os.getenv('EMAIL_RECEIVER')
NEWS_API_KEY = os.getenv('NEWS_API_KEY') # 复用你之前的 NewsAPI Key

translator = Translator()

def translate_text(text):
    if not text: return "暂无内容"
    try:
        return translator.translate(text, dest='zh-cn').text
    except:
        return text

def fetch_pubmed_plus():
    """PubMed 增强搜索：指南 + 专家共识"""
    print("🚀 正在检索 PubMed 增强库 (Guidelines & Consensus)...")
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    # 扩大搜索范围：标题包含 Guideline 或 Consensus，且是最近 30 天
    term = "(guideline[Title] OR consensus[Title]) AND (last 30 days[Filter])"
    params = {"db": "pubmed", "term": term, "retmode": "json", "retmax": 5}
    try:
        res = requests.get(search_url, params=params, timeout=20).json()
        id_list = res.get('esearchresult', {}).get('idlist', [])
        if not id_list: return []
        
        summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        s_res = requests.get(summary_url, params={"db": "pubmed", "id": ",".join(id_list), "retmode": "json"}).json()
        
        results = []
        for pid in id_list:
            item = s_res['result'][pid]
            results.append({
                "source_type": "PubMed 权威文献",
                "title": item.get('title'),
                "info": f"{item.get('source')} | {item.get('pubdate')}",
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pid}/"
            })
        return results
    except:
        return []

def fetch_medical_news():
    """从 NewsAPI 抓取全球顶级医疗动态 (WHO, Lancet 等关键词)"""
    if not NEWS_API_KEY: return []
    print("🚀 正在抓取 NewsAPI 全球医疗前沿...")
    # 搜索包含医学指南或重大研究的报道
    url = f"https://newsapi.org/v2/everything?q=(medical guideline OR clinical study)&language=en&sortBy=publishedAt&pageSize=5&apiKey={NEWS_API_KEY}"
    try:
        res = requests.get(url, timeout=20).json()
        articles = res.get('articles', [])
        results = []
        for art in articles:
            results.append({
                "source_type": "NewsAPI 全球动态",
                "title": art.get('title'),
                "info": f"{art.get('source', {}).get('name')} | {art.get('publishedAt')[:10]}",
                "url": art.get('url')
            })
        return results
    except:
        return []

def main():
    start_time = time.time()
    # 合并两个数据源
    pubmed_data = fetch_pubmed_plus()
    news_data = fetch_medical_news()
    all_data = pubmed_data + news_data

    if not all_data:
        print("📭 全球库暂无更新。")
        return

    # 构造 HTML
    html = f"""<div style="font-family: sans-serif; max-width: 600px; margin: auto; border: 1px solid #ddd; padding: 20px; border-radius: 12px;">
        <div style="background: #c0392b; color: white; padding: 15px; text-align: center; border-radius: 8px;">
            <h1 style="margin: 0; font-size: 20px;">🩺 全球医学情报周报</h1>
            <p style="margin: 5px 0 0 0;">PubMed 增强版 + 全球顶级医疗新闻</p>
        </div>"""

    for i, item in enumerate(all_data):
        title_cn = translate_text(item['title'])
        html += f"""<div style="margin-top: 20px; border-bottom: 1px solid #eee; padding-bottom: 15px;">
            <span style="background: #ecf0f1; color: #7f8c8d; font-size: 10px; padding: 2px 6px; border-radius: 4px;">{item['source_type']}</span>
            <div style="font-weight: bold; color: #2c3e50; font-size: 16px; margin-top: 8px;">{item['title']}</div>
            <div style="color: #27ae60; font-size: 14px; margin: 8px 0;"><b>中文：</b>{title_cn}</div>
            <div style="font-size: 12px; color: #95a5a6;">📍 {item['info']}</div>
            <a href="{item['url']}" style="color: #2980b9; font-size: 13px; text-decoration: none; font-weight: bold;">查看全文 →</a>
        </div>"""
        time.sleep(0.5)

    html += f"<p style='text-align: center; color: #bdc3c7; font-size: 11px; margin-top: 20px;'>系统已打通 PubMed & NewsAPI | 耗时 {int(time.time()-start_time)}s</p></div>"

    # 发送
    msg = MIMEText(html, 'html', 'utf-8')
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = Header(f"🩺 医学指南与全球动态 ({time.strftime('%m/%d')})", 'utf-8')

    try:
        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, [EMAIL_RECEIVER], msg.as_string())
        server.quit()
        print(f"📧 邮件已送达！包含 {len(all_data)} 条情报。")
    except Exception as e:
        print(f"❌ 失败: {e}")

if __name__ == "__main__":
    main()
