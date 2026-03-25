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

translator = Translator()

def translate_text(text):
    if not text: return "暂无内容"
    try:
        return translator.translate(text, dest='zh-cn').text
    except Exception as e:
        return text

def fetch_pubmed_guidelines():
    print("🚀 正在检索 PubMed 全球医学指南库...")
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_params = {
        "db": "pubmed",
        "term": "(Practice Guideline[Publication Type]) AND (last 30 days[Filter])",
        "retmode": "json",
        "retmax": 10
    }
    try:
        search_res = requests.get(search_url, params=search_params, timeout=20).json()
        id_list = search_res.get('esearchresult', {}).get('idlist', [])
        if not id_list:
            print("📭 本周 PubMed 暂无新指南。")
            return []
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
        return guidelines
    except Exception as e:
        print(f"❌ 抓取失败: {e}")
        return []

def send_email_report(html_body):
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        print("❌ 错误：未检测到邮箱配置（Secrets）。")
        return
    msg = MIMEText(html_body, 'html', 'utf-8')
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = Header(f"🩺 医学指南周报 | PubMed 全球前沿 ({time.strftime('%Y-%m-%d')})", 'utf-8')
    try:
        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, [EMAIL_RECEIVER], msg.as_string())
        server.quit()
        print("📧 邮件已成功投递至: " + EMAIL_RECEIVER)
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

def main():
    guidelines = fetch_pubmed_guidelines()
    if not guidelines: return
    html = f"""<div style="font-family: sans-serif; max-width: 600px; margin: auto; border: 1px solid #eee; padding: 20px;">
        <h2 style="color: #2c3e50; text-align: center;">🩺 每周医学指南快报</h2>"""
    for i, g in enumerate(guidelines):
        title_cn = translate_text(g['title'])
        html += f"""<div style="margin-top: 20px; border-bottom: 1px solid #f0f0f0; padding-bottom: 10px;">
            <div style="font-weight: bold; color: #c0392b;">{i+1}. {g['title']}</div>
            <div style="background: #f1f8e9; padding: 5px; margin: 5px 0; font-size: 14px;">{title_cn}</div>
            <div style="font-size: 12px; color: #7f8c8d;">来源: {g['source']} | {g['date']}</div>
            <a href="{g['url']}" style="color: #2980b9; font-size: 13px;">查看原文 →</a>
        </div>"""
        time.sleep(0.5)
    html += "</div>"
    send_email_report(html)

if __name__ == "__main__":
    main()
