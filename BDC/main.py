import os
import re
import smtplib
import fitz  # PyMuPDF
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate

# --- 配置区 ---
# 确保 PDF 文件在根目录
PDF_PATH = "威威的GPT单词本(8000词).pdf"
PROGRESS_FILE = "BDC/progress.txt"
LAST_WORDS_FILE = "BDC/last_words.txt"
WORDS_PER_DAY = 50

def get_file_content(path, default="0"):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return default

def save_file_content(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(str(content))

def extract_content():
    current_idx = int(get_file_content(PROGRESS_FILE))
    yesterday_words = get_file_content(LAST_WORDS_FILE, "第一天开始，暂无复习内容")
    
    if not os.path.exists(PDF_PATH):
        print(f"❌ 错误：找不到文件 {PDF_PATH}")
        return None
        
    doc = fitz.open(PDF_PATH)
    full_text = ""
    # 提取前 500 页内容（加速处理，8000词通常在前几百页）
    for i in range(min(len(doc), 500)):
        full_text += doc[i].get_text("text") + "\n"
    
    # 核心正则：根据书中格式提取条目
    # 该书条目通常以单词开始，下一行是“分析词义:”
    # 匹配模式：单词行 + 换行 + 分析词义
    blocks = re.split(r'\n(?=[a-zA-Z\-]{2,}\n分析词义:)', full_text)
    
    # 过滤掉不含“分析词义”的杂质块
    blocks = [b.strip() for b in blocks if "分析词义:" in b]

    total_count = len(blocks)
    start = current_idx
    end = min(start + WORDS_PER_DAY, total_count)
    
    today_blocks = blocks[start:end]
    
    today_word_names = []
    html_content = ""
    for b in today_blocks:
        # 提取块中的第一个单词作为名字
        name_match = re.match(r'^([a-zA-Z\-]+)', b)
        if name_match:
            today_word_names.append(name_match.group(1))
        # 格式化 HTML 内容
        formatted_block = b.replace('\n', '<br>')
        html_content += f"<div style='border-bottom:1px solid #eee; padding:15px; margin-bottom:10px; background:#fff;'>{formatted_block}</div>"

    return html_content, today_word_names, yesterday_words, end, total_count

def send_email(content, today_list, review_text):
    sender = os.environ.get("SENDER_EMAIL")
    password = os.environ.get("SENDER_PWD")
    receiver = os.environ.get("RECEIVER_EMAIL")

    if not sender or not password:
        print("❌ 错误：未设置环境变量 SENDER_EMAIL 或 SENDER_PWD")
        return False

    msg = MIMEMultipart()
    msg['From'] = f"单词助手 <{sender}>"
    msg['To'] = receiver
    msg['Subject'] = f"📖 今日50词 ({today_list[0]}...)"
    msg['Date'] = formatdate(localtime=True)

    html_template = f"""
    <html>
    <body style="background-color: #f4f7f6; padding: 20px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
        <div style="max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <div style="background: #e74c3c; color: white; padding: 15px; border-radius: 8px 8px 0 0;">
                <h3 style="margin:0;">🔄 昨日单词复习</h3>
            </div>
            <div style="padding: 15px; background: #fdf2f2; border: 1px solid #f5c6cb; border-top:none; margin-bottom: 20px; line-height: 1.8;">
                {review_text}
            </div>
            
            <h2 style="color: #2c3e50; border-left: 5px solid #27ae60; padding-left: 10px;">🚀 今日新词 (50个)</h2>
            {content}
            <hr>
            <p style="text-align:center; color: #7f8c8d; font-size: 12px;">每日学习，积少成多</p>
        </div>
    </body>
    </html>
    """
    msg.attach(MIMEText(html_template, 'html', 'utf-8'))

    try:
        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(sender, password)
        server.sendmail(sender, [receiver], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False

if __name__ == "__main__":
    result = extract_content()
    if result:
        html_body, today_names, review, next_idx, total = result
        if not today_names:
            print("🎉 所有单词已学完！")
        else:
            if send_email(html_body, today_names, review):
                save_file_content(PROGRESS_FILE, next_idx)
                save_file_content(LAST_WORDS_FILE, "、".join(today_names))
                print(f"✅ 发送成功！已推送第 {next_idx}/{total} 个单词")
