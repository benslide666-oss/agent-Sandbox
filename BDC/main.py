import os, smtplib
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
    
    # 1. 构造昨日复习 HTML (每行一个单词 + 意思)
    review_html = ""
    if os.path.exists(LAST_WORDS_FILE):
        with open(LAST_WORDS_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                if ":" in line:
                    word, mean = line.split(":", 1)
                    review_html += f"<div style='margin-bottom:5px; font-size:14px; border-bottom:1px solid #f0f0f0; padding-bottom:2px;'><b style='color:#555;'>{word.strip()}</b>: <span style='color:#888;'>{mean.strip()}</span></div>"

    # 2. 提取今日 50 词并精准处理排版
    today = words[curr : curr + WORDS_PER_DAY]
    today_review_data = [] 
    html_blocks = []

    for b in today:
        lines = b.splitlines()
        # 修复首字母缺失：直接提取第一行并去掉 # 号
        title = lines[0].lstrip('#').strip()
        # 提取正文：去掉第一行后的所有内容
        content_lines = lines[1:]
        
        # 提取核心意思用于复习
        meaning = "查看详情"
        for l in content_lines:
            if "分析词义" in l:
                meaning = l.replace("分析词义", "").strip()[:40]
                break
        today_review_data.append(f"{title}: {meaning}")

        # 构造 HTML：保留换行符
        body_content = "<br>".join([l.strip() for l in content_lines if l.strip()])
        
        block_html = f"""
        <div style='padding: 20px 0; border-bottom: 2px solid #eeeeee;'>
            <div style='color: #e74c3c; font-size: 28px; font-weight: bold; margin-bottom: 15px;'>{title}</div>
            <div style='color: #2c3e50; font-size: 16px; line-height: 1.8; font-family: "Microsoft YaHei", sans-serif;'>
                {body_content}
            </div>
        </div>
        """
        html_blocks.append(block_html)
    
    # 3. 组装邮件内容
    sender, pwd, rcvr = os.environ.get("SENDER_EMAIL"), os.environ.get("SENDER_PWD"), os.environ.get("RECEIVER_EMAIL")
    msg = MIMEMultipart()
    msg['Subject'] = f"📖 单词：{today_review_data[0].split(':')[0]} 等{len(today)}词"
    msg['From'], msg['To'] = sender, rcvr
    
    email_body = f"""
    <html>
    <body style='padding: 20px; background-color: #fcfcfc;'>
        <div style='max-width: 600px; margin: auto; background: white; padding: 30px; border: 1px solid #ddd; border-radius: 8px;'>
            <div style='background: #fdf2f2; padding: 20px; border-radius: 6px; margin-bottom: 30px; border-left: 5px solid #d9534f;'>
                <h3 style='color: #d9534f; margin-top: 0;'>🔄 昨日复习回顾</h3>
                {review_html if review_html else "第一天开启，Fighting!"}
            </div>
            <h2 style='color: #333; border-bottom: 3px solid #e74c3c; padding-bottom: 10px; margin-bottom: 20px;'>今日新词</h2>
            {"".join(html_blocks)}
            <div style='text-align: center; color: #aaa; font-size: 12px; margin-top: 30px;'>— 威威制作 · 坚持就是胜利 —</div>
        </div>
    </body>
    </html>
    """
    msg.attach(MIMEText(email_body, 'html', 'utf-8'))
    
    try:
        s = smtplib.SMTP_SSL("smtp.qq.com", 465)
        s.login(sender, pwd); s.sendmail(sender, [rcvr], msg.as_string()); s.quit()
        # 更新记录
        with open(PROGRESS_FILE, "w") as f: f.write(str(curr + len(today)))
        with open(LAST_WORDS_FILE, "w", encoding="utf-8") as f: f.write("\n".join(today_review_data))
        print("✅ 排版与首字母修复版发送成功！")
    except Exception as e:
        print(f"❌ 失败: {e}")
