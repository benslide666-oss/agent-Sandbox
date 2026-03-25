import os
import requests
import time
from googletrans import Translator

# ================= 安全配置区 =================
# 从 GitHub Secrets 中自动读取密钥
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
PUSHPLUS_TOKEN = os.getenv('PUSHPLUS_TOKEN')
# ============================================

translator = Translator()

def translate_text(text):
    """翻译函数：将英文翻译为中文"""
    if not text or len(text.strip()) == 0:
        return "暂无摘要内容"
    try:
        # 尝试翻译，dest='zh-cn' 表示目标语言为简体中文
        result = translator.translate(text, dest='zh-cn')
        return result.text
    except Exception as e:
        print(f"翻译出错: {e}")
        return text # 翻译失败则返回原文

def get_news_data(category, count=20):
    """获取指定类目的全球新闻"""
    print(f"🚀 正在抓取 {category} 类目新闻...")
    url = f"https://newsapi.org/v2/top-headlines?category={category}&language=en&pageSize={count}&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(url, timeout=20)
        return response.json().get('articles', [])
    except Exception as e:
        print(f"获取新闻失败: {e}")
        return []

def format_news_section(articles, section_title):
    """格式化新闻板块：标题(中) + 摘要(中) + 链接"""
    html = f"<h2 style='color: #2c3e50; border-left: 5px solid #3498db; padding-left: 10px;'>🌟 {section_title}</h2>"
    
    if not articles:
        return html + "<p>未能获取到相关新闻，请检查 API 状态。</p>"

    for i, art in enumerate(articles):
        # 翻译标题和摘要
        title_cn = translate_text(art.get('title', '无标题'))
        desc_cn = translate_text(art.get('description', '作者未提供内容摘要'))
        
        # 组装 HTML
        html += f"""
        <div style='margin-bottom: 25px; border-bottom: 1px dashed #ddd; padding-bottom: 10px;'>
            <div style='font-weight: bold; font-size: 16px; color: #333;'>{i+1}. {title_cn}</div>
            <p style='font-size: 14px; color: #666; line-height: 1.6;'><b>中文摘要：</b>{desc_cn}</p>
            <a href='{art['url']}' style='color: #3498db; text-decoration: none; font-size: 13px;'>🔗 阅读原文 (English)</a>
        </div>
        """
        # 控制速度，避免被翻译 API 封锁
        time.sleep(0.4)
        print(f"已处理 {section_title} 第 {i+1} 条...")
        
    return html

def get_daily_quote():
    """额外功能：获取每日一句英语（助力雅思学习）"""
    try:
        res = requests.get("https://api.quotable.io/random?tags=inspirational", timeout=5).json()
        en = res['content']
        cn = translate_text(en)
        return f"<div style='background: #f1f9ff; padding: 15px; border-radius: 10px; margin-bottom: 20px;'><b>💡 雅思每日金句：</b><br><i>{en}</i><br>{cn}</div>"
    except:
        return ""

def main():
    start_time = time.time()
    
    # 头部个性化信息
    header = f"<h1 style='text-align: center; color: #1a73e8;'>早安，子超！</h1>"
    header += f"<p style='text-align: center; color: #888;'>📅 2026年3月25日 全球资讯准时送达</p>"
    header += get_daily_quote()

    # 1. 抓取全球热门 (20条)
    hot_news = get_news_data('general', 20)
    hot_html = format_news_section(hot_news, "今日全球焦点")

    # 2. 抓取医药健康 (20条)
    med_news = get_news_data('health', 20)
    med_html = format_news_section(med_news, "医药健康前沿")

    # 合并推送内容
    full_content = header + hot_html + med_html
    
    # 推送至微信
    print("📨 正在发送至微信...")
    push_url = 'http://www.pushplus.plus/send'
    payload = {
        "token": PUSHPLUS_TOKEN,
        "title": "🌍 每日全球 & 医药双重简报",
        "content": full_content,
        "template": "html"
    }
    
    try:
        res = requests.post(push_url, json=payload)
        print(f"✅ 推送任务完成！响应结果: {res.text}")
    except Exception as e:
        print(f"❌ 推送失败: {e}")

    print(f"⏱️ 总耗时: {int(time.time() - start_time)} 秒")

if __name__ == "__main__":
    main()