import pandas as pd
import datetime
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# --- 配置区 ---
DUTY_LIST = ["张明亮", "陶伟", "王风清", "王浩", "贡小春", "杨庆华"]
ANCHOR_DATE = datetime.date(2026, 1, 1)

def generate_report():
    today = datetime.date.today()
    first_day_this_month = today.replace(day=1)
    last_day_last_month = first_day_this_month - datetime.timedelta(days=1)
    first_day_last_month = last_day_last_month.replace(day=1)
    
    month_str = first_day_last_month.strftime("%Y年%m月")
    filename = f"{month_str}行政值班统计表.xlsx"

    dates, names, weekdays = [], [], []
    current_date = first_day_last_month
    while current_date <= last_day_last_month:
        days_diff = (current_date - ANCHOR_DATE).days
        person_index = days_diff % len(DUTY_LIST)
        dates.append(current_date.strftime("%Y-%m-%d"))
        names.append(DUTY_LIST[person_index])
        weekdays.append(["周一","周二","周三","周四","周五","周六","周日"][current_date.weekday()])
        current_date += datetime.timedelta(days=1)

    df_detail = pd.DataFrame({"日期": dates, "星期": weekdays, "值班人员": names})
    df_summary = df_detail["值班人员"].value_counts().reset_index()
    df_summary.columns = ["姓名", f"{first_day_last_month.month}月值班天数"]

    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df_summary.to_excel(writer, sheet_name="统计摘要", index=False)
        df_detail.to_excel(writer, sheet_name="值班明细", index=False)
    
    return filename, month_str

def send_email(file_path, month_str):
    # 直接读取背单词项目已有的环境变量名
    sender = os.environ.get("SENDER_EMAIL")
    password = os.environ.get("SENDER_PWD")
    receiver = os.environ.get("RECEIVER_EMAIL")

    msg = MIMEMultipart()
    msg['Subject'] = f"📅 行政值班统计：{month_str}"
    msg['From'], msg['To'] = sender, receiver
    
    msg.attach(MIMEText(f"您好，附件为您上个月（{month_str}）的行政值班统计表，由 AI 自动生成。", 'plain'))

    with open(file_path, "rb") as f:
        part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        msg.attach(part)

    with smtplib.SMTP_SSL("smtp.qq.com", 465) as server:
        server.login(sender, password)
        server.send_message(msg)
    print("✅ 值班报表已通过现有 Secrets 发送成功！")

if __name__ == "__main__":
    file, m_str = generate_report()
    send_email(file, m_str)
