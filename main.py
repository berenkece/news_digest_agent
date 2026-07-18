import feedparser
import ollama
import re
import json
import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# .env dosyasindaki degiskenleri yukle (sifreler burada, git'e GITMEZ)
load_dotenv()

GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
MAIL_TO = os.environ.get("MAIL_TO", GMAIL_USER)

file_path = "gonderilen_haberler.json"


def clean(html_text, max_length=150):
    cleaned_text = re.sub('<[^<]+?>', '', html_text)
    return cleaned_text.strip()[:max_length]


def read_previous_news():
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return set(json.load(f))
        except (json.JSONDecodeError, ValueError):
            return set()
    return set()


def save_current_news(links):
    with open(file_path, 'w') as f:
        json.dump(list(links), f, indent=2)


previous_links = read_previous_news()

feed = feedparser.parse('https://www.techmeme.com/feed.xml')

new_links = [e for e in feed.entries if e.link not in previous_links]

if not new_links:
    print("No new news found. No email will be sent.")
else:
    candidates = new_links[:10]

    news = "\n\n".join(
        f"{i}. {entry.title}\n{clean(entry.get('summary', ''))}"
        for i, entry in enumerate(candidates, start=1)
    )

    prompt = f"""Below are tech news items, each with a number.

{news}

Summarize the most important ones. Output ONLY a numbered list.
Each item: one line, headline + one sentence summary.
No headers, no sections, no categories, no repeating items, no links.

Each item MUST start with the exact same number shown next to its
headline above. Do not change or recalculate the numbers."""

    yanit = ollama.chat(
        model="qwen2.5:7b-instruct",
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.3}
    )

    print("HAM CEVAP:", repr(yanit["message"]["content"]))

    splitted_yanit = yanit["message"]["content"].split("\n")
    splitted_yanit = [satir for satir in splitted_yanit if satir.strip() != ""]

    linkli_satirlar = []
    for item in splitted_yanit:
        eslesme = re.match(r'^(\d+)[\.\)]?\s*(.*)', item)
        if eslesme:
            numara = int(eslesme.group(1))
            if 1 <= numara <= len(candidates):
                haber = candidates[numara - 1]
                linkli_satirlar.append(f"{item}\n{haber.link}")
            else:
                linkli_satirlar.append(item)
        elif linkli_satirlar:
            linkli_satirlar[-1] += f"\n{item}"

    if not linkli_satirlar:
        print("Model bosluk/gecersiz cevap dondurdu. Mail atilmadi.")
    else:
        ozet = "\n\n".join(linkli_satirlar)

        mesaj = MIMEText(ozet)
        mesaj["Subject"] = "Tech News Summary"
        mesaj["From"] = GMAIL_USER
        mesaj["To"] = MAIL_TO

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(mesaj)
            server.quit()
        except Exception as e:
            print(f"Email GONDERILEMEDI: {e}")
        else:
            yeni_linkler = {e.link for e in candidates}
            save_current_news(previous_links | yeni_linkler)
            print("Email sent successfully.")