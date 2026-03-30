cat << 'EOF' > main.py
import os
import smtplib
import fitz  # PyMuPDF
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate # 用于生成标准时间戳防拦截

PDF_FILE = "威威的GPT单词本(8000词).pdf"
PROGRESS_FILE = "progress.txt"
PAGES_PER_DAY = 3

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
    
    content = f"<h3>📚 今日学习进度：第 {start_page + 1} 页 至 第 {end_page} 页</h3><hr>"
    for i in range(start_page, end_page):
        page = doc.load_page(i)
        text = page.get_text("text").replace('\n', '<br>')
        content += f"<h4>--- 第 {i + 1} 页 ---</h4><p style='line-height: 1.6;'>{text}</p><br>"
        
    return content, end_page, total_pages

def send_email(content):
    sender = os.environ.get("SENDER_EMAIL")
    password = os.environ.get("SENDER_PWD")
    receiver = os.environ.get("RECEIVER_EMAIL")

    # 1. 拦截空变量（防止本地运行报错）
    if not sender or not password or not receiver:
        print("❌ 错误：环境变量为空！请检查 Secrets 配置或本地 export。")
        return False

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = "🚀 你的每日 GPT 单词本推送"
    # 2. 补全时间戳，伪装成正常客户端发信，防止被踢
    msg['Date'] = formatdate(localtime=True)

    msg.attach(MIMEText(content, 'html', 'utf-8'))

    try:
        print("-> 正在连接 QQ 邮箱服务器...")
        server = smtplib.SMTP_SSL("smtp.qq.com", 465, timeout=10)
        # 3. 开启 debug 模式，如果再失败，能看到具体是哪一步被拒绝
        server.set_debuglevel(1) 
        
        print("-> 连接成功，准备验证授权码...")
        server.login(sender, password)
        
        print("-> 验证通过，正在发送数据...")
        server.sendmail(sender, [receiver], msg.as_string())
        server.quit()
        print("✅ 邮件发送成功！")
        return True
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False

if __name__ == "__main__":
    current_page = get_progress()
    print(f"当前进度：第 {current_page} 页")
    
    daily_content, next_page, total_pages = extract_text_from_pdf(current_page, PAGES_PER_DAY)
    
    if current_page >= total_pages:
        print("🎉 恭喜！整本书已经推送完毕。")
    else:
        # 4. 逻辑修复：只有邮件确实发送成功了，才把进度写入文件
        if send_email(daily_content):
            update_progress(next_page)
            print(f"进度已安全更新至第 {next_page} 页。")
        else:
            print("⚠️ 邮件未发出，进度保持不变。")
EOF