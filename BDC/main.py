import os
import re
import smtplib
import fitz  # PyMuPDF
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate

# --- 配置区 ---
PDF_PATH = "BDC/威威的GPT单词本(8000词).pdf"
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
        return None
        
    doc = fitz.open(PDF_PATH)
    full_text = ""
    # 遍历所有页面提取文本
    for page in doc:
        full_text += page.get_text("text") + "\n"
    
    # 核心正则：匹配单词条目。匹配逻辑：单词(英文) + 换行 + "分析词义:"
    # 使用 re.DOTALL 确保匹配更灵活
    blocks = re.split(r'\n(?=[a-zA-Z\-]{2,}\n分析词义:)', full_text)
    
    # 过滤掉不含“分析词义”的非单词块（如目录、前言）
    blocks = [b.strip() for b in blocks if "分析词义:" in b]

    total_count = len(blocks)
    start = current_idx
    end = min(start + WORDS_PER_DAY, total_count)
    
    today_blocks = blocks[start:end]
    today_word_names = []
    html_content = ""

    for b in today_blocks:
        # 提取单词名称
        name_match = re.match(r'^([a-zA-Z\-]+)', b)
        word_name = name_match.group(1) if name_match else "Vocabulary"
        if name_match:
            today_word_names.append(word_name)
        
        # 处理正文：将第一个单词替换为 红色、加粗、大字号 的 HTML
        # 其余换行替换为 <br>
        body_without_name = b[len(word_name):].strip().replace('\n', '<br>')
        
        html_content += f"""
        <div style='border-bottom:2px solid #eee; padding:20px 0; margin-bottom:10px;'>
            <span style='color: #e74c3c; font-size: 24px; font-weight: bold;'>{word_name}</span>
            <div style='margin-top: 10px; color: #34495e; font-size: 16px; line-height: 1.6;'>
                {body_without_name}
            </div>
        </div>
        """

    return html_content, today_word_names, yesterday_words, end, total_count

def send_email(content, today_list, review_text):
    sender = os.environ.get("SENDER_EMAIL")
    password = os.environ.get("SENDER_PWD")
    receiver = os.environ.get("RECEIVER_EMAIL")

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = f"🔥 今日50词突破：{today_list[0]}..."
    msg['Date'] = formatdate(localtime=True)

    html_template = f"""
    <html>
    <body style="background-color: #ffffff; padding: 10px; font-family: sans-serif;">
        <div style="max-width: 600px; margin: auto; border: 1px solid #e1e4e8; border-radius: 12px; overflow: hidden;">
            <div style="background: #fdf2f2; padding: 15px; border-bottom: 2px solid #f5c6cb;">
                <h3 style="color: #d9534f; margin: 0 0 10px 0;">🔄 昨日复习回顾</h3>
                <p style="font-size: 14px; color: #7f8c8d; line-height: 1.5;">{review_text}</p>
            </div>
            <div style="padding: 20px;">
                <h2 style="color: #2c3e50; border-bottom: 3px solid #e74c3c; display: inline-block; padding-bottom: 5px;">📖 今日新词 (50)</h2>
                {content}
            </div>
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
        print(f"❌ 发送失败: {e}")
        return False

if __name__ == "__main__":
    result = extract_content()
    if result:
        html_body, today_names, review, next_idx, total = result
        if not today_names:
            print("🎉 恭喜！全书已学完。")
        else:
            if send_email(html_body, today_names, review):
                save_file_content(PROGRESS_FILE, next_idx)
                save_file_content(LAST_WORDS_FILE, "、".join(today_names))
                print(f"✅ 成功！进度: {next_idx}/{total}")
