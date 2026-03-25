import os
import requests
import time
import sys

# 打印第一行，确保我们知道程序启动了
print("--- [系统日志] 程序开始初始化... ---")

try:
    from googletrans import Translator
    print("--- [系统日志] 翻译插件加载成功 ---")
except Exception as e:
    print(f"❌ [严重错误] 无法加载翻译插件: {e}")
    sys.exit(1)

# ================= 安全配置区 =================
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
PUSHPLUS_TOKEN = os.getenv('PUSHPLUS_TOKEN')
# ============================================

def translate_text(translator, text):
    """翻译函数：带错误捕获"""
    if not text or len(text.strip()) == 0:
        return "暂无内容"
    try:
        # 增加超时设置
        result = translator.translate(text, dest='zh-cn')
        return result.text
    except Exception as e:
        print(f"⚠️ 翻译微报错 (将返回原文): {e}")
        return text

def get_news_data(category, count=8):
    """抓取新闻"""
    print(f"🚀 正在抓取 {category} 类目新闻...")
    url = f"https://newsapi.org/v2/top-headlines?category={category}&language=en&pageSize={count}&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(url, timeout=15)
        articles = response.json().get('articles', [])
        print(f"✅ 成功抓取 {len(articles)} 条 {category} 新闻")
        return articles
    except Exception as e:
        print(f"❌ 获取新闻失败: {e}")
        return []

def main():
    # 在函数内部初始化翻译器，防止全局卡死
    try:
        translator = Translator()
    except Exception as e:
        print(f"❌ 翻译器初始化失败: {e}")
        return

    start_time = time.time()
    
    # 1. 抓取数据
    hot_articles = get_news_data('general', 8)
    med_articles = get_news_data('health', 8)

    if not hot_articles and not med_articles:
        print("⚠️ 未抓取到任何新闻，请检查 NEWS_API_KEY 是否正确。")
        return

    # 2. 构造 HTML (精简版排版)
    html = f"<h1 style='color: #1a73e8;'>早安，子超！</h1>"
    
    # 全球新闻板块
    html += "<h2>🌟 今日全球焦点</h2>"
    for art in hot_articles:
        title = translate_text(translator, art.get('title', '无标题'))
        html += f"<p><b>· {title}</b> <br> <a href='{art['url']}'>查看原文</a></p>"
    
    # 医药健康板块
    html += "<h2>💊 医药健康前沿</h2>"
    for art in med_articles:
        title = translate_text(translator, art.get('title', '无标题'))
        html += f"<p><b>· {title}</b> <br> <a href='{art['url']}'>查看原文</a></p>"

    # 3. 推送
    print(f"📨 正在推送至微信 (内容长度: {len(html)})...")
    payload = {
        "token": PUSHPLUS_TOKEN,
        "title": "🌍 每日双语资讯简报",
        "content": html,
        "template": "html"
    }
    
    try:
        res = requests.post('http://www.pushplus.plus/send', json=payload, timeout=20)
        print(f"✅ 推送任务完成！服务器回复: {res.text}")
    except Exception as e:
        print(f"❌ 推送过程出错: {e}")

if __name__ == "__main__":
    main()