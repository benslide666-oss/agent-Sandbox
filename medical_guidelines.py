import os
import requests
import smtplib
import time
import sys
from email.mime.text import MIMEText
from email.header import Header
from googletrans import Translator

# 强制打印启动日志
print("--- [系统日志] 脚本已启动 ---")

EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_RECEIVER = os.getenv('EMAIL_RECEIVER')

if not EMAIL_SENDER:
    print("❌ 错误：环境变量 EMAIL_SENDER 为空")
    sys.exit(1)

translator = Translator()

def fetch_pubmed_guidelines():
    # 我们直接搜索 "Medicine" 确保一定能搜到东西来测试邮件
    print("🚀 正在检索 PubMed 数据库 (测试模式: 搜索 Medicine)...")
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_params = {
        "db": "pubmed",
        "term": "Medicine[Title]", 
        "retmode": "json",
        "retmax": 3
    }
    try:
        res = requests.get(search_url, params=search_params, timeout=20).json()
        id_list = res.get('esearchresult', {}).get('idlist', [])
        if not id_list:
            print("📭 未搜到任何结果。")
            return []
        
        print(f"✅ 成功抓取到 {len(id_list)} 篇文献，准备发送邮件...")
        return [{"title": "Test Medical Article", "url": "https://pubmed.ncbi.nlm.nih.gov/"}]
    except Exception as e:
        print(f"❌ 抓取失败: {e}")
        return []

def main():
    guidelines = fetch_pubmed_guidelines()
    if not guidelines:
        return
    
    body = "<h3>医学助手测试邮件</h3><p>如果你收到这封信，说明你的 GitHub Secrets 配置完全正确！</p>"
    
    msg = MIMEText(body, 'html', 'utf-8')
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = Header("🎯 恭喜！你的医学助理上线了", "utf-8")

    try:
        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, [EMAIL_RECEIVER], msg.as_string())
        server.quit()
        print("📧 邮件已成功送达！快去检查 QQ 邮箱。")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

if __name__ == "__main__":
    main()
