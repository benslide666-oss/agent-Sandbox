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
    url = f"https://newsapi.org/v2/top-headlines?sources=bbc-news&apiKey={NEWS_API_KEY}"
    try:
        res = requests.get(url, timeout=15).json()
        return res.get('articles', [])[:count]
    except: return []

def get_higher_quality_jokes(count=5):
    """尝试抓取更有梗的笑话 (包含 Two-part 反转笑话)"""
    print(f"🚀 正在为王浩寻找有梗的笑话...")
    jokes = []
    # 尝试抓取不同类型的笑话
    url = f"https://v2.jokeapi.dev/joke/Programming,Misc,Pun?blacklistFlags=nsfw,religious,political,racist,sexist,explicit&amount={count}"
    try:
        res = requests.get(url, timeout=15).json()
        for j in res.get('jokes', []):
            if j['type'] == 'single':
                jokes.append(j['joke'])
            else:
                # 这种反转形式通常更幽默
                jokes.append(f"{j['setup']} \n-- {j['delivery']}")
        return jokes
    except:
        return ["My wife told me to stop impersonating a flamingo. I had to put my foot down."]

def main():
    start_time = time.time()
    articles = get_bbc_news(5)
    jokes = get_higher_quality_jokes(5)
    
    # 1. 构造页头 (已更名为王浩)
    header = f"""
    <div style='text-align: center; background: #2c3e50; padding: 20px; color: white; border-radius: 10px;'>
        <h1 style='margin: 0;'>王浩的晨读与幽默</h1>
        <p style='margin: 5px 0 0 0;'>📅 {time.strftime('%Y-%m-%d')} | 既然要学，就开心地学</p>
    </div>
    """

    # 2. 构造新闻内容
    news_html = "<h2 style='color: #b71c1c; border-left: 5px solid #b71c1c; padding-left: 10px; margin-top: 25px;'>🇬🇧 BBC News & IELTS</h2>"
    all_vocab = []
    for i, art in enumerate(articles):
        en_title = art.get('title', '')
        all_vocab.extend(extract_vocab(art.get('description', ''), 1))
        news_html += f"<div style='margin-top: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px;'><b>{i+1}. {en_title}</b><br><span style='font-size: 13px; color: #666;'>{translate_text(en_title)}</span></div>"

    # 3. 构造笑话板块 (优化了反转效果的排版)
    joke_html = "<h2 style='color: #f39c12; border-left: 5px solid #f39c12; padding-left: 10px; margin-top: 30px;'>😆 Daily Puns & Flips (双语反转笑话)</h2>"
    for j in jokes:
        joke_html += f"""
        <div style='background: #fff9c4; padding: 12px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #f1c40f;'>
            <div style='color: #2c3e50; font-size: 14px; font-weight: 500;'>{j.replace('--', '<br><b style="color:#d35400;">→ </b>')}</div>
            <div style='color: #7f8c8d; font-size: 13px; margin-top: 8px; border-top: 1px solid #f9e79f; padding-top: 5px;'>{translate_text(j)}</div>
        </div>
        """

    # 4. 词汇汇总
    vocab_html = ""
    if all_vocab:
        items = "".join([f"<li style='margin-bottom:5px;'>{v}</li>" for v in list(set(all_vocab))[:5]])
        vocab_html = f"<div style='background: #f4f6f7; padding: 15px; border-radius: 10px; margin-top: 20px;'><h3>✍️ IELTS Focus</h3><ul>{items}</ul></div>"

    full_html = header + news_html + vocab_html + joke_html

    # 5. 推送
    payload = {"token": PUSHPLUS_TOKEN, "title": "🌍 王浩的新闻 & 😆 幽默双语简报", "content": full_html, "template": "html"}
    requests.post('http://www.pushplus.plus/send', json=payload)
    print(f"✅ 推送完成，王浩请查收！耗时 {int(time.time()-start_time)}s")

if __name__ == "__main__":
    main()
