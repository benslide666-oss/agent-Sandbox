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
            raw_content = f.read()
            blocks = re.split(r'\n(?=## )|(?<=---)\n(?=## )', raw_content)
            for b in blocks:
                b = b.strip().replace("---", "")
                if b and "分析词义" in b: all_blocks.append(b)
    return all_blocks

def get_motivational_msg(percent):
    if percent < 5: return "🌟 万事开头难，你已经迈出了最勇敢的一步！"
    if percent < 20: return "🚀 渐入佳境！保持这个节奏，词汇量正在悄悄蜕变。"
    if percent < 50: return "💪 坚持就是胜利！你已经消灭了近一半的拦路虎。"
    if percent < 80: return "🔥 势不可挡！胜利的曙光就在前方，再加把劲！"
    return "👑 奇迹即将发生！最后的一小段路，见证你的辉煌！"

if __name__ == "__main__":
    all_words = load_words()
    total_count = len(all_words)
    if not all_words: print("❌ 未提取到单词"); exit(1)

    try:
        with open(PROGRESS_FILE, "r") as f: curr = int(f.read().strip())
    except: curr = 0
    
    percent = round((curr / total_count) * 100, 1)
    days_left = (total_count - curr) // WORDS_PER_DAY
    moto_msg = get_motivational_msg(percent)

    review_html = ""
    if os.path.exists(LAST_WORDS_FILE):
        with open(LAST_WORDS_FILE, "r", encoding="utf-8") as f:
            for line in f.readlines():
                if ":" in line:
                    word, mean = line.split(":", 1)
                    review_html += f"<div style='margin-bottom:8px; font-size:16px; border-bottom:1px dashed #eee; padding-bottom:3px;'><b style='color:#333;'>{word.strip()}</b>: <span style='color:#666;'>{mean.strip()}</span></div>"

    today = all_words[curr : curr + WORDS_PER_DAY]
    today_review_data = [] 
    html_blocks = []
    sub_headers = ["分析词义", "列举例句", "词根分析", "词缀分析", "发展历史和文化背景", "单词变形", "记忆辅助", "小故事"]

    for b in today:
        lines = b.splitlines()
        title = ""
        content_body = []
        for line in lines:
            line = line.strip()
            if not line: continue
            if line.startswith("##"):
                title = line.lstrip("#").strip()
            else:
                is_sub = False
                for sh in sub_headers:
                    if sh in line and len(line) < len(sh) + 5:
                        line = f"<div style='color:#2980b9; font-weight:bold; font-size:22px; margin-top:25px; margin-bottom:10px;'>【{sh}】</div>"
                        is_sub = True
                        break
                if not is_sub:
                    line = f"<div style='margin-bottom:12px; font-size:18px;'>{line}</div>"
                content_body.append(line)

        meaning = "查看详情"
        for line in b.splitlines():
            if "分析词义" in line:
                meaning = line.replace("分析词义", "").strip()[:40]
                break
        today_review_data.append(f"{title}: {meaning}")

        block_html = f"""
        <div style='padding-top: 35px; margin-top: 35px; border-top: 3px solid #e74c3c;'>
            <div style='color: #e74c3c; font-size: 38px; font-weight: bold; margin-bottom: 15px;'>{title}</div>
            <div style='color: #2c3e50; font-size: 18px; line-height: 1.9;'>
                {"".join(content_body)}
            </div>
        </div>
        """
        html_blocks.append(block_html)
    
    sender, pwd, rcvr = os.environ.get("SENDER_EMAIL"), os.environ.get("SENDER_PWD"), os.environ.get("RECEIVER_EMAIL")
    msg = MIMEMultipart()
    msg['Subject'] = f"📈 {percent}% | 今日：{today_review_data[0].split(':')[0]} 等50词"
    msg['From'], msg['To'] = sender, rcvr
    
    email_body = f"""
    <html>
    <body style='padding: 20px; background-color: #f5f7f9;'>
        <div style='max-width: 700px; margin: auto; background: white; padding: 40px; border: 1px solid #e1e8ed; border-radius: 15px;'>
            <div style='text-align: center; margin-bottom: 35px; padding: 20px; background: #fff9db; border-radius: 10px; border: 1px solid #fab005;'>
                <div style='font-size: 20px; color: #f08c00; font-weight: bold; margin-bottom: 10px;'>{moto_msg}</div>
                <div style='background: #e9ecef; border-radius: 20px; height: 15px; width: 100%; margin: 15px 0;'>
                    <div style='background: #fab005; height: 15px; width: {percent}%; border-radius: 20px;'></div>
                </div>
                <div style='font-size: 16px; color: #5c5f66;'>
                    当前进度：<b>{curr} / {total_count}</b> ({percent}%) | 预计 <b>{days_left}</b> 天通关 🏁
                </div>
            </div>
            <div style='background: #fffafa; padding: 20px; border-radius: 8px; margin-bottom: 35px; border: 1px solid #f5c6cb;'>
                <h3 style='color: #d9534f; margin-top: 0; font-size: 22px;'>🔄 昨日复习回顾</h3>
                {review_html if review_html else "第一天，开始你的表演！"}
            </div>
            <h2 style='color: #333; text-align: center; font-size: 30px; border-bottom: 5px solid #e74c3c; padding-bottom: 15px;'>今日新词任务</h2>
            {"".join(html_blocks)}
            <div style='text-align: center; color: #95a5a6; font-size: 14px; margin-top: 50px; border-top: 1px solid #eee; padding-top: 25px;'>
                — 威威词霸 · 每日精进 · 第 { (curr // 50) + 1 } 天 —
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
        print(f"✅ 激励大字版发送成功！当前进度：{percent}%")
    except Exception as e:
        print(f"❌ 发送失败: {e}")
