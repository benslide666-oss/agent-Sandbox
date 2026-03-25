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
    """翻译函数"""
    if not text: return ""
    try:
        return translator.translate(text, dest='zh-cn').text
    except:
        return text

def extract_vocab(text, count=3):
    """从文本中提取潜在的雅思高频词汇（简单逻辑：筛选长度大于7的学术感单词）"""
    # 移除标点并转为小写，提取所有单词
    words = re.findall(r'\b[a-zA-Z]{8,}\b', text) 
    # 去重并过滤掉一些极其常见的词（可选）
    unique_words = list(set(words))
    # 选取前 count 个单词进行翻译
    vocab_list = []
    for word in unique_words[:count]:
        cn = translate_text(word)
        if cn.lower() != word.lower(): # 确保翻译成功
            vocab_list.append(f"<b>{word}</b>: {cn}")
    return vocab_list

def get_bbc_news(count=5):
    """抓取 BBC News"""
    print("🚀 正在抓取 BBC News...")
    url = f"https://newsapi.org/v2/top-headlines?sources=bbc-news&apiKey={NEWS_API_KEY}"
    try:
        res = requests.get(url, timeout=15).json()
        return res.get('articles', [])[:count]
    except:
        return []

def main():
    start_time = time.time()
    articles = get_bbc_news(5)
    
    if not articles:
        print("未能抓取到新闻")
        return

    # 1. 构造页头
    header = f"""
    <div style='text-align: center; background: #b71c1c; padding: 20px; color: white; border-radius: 10px;'>
        <h1 style='margin: 0;'>王浩的 BBC 雅思晨读</h1>
        <p style='margin: 5px 0 0 0;'>📅 {time.strftime('%Y-%m-%d')} | 目标：CUHK</p>
    </div>
    """

    # 2. 构造新闻与词汇内容
    content_html = ""
    all_vocab = []

    for i, art in enumerate(articles):
        en_title = art.get('title', '')
        en_desc = art.get('description', '')
        
        # 提取本条新闻中的生词
        vocabs = extract_vocab(en_desc, 2)
        all_vocab.extend(vocabs)

        content_html += f"""
        <div style='margin-top: 20px; border-bottom: 2px solid #f0f0f0; padding-bottom: 15px;'>
            <div style='font-size: 16px; font-weight: bold; color: #b71c1c;'>{i+1}. {en_title}</div>
            <div style='font-size: 14px; color: #888; margin: 4px 0;'>{translate_text(en_title)}</div>
            <p style='font-size: 14px; color: #444; line-height: 1.6; background: #f9f9f9; padding: 10px; border-radius: 5px;'>
                {en_desc}<br>
                <span style='color: #666; font-size: 13px;'>[译]: {translate_text(en_desc)}</span>
            </p>
            <a href='{art['url']}' style='color: #1a73e8; text-decoration: none; font-size: 12px;'>🔗 Read Full Story</a>
        </div>
        """
        time.sleep(0.3)

    # 3. 构造雅思词汇划重点板块
    vocab_section = ""
    if all_vocab:
        # 去重并取前 5 个
        final_vocab = list(set(all_vocab))[:5]
        vocab_items = "".join([f"<li style='margin-bottom:5px;'>{item}</li>" for item in final_vocab])
        vocab_section = f"""
        <div style='margin-top: 25px; padding: 15px; background: #fffde7; border: 1px solid #fff176; border-radius: 10px;'>
            <h3 style='margin-top: 0; color: #f57f17;'>✍️ IELTS Vocabulary Focus</h3>
            <ul style='font-size: 14px; color: #333; padding-left: 20px;'>
                {vocab_items}
            </ul>
            <p style='font-size: 12px; color: #999;'>* 建议尝试用以上单词造句，助力港中文申请文书。</p>
        </div>
        """

    full_html = header + content_html + vocab_section

    # 4. 推送
    print(f"📨 正在推送 (长度: {len(full_html)})...")
    payload = {
        "token": PUSHPLUS_TOKEN,
        "title": "🇬🇧 BBC News & IELTS Vocab",
        "content": full_html,
        "template": "html"
    }
    requests.post('http://www.pushplus.plus/send', json=payload)
    print(f"✅ 任务完成，耗时 {int(time.time()-start_time)} 秒")

if __name__ == "__main__":
    main()