import os
import smtplib
import fitz  # PyMuPDF
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ================= 配置参数 =================
PDF_FILE = "威威的GPT单词本(8000词).pdf"
PROGRESS_FILE = "progress.txt"
PAGES_PER_DAY = 3 # 每天推送的页数，可根据单词密度自行修改

def get_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return int(f.read().strip())
    return 0

def update_progress(new_page):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        f.write(str(new_page))

def extract_text_from_pdf(start_page, num_pages):
    doc = fitz.open(PDF_FILE)
    total_pages = len(doc)
    end_page = min(start_page + num_pages, total_pages)
    
    # 简单的 HTML 邮件排版
    content = f"<h3>📚 今日学习进度：第 {start_page + 1} 页 至 第 {end_page} 页</h3><hr>"
    
    for i in range(start_page, end_page):
        page = doc.load_page(i)
        # 提取文本并将换行符替换为 HTML 的 <br>
        text = page.get_text("text").replace('\n', '<br>')
        content += f"<h4>--- 第 {i + 1} 页 ---</h4><p style='line-height: 1.6;'>{text}</p><br>"
        
    return content, end_page, total_pages

def send_email(content):
    sender = os.environ.get("SENDER_EMAIL")
    password = os.environ.get("SENDER_PWD")
    receiver = os.environ.get("RECEIVER_EMAIL")

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = "🚀 你的每日 GPT 单词本推送"

    msg.attach(MIMEText(content, 'html', 'utf-8'))

    # QQ 邮箱的 SMTP 服务器和端口
    try:
        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(sender, password)
        server.sendmail(sender, [receiver], msg.as_string())
        server.quit()
        print("邮件发送成功！")
    except Exception as e:
        print(f"邮件发送失败: {e}")

if __name__ == "__main__":
    current_page = get_progress()
    print(f"当前进度：第 {current_page} 页")
    
    daily_content, next_page, total_pages = extract_text_from_pdf(current_page, PAGES_PER_DAY)
    
    if current_page >= total_pages:
        print("🎉 恭喜！整本书已经推送完毕。")
    else:
        send_email(daily_content)
        update_progress(next_page)
        print(f"进度已更新至第 {next_page} 页。")