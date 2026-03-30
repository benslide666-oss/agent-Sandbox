import os, smtplib, re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate

# 路径配置
DCB_DIR = "BDC/DCB"
PROGRESS_FILE = "BDC/progress.txt"
LAST_WORDS_FILE = "BDC/last_words.txt"
WORDS_PER_DAY = 50

def load_words():
    all_blocks = []
    if not os.path.exists(DCB_DIR): return []
    files = sorted([f for f in os.listdir(DCB_DIR) if f.endswith(".md")])
    for f_name in files:
        with open(os.path.join(DCB_DIR, f_name), "r", encoding="utf-8") as f:
            for block in f.read().split("---"):
                block = block.strip()
                if block and "分析词义" in block:
                    all_blocks.append(block)
    return all_blocks

if __name__ == "__main__":
    words = load_words()
    if not words: print("❌ 未提取到单词"); exit(1)

    try:
        with open(PROGRESS_FILE, "r") as f: curr = int(f.read().strip())
    except: curr = 0
    
    # 1. 处理昨日复习内容
    review_html = ""
    if os.path.exists(LAST_WORDS_FILE):
        with open(LAST_WORDS_FILE, "r", encoding="utf-8") as f:
            review_lines = f.readlines()
            review_html = "".join([f"<li style='margin-bottom:5px;font-size:14px;color:#666;'>{line.strip()}</li>" for line in review_lines if line.strip()])

    # 2. 提取今日 50 词并生成 HTML
    today = words[curr : curr + WORDS_PER_DAY]
    today_review_data = [] # 存入 review 文件的格式：单词: 意思
    html_blocks = []

    for b in today:
        lines = [l.strip() for l in b.split('\n') if l.strip()]
        name = lines[0].replace("#", "").strip()
        
        # 提取简短中文意思（用于明天的复习列表）
        meaning = "暂无释义"
        for line in lines:
            if "分析词义" in line:
                meaning = line.split("分析词义")[-1].strip()[:30] # 截取前30个字
                break
        today_review_data.append(f"{name}: {meaning}")

        # 构造单词 HTML 内容
        # 将原文本中的换行符转换为 <br>，保持排版
        body_html = b.replace("\n", "<br>").replace(f"## {name}", "").strip()
        
        block_html = f"""
        <div style='margin-bottom: 30px;'>
            <div style='color: #e74c3c; font-size: 26px; font-weight: bold; margin-bottom: 10px;'>{name}</div>
            <div style='color: #34495e; font-size: 16px; line-height: 1.8; background: #f9f9f9; padding: 15px; border-left: 4px solid #e74c3c;'>
                {body_html}
            </div>
            <hr style='border: 0; border-top: 1px dashed #ccc; margin-top: 20px;'>
        </div>
        """
        html_blocks.append(block_html)
    
    # 3. 发送邮件
    sender, pwd, rcvr = os.environ.get("SENDER_EMAIL"), os.environ.get("SENDER_PWD"), os.environ.get("RECEIVER_EMAIL")
    msg = MIMEMultipart()
    msg['Subject'] = f"📖 单词：{today_review_data[0].split(':')[0]} 等{len(today)}词"
    msg['From'], msg['To'] = sender, rcvr
    
    email_body = f"""
    <html>
    <body style='font-family: sans-serif; padding: 20px; color: #333;'>
        <div style='max-width: 650px; margin: auto; border: 1px solid #eee; padding: 20px; border-radius: 10px;'>
            <div style='background: #fff5f5; padding: 15px; border-radius: 8px; margin-bottom: 25px;'>
                <h3 style='color: #d9534f; margin-top: 0;'>🔄 昨日复习回顾</h3>
                <ul style='padding-left: 20px; margin: 0;'>{review_html if review_html else "第一天开始，加油！"}</ul>
            </div>
            <h2 style='border-bottom: 2px solid #e74c3c; padding-bottom: 10px;'>今日新词任务</h2>
            {"".join(html_blocks)}
        </div>
    </body>
    </html>
    """
    msg.attach(MIMEText(email_body, 'html', 'utf-8'))
    
    try:
        s = smtplib.SMTP_SSL("smtp.qq.com", 465)
        s.login(sender, pwd); s.sendmail(sender, [rcvr], msg.as_string()); s.quit()
        # 更新进度和复习列表
        with open(PROGRESS_FILE, "w") as f: f.write(str(curr + len(today)))
        with open(LAST_WORDS_FILE, "w", encoding="utf-8") as f: f.write("\n".join(today_review_data))
        print(f"✅ 排版优化版发送成功！")
    except Exception as e:
        print(f"❌ 邮件失败: {e}")
