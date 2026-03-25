import os
import requests
import smtplib
import time
from email.mime.text import MIMEText
from email.header import Header
from googletrans import Translator

# 从 GitHub Secrets 读取配置
EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_RECEIVER = os.getenv('EMAIL_RECEIVER')

translator = Translator()

def translate_text(text):
    """安全翻译函数"""
    if not text: return "暂无内容"
    try:
        return translator.translate(text, dest='zh-cn').text
    except:
        return text

def fetch_pubmed_guidelines():
    """从 PubMed 检索过去 30 天的临床实践指南"""
    print("🚀 正在检索 PubMed 全球医学指南库...")
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_params = {
        "db": "pubmed",
        "term": "(Practice Guideline[Publication Type]) AND (last 30 days[Filter])",
        "retmode": "json",
        "retmax": 10
    }
    try:
        res = requests.get(search_url, params=search_params, timeout=20).json()
        id_list = res.get('esearchresult', {}).get('idlist', [])
        if not id_list:
            print("📭 过去 30 天暂无新指南发布。")
            return []
        
        # 获取摘要简报
        summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        summary_params = {"db": "pubmed", "id": ",".join(id_list), "retmode": "json"}
        summary_res = requests.get(summary_url, params=summary_params, timeout=20).json()
        
        guidelines = []
        for pid in id_list:
            item = summary_res['result'][pid]
            guidelines.append({
                "title": item.get('title'),
                "source": item.get('source'),
                "date": item.get('pubdate'),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pid}/"
            })
        print(f"✅ 成功抓取 {len(guidelines)} 篇临床指南")
        return guidelines
    except Exception as e:
        print(f"❌ 抓取失败: {e}")
        return []

def main():
    start_time = time.time()
    guidelines = fetch_pubmed_guidelines()
    if not guidelines:
        return
    
    # 构造专业 HTML 邮件排版
    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: auto; border: 1px solid #e0e0e0; padding: 20px; border-radius: 10px;">
        <div style="background-color: #2c3e50; padding: 15px; border-radius: 5px; text-align: center;">
            <h1 style="color: #ffffff; margin: 0; font-size: 20px;">🩺 每周医学指南快报</h1>
            <p style="color: #bdc3c7; margin: 5px 0 0 0;">数据源：PubMed (National Library of Medicine)</p>
        </div>
    """
    
    for i, g in enumerate(guidelines):
        title_cn = translate_text(g['title'])
        html += f"""
        <div style="margin-top: 20px; padding-bottom: 15px; border-bottom: 1px dashed #ddd;">
            <div style="font-weight: bold; font-size: 16px; color: #c0392b;">{i+1}. {g['title']}</div>
            <div style="background: #f1f8e9; padding: 8px; border-radius: 4px; margin: 10px 0; font-size: 14px; color: #2e7d32;">
                <b>中文标题：</b>{title_cn}
            </div>
            <div style="font-size: 12px; color: #7f8c8d;">🏢 来源：{g['source']} | 📅 日期：{g['date']}</div>
            <a href="{g['url']}" style="color: #2980b9; text-decoration: none; font-size: 13px; font-weight: bold;">查看原文摘要 →</a>
        </div>
        """
        time.sleep(0.5)

    html += f"<p style='text-align: center; color: #95a5a6; font-size: 12px; margin-top: 20px;'>耗时 {int(time.time()-start_time)}s | 加油，子超！</p></div>"

    # 发送邮件
    msg = MIMEText(html, 'html', 'utf-8')
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = Header(f"🩺 全球医学指南周报 ({time.strftime('%Y-%m-%d')})", 'utf-8')

    try:
        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, [EMAIL_RECEIVER], msg.as_string())
        server.quit()
        print("📧 专业版简报已送达！")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

if __name__ == "__main__":
    main()
