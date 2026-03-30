import os
import requests
import smtplib
import time
from email.mime.text import MIMEText
from email.header import Header
from googletrans import Translator

EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_RECEIVER = os.getenv('EMAIL_RECEIVER')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')

translator = Translator()

def translate_text(text):
    if not text: return "暂无内容"
    try:
        return translator.translate(text, dest='zh-cn').text
    except:
        return text

def fetch_pubmed_comprehensive():
    """PubMed 综合搜索：指南 + 专家共识 + 荟萃分析 (证据等级最高)"""
    print("🚀 正在检索 PubMed 综合医学库...")
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    # 扩大搜索词：不仅搜标题，还搜摘要，加入 Meta-Analysis
    term = "(guideline[Title/Abstract] OR consensus[Title/Abstract] OR \"meta-analysis\"[Title/Abstract]) AND (last 30 days[Filter])"
    params = {"db": "pubmed", "term": term, "retmode": "json", "retmax": 8}
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
                "tag": "权威文献/指南",
                "title": item.get('title'),
                "info": f"{item.get('source')} | {item.get('pubdate')}",
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pid}/"
            })
        return results
    except: return []

def fetch_health_news():
    """NewsAPI 搜索医学突破"""
    if not NEWS_API_KEY: 
        print("⚠️ 警告: NEWS_API_KEY 未配置，跳过新闻抓取。")
        return []
    print("🚀 正在抓取 NewsAPI 医疗动态...")
    # 搜索医学研究或指南
    url = f"https://newsapi.org/v2/everything?q=(medical study OR health guideline)&language=en&sortBy=relevancy&pageSize=5&apiKey={NEWS_API_KEY}"
    try:
        res = requests.get(url, timeout=20).json()
        articles = res.get('articles', [])
        return [{"tag": "全球医疗趋势", "title": a['title'], "info": a['source']['name'], "url": a['url']} for a in articles]
    except: return []

def main():
    start_time = time.time()
    all_data = fetch_pubmed_comprehensive() + fetch_health_news()

    if not all_data:
        print("📭 依然未搜到内容，请检查关键词或 API 额度。")
        return

    html = f"""<div style="font-family: sans-serif; max-width: 600px; margin: auto; border: 1px solid #eee; padding: 20px; border-radius: 12px;">
        <div style="background: #2c3e50; color: white; padding: 15px; text-align: center; border-radius: 8px;">
            <h1 style="margin: 0; font-size: 18px;">🩺 全球医学前沿周报 (王浩专供)</h1>
        </div>"""

    for i, item in enumerate(all_data):
        cn_title = translate_text(item['title'])
        html += f"""<div style="margin-top: 15px; border-bottom: 1px dashed #ddd; padding-bottom: 15px;">
            <span style="background: #e74c3c; color: white; font-size: 10px; padding: 2px 6px; border-radius: 4px;">{item['tag']}</span>
            <div style="font-weight: bold; color: #333; font-size: 15px; margin-top: 5px;">{item['title']}</div>
            <div style="color: #27ae60; font-size: 14px; margin: 5px 0;">{cn_title}</div>
            <div style="font-size: 12px; color: #999;">{item['info']}</div>
            <a href="{item['url']}" style="color: #2980b9; font-size: 12px; text-decoration: none;">Read Detail →</a>
        </div>"""
        time.sleep(0.4)

    html += "</div>"
    
    msg = MIMEText(html, 'html', 'utf-8')
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = Header(f"🩺 每周医学前沿情报 ({time.strftime('%m/%d')})", 'utf-8')

    try:
        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, [EMAIL_RECEIVER], msg.as_string())
        server.quit()
        print(f"📧 邮件已发出！共 {len(all_data)} 条情报。")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    main()
