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
            # 兼容 --- 分隔和直接 ## 分隔
            raw_content = f.read()
            # 统一按 ## 进行分割，确保每个单词都是独立的块
            blocks = re.split(r'\n(?=## )|(?<=---)\n(?=## )', raw_content)
            for b in blocks:
                b = b.strip().replace("---", "")
                if b and "分析词义" in b:
                    all_blocks.append(b)
    return all_blocks

if __name__ == "__main__":
    words = load_words()
    if not words: print("❌ 未提取到单词"); exit(1)

    try:
        with open(PROGRESS_FILE, "r") as f: curr = int(f.read().strip())
    except: curr = 0
    
    # 1. 构造昨日复习 HTML
    review_html = ""
    if os.path.exists(LAST_WORDS_FILE):
        with open(LAST_WORDS_FILE, "r", encoding="utf-8") as f:
            for line in f.readlines():
                if ":" in line:
                    word, mean = line.split(":", 1)
                    review_html += f"<div style='margin-bottom:8px; font-size:14px; border-bottom:1px dashed #eee; padding-bottom:3px;'><b style='color:#333;'>{word.strip()}</b>: <span style='color:#666;'>{mean.strip()}</span></div>"

    # 2. 提取今日 50 词
    today = words[curr : curr + WORDS_PER_DAY]
    today_review_data = [] 
    html_blocks = []

    # 需要加括号的项目列表
    sub_headers = ["分析词义", "列举例句", "词根分析", "词缀分析", "发展历史和文化背景", "单词变形", "记忆辅助", "小故事"]

    for b in today:
        lines = b.splitlines()
        title = ""
        content_body = []
        
        # 提取标题并处理正文
        for line in lines:
            line = line.strip()
            if not line: continue
            if line.startswith("##"):
                title = line.lstrip("#").strip()
            else:
                # 检查是否是子项标题，是的话加上 【 】
                is_sub = False
                for sh in sub_headers:
                    if sh in line and len(line) < len(sh) + 5:
                        line = f"<div style='color:#2980b9; font-weight:bold; margin-top:15px; margin-bottom:5px;'>【{sh}】</div>"
                        is_sub = True
                        break
                if not is_sub:
                    line = f"<div style='margin-bottom:8px;'>{line}</div>"
                content_body.append(line)

        # 记录简要意思用于复习
        meaning = "查看详情"
        for line in b.splitlines():
            if "分析词义" in line:
                meaning = line.replace("分析词义", "").strip()[:40]
                break
        today_review_data.append(f"{title}: {meaning}")

        # 构造单个单词的 HTML 块
        # 顶部加一条明显的横线 (hr)
        block_html = f"""
        <div style='padding-top: 20px; margin-top: 20px; border-top: 2px solid #e74c3c;'>
            <div style='color: #e74c3c; font-size: 30px; font-weight: bold; margin-bottom: 15px;'>{title}</div>
            <div style='color: #2c3e50; font-size: 16px; line-height: 1.7; font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;'>
                {"".join(content_body)}
            </div>
        </div>
        """
        html_blocks.append(block_html)
    
    # 3. 发送邮件
    sender, pwd, rcvr = os.environ.get("SENDER_EMAIL"), os.environ.get("SENDER_PWD"), os.environ.get("RECEIVER_EMAIL")
    msg = MIMEMultipart()
    msg['Subject'] = f"📖 单词突破：{today_review_data[0].split(':')[0]} 等{len(today)}词"
    msg['From'], msg['To'] = sender, rcvr
    
    email_body = f"""
    <html>
    <body style='padding: 20px; background-color: #f5f7f9;'>
        <div style='max-width: 650px; margin: auto; background: white; padding: 30px; border: 1px solid #e1e8ed; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);'>
            <div style='background: #fffafa; padding: 20px; border-radius: 8px; margin-bottom: 30px; border: 1px solid #f5c6cb;'>
                <h3 style='color: #d9534f; margin-top: 0;'>🔄 昨日复习清单</h3>
                {review_html if review_html else "第一天，开始你的表演！"}
            </div>
            <h2 style='color: #333; text-align: center; margin-bottom: 30px;'>今日新词任务</h2>
            {"".join(html_blocks)}
            <div style='text-align: center; color: #95a5a6; font-size: 12px; margin-top: 40px; border-top: 1px solid #eee; padding-top: 20px;'>
                — 威威 GPT 单词本 · 打造最强词汇量 —
            </div>
        </div>
    </body>
    </html>
    """
    msg.attach(MIMEText(email_body, 'html', 'utf-8'))
    
    try:
        s = smtplib.SMTP_SSL("smtp.qq.com", 465)
        s.login(sender, pwd); s.sendmail(sender, [rcvr], msg.as_string()); s.quit()
        with open(PROGRESS_FILE, "w") as f: f.write(str(curr + len(today)))
        with open(LAST_WORDS_FILE, "w", encoding="utf-8") as f: f.write("\n".join(today_review_data))
        print("✅ 结构化排版修复版发送成功！")
    except Exception as e:
        print(f"❌ 发送失败: {e}")
