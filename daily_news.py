import os
import requests
import time
import re
from googletrans import Translator

# ================= 配置区 =================
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
PUSHPLUS_TOKEN = os.getenv('PUSHPLUS_TOKEN')
# ==========================================

translator = Translator()

def translate_text(text):
    if not text: return ""
    try:
        return translator.translate(text, dest='zh-cn').text
    except:
        return text

def extract_vocab(text, count=3):
    """提取雅思词汇"""
    words = re.findall(r'\b[a-zA-Z]{8,}\b', text) 
    unique_words = list(set(words))
    vocab_list = []
    for word in unique_words[:count]:
        cn = translate_text(word)
        if cn.lower() != word.lower():
            vocab_list.append(f"<b>{word}</b>: {cn}")
    return vocab_list

def get_bbc_news(count=5):
    """抓取 BBC 新闻"""
    print("🚀 正在抓取 BBC News...")
    url = f"https://newsapi.org/v2/top-headlines?sources=bbc-news&apiKey={NEWS_API_KEY}"
    try:
        res = requests.get(url, timeout=15).json()
        return res.get('articles', [])[:count]
    except: return []

def get_jokes(count=5):
    """抓取全球冷笑话 (安全模式)"""
    print(f"🚀 正在抓取 {count} 个冷笑话...")
    url = f"https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,religious,political,racist,sexist,explicit&type=single&amount={count}"
    try:
        res = requests.get(url, timeout=15).json()
        jokes = res.get('jokes', [])
        return [j['joke'] for j in jokes]
    except:
        return ["Why don't scientists trust atoms? Because they make up everything!"]

def main():
    start_time = time.time()
    
    # 1. 抓取数据
    articles = get_bbc_news(5)
    jokes = get_jokes(5)
    
    # 2. 构造页头
    header = f"""
    <div style='text-align: center; background: #2c3e50; padding: 20px; color: white; border-radius: 10px;'>
        <h1 style='margin: 0;'>子超的晨读与幽默</h1>
        <p style='margin: 5px 0 0 0;'>📅 {time.strftime('%Y-%m-%d')} | 学习也要好心情</p>
    </div>
    """

    # 3. 构造新闻与词汇内容
    news_html = "<h2 style='color: #b71c1c; border-left: 5px solid #b71c1c; padding-left: 10px; margin-top: 25px;'>🇬🇧 BBC News & IELTS</h2>"
    all_vocab = []
    for i, art in enumerate(articles):
        en_title = art.get('title', '')
        en_desc = art.get('description', '')
        all_vocab.extend(extract_vocab(en_desc, 1))
        news_html += f"""
        <div style='margin-top: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px;'>
            <div style='font-weight: bold; color: #333;'>{i+1}. {en_title}</div>
            <div style='font-size: 13px; color: #666;'>{translate_text(en_title)}</div>
            <a href='{art['url']}' style='color: #1a73e8; font-size: 11px; text-decoration: none;'>View Details</a>
        </div>
        """

    # 4. 构造笑话板块 (新增)
    joke_html = "<h2 style='color: #f39c12; border-left: 5px solid #f39c12; padding-left: 10px; margin-top: 30px;'>😆 Morning Laughter (双语笑话)</h2>"
    for i, jk in enumerate(jokes):
        cn_jk = translate_text(jk)
        joke_html += f"""
        <div style='background: #fff9c4; padding: 12px; border-radius: 8px; margin-bottom: 15px;'>
            <div style='color: #444; font-size: 14px; font-style: italic;'>"{jk}"</div>
            <div style='color: #7f8c8d; font-size: 13px; margin-top: 5px;'><b>译：</b>{cn_jk}</div>
        </div>
        """

    # 5. 词汇总结
    vocab_html = ""
    if all_vocab:
        items = "".join([f"<li style='margin-bottom:5px;'>{v}</li>" for v in list(set(all_vocab))[:5]])
        vocab_html = f"<div style='background: #f1f8e9; padding: 15px; border-radius: 10px; margin-top: 20px;'><h3>✍️ IELTS Focus</h3><ul>{items}</ul></div>"

    full_html = header + news_html + vocab_html + joke_html

    # 6. 推送
    print(f"📨 正在推送至微信 (长度: {len(full_html)})...")
    payload = {"token": PUSHPLUS_TOKEN, "title": "🌍 BBC新闻 + 😆 每日笑话", "content": full_html, "template": "html"}
    requests.post('http://www.pushplus.plus/send', json=payload)
    print(f"✅ 任务完成，耗时 {int(time.time()-start_time)} 秒")

if __name__ == "__main__":
    main()
