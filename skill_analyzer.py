import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import datetime
from collections import Counter
import re

# --- CONFIGURATION ---
SENDER_EMAIL = os.environ.get("SENDER_EMAIL") 
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "fathir.ramadhan04@gmail.com")

KEYWORDS_TO_TRACK = [
    "React", "Node.js", "TypeScript", "Next.js", "Express", "MongoDB", "SQL", 
    "API", "Figma", "Excel", "Canva", "Public Speaking", "English", "KOL", "TikTok"
]

def analyze_market_skills():
    print("Menganalisis tren skill pasar...")
    # Kita ambil sampel 3 halaman pertama untuk kata kunci umum "IT" dan "Marketing"
    search_queries = ["frontend", "backend", "marketing", "admin"]
    text_corpus = ""
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    for query in search_queries:
        try:
            # Menggunakan route lokasi yang pasti valid (jakarta)
            url = f"https://www.kalibrr.com/job-board/te/{query}/l/jakarta/1"
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")
                # Kita ambil teks dari semua elemen yang berpotensi memiliki deskripsi/judul
                text_corpus += " " + soup.get_text().lower()
        except Exception as e:
            print(f"Error pada query {query}: {e}")
            
    # Menghitung kemunculan kata kunci
    skill_counts = {}
    for skill in KEYWORDS_TO_TRACK:
        # Gunakan regex agar cocokan kata pas (boundaries) atau sekadar sub-string
        count = text_corpus.count(skill.lower())
        if count > 0:
            skill_counts[skill] = count
            
    # Urutkan dari yang terbanyak
    sorted_skills = sorted(skill_counts.items(), key=lambda item: item[1], reverse=True)
    return sorted_skills

def send_skill_report(skills_data):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("Error: Email credentials not set.")
        return

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"📊 Laporan Tren Skill Harian - {datetime.date.today()}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    html = f"""\
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.5;">
        <h2>Halo Fathir! 📈</h2>
        <p>Berikut adalah hasil analisis tren skill / teknologi yang paling banyak dicari oleh perusahaan di Indonesia hari ini:</p>
        
        <table style="width: 100%; max-width: 500px; border-collapse: collapse; margin-bottom: 20px;">
            <tr style="background-color: #f2f2f2;">
                <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Skill / Keyword</th>
                <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">Skor Kemunculan</th>
            </tr>
    """
    
    if skills_data:
        for skill, count in skills_data:
            html += f"""
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">{skill}</td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{count}</td>
            </tr>
            """
    else:
        html += "<tr><td colspan='2' style='padding: 10px; text-align: center;'>Data belum memadai hari ini.</td></tr>"

    html += """
        </table>
        <p style="font-size: 14px; color: #555;"><strong>Tips:</strong> Pelajari skill yang berada di posisi 3 teratas untuk meningkatkan nilai jual CV-mu secara drastis!</p>
        <hr>
        <p style="font-size: 12px; color: #777;">Automasi oleh Job Scraper - Skill Analyzer.</p>
      </body>
    </html>
    """
    
    part2 = MIMEText(html, 'html')
    msg.attach(part2)

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print("Skill report sent successfully!")
    except Exception as e:
        print(f"Failed to send skill report: {e}")

if __name__ == "__main__":
    print("Starting Skill Analyzer...")
    trends = analyze_market_skills()
    send_skill_report(trends)
