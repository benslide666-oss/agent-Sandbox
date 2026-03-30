import os, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def load_words():
    all_blocks = []
    dcb_dir = "BDC/DCB"
    if not os.path.exists(dcb_dir): return []
    files = sorted([f for f in os.listdir(dcb_dir) if f.endswith(".md")])
    for f_name in files:
        with open(os.path.join(dcb_dir, f_name), "r", encoding="utf-8") as f:
            blocks = f.read().split("---")
            for b in blocks:
                b = b.strip()
                if b and "分析词义" in b: all_blocks.append(b)
    return all_blocks

if __name__ == "__main__":
    print("--- 词霸 V2026-FINAL 启动 ---")
    words = load_words()
    if not words:
        print("❌ 没找到单词库"); exit(1)

    progress_file = "BDC/progress.txt"
    curr = 0
    if os.path.exists(progress_file):
        try:
            with open(progress_file, "r") as f: curr = int(f.read().strip())
        except: curr = 0
    
    today = words[curr : curr + 50]
    names = [b.splitlines()[0].replace("#", "").strip() for b in today]
    
    sender, pwd, rcvr = os.environ.get("SENDER_EMAIL"), os.environ.get("SENDER_PWD"), os.environ.get("RECEIVER_EMAIL")
    html = "".join([f"<div style='padding:10px;border-bottom:1px solid #eee;'><b style='color:#e74c3c;font-size:24px;'>{n}</b><br>{b}</div>" for n, b in zip(names, today)])
    
    msg = MIMEMultipart()
    msg['Subject'] = f"🎯 今日单词：{names[0]} 等50词"
    msg['From'], msg['To'] = sender, rcvr
    msg.attach(MIMEText(f"<html><body><h2>词霸 V2026-FINAL</h2>{html}</body></html>", 'html', 'utf-8'))
    
    try:
        s = smtplib.SMTP_SSL("smtp.qq.com", 465)
        s.login(sender, pwd); s.sendmail(sender, [rcvr], msg.as_string()); s.quit()
        with open(progress_file, "w") as f: f.write(str(curr + len(today)))
        print(f"✅ 发送成功！起始词：{names[0]}")
    except Exception as e:
        print(f"❌ 邮件失败: {e}")
