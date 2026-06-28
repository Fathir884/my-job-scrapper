import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import datetime

# --- CONFIGURATION ---
SENDER_EMAIL = os.environ.get("SENDER_EMAIL") 
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "fathir.ramadhan04@gmail.com")

KEYWORDS = ["React", "Node.js", "KOL", "Administrasi", "Arsip", "Pustakawan", "Document Control"]
LOCATIONS = ["Jakarta", "Remote"]

def scrape_kalibrr(keyword, location):
    print(f"Scraping Kalibrr for '{keyword}' in '{location}'...")
    jobs = []
    
    kw_url = keyword.replace(" ", "-").lower()
    loc_url = location.replace(" ", "-").lower()
    
    url = f"https://www.kalibrr.com/job-board/te/{kw_url}/l/{loc_url}/1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        
        links = soup.find_all("a", href=True)
        job_links = []
        for a in links:
            href = a['href']
            if "/jobs/" in href and "/c/" in href:
                full_link = f"https://www.kalibrr.com{href}" if href.startswith("/") else href
                title = a.text.strip()
                if title and full_link not in [j['link'] for j in jobs]:
                    if len(title) > 4 and title.lower() != "apply now":
                        jobs.append({
                            "title": title,
                            "link": full_link,
                            "keyword": keyword,
                            "location": location
                        })
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        
    return jobs

def send_email(jobs_found):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("Error: Email credentials not set.")
        return

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🚀 Job Scraper Daily Report - {datetime.date.today()}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    html = f"""\
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>Halo Fathir! 👋</h2>
        <p>Berikut adalah daftar lowongan pekerjaan terbaru yang sesuai dengan CV kamu hari ini ({datetime.date.today()}):</p>
        <hr>
    """
    
    if jobs_found:
        html += "<ul>"
        for job in jobs_found:
            html += f"""
            <li style="margin-bottom: 15px;">
                <strong>{job['title']}</strong><br>
                <em style="color: #666; font-size: 13px;">Kategori: {job['keyword']} | Lokasi: {job['location']}</em><br>
                <a href="{job['link']}" style="color: #0066cc; text-decoration: none; font-weight: bold;">&rarr; Lihat Detail & Apply</a>
            </li>
            """
        html += "</ul>"
    else:
        html += "<p><em>Sayang sekali, hari ini belum ada lowongan baru yang cocok. Tetap semangat!</em></p>"

    html += """
        <hr>
        <p style="font-size: 12px; color: #777;">Email ini dikirim secara otomatis oleh sistem Job Scraper Fathir.</p>
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
        print("Email report sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():
    print("Starting Job Scraper...")
    all_jobs = []
    
    for kw in KEYWORDS:
        for loc in LOCATIONS:
            jobs = scrape_kalibrr(kw, loc)
            all_jobs.extend(jobs)
            
    # Remove duplicates
    unique_jobs = list({job['link']: job for job in all_jobs}.values())
    
    print(f"Total unique jobs found: {len(unique_jobs)}")
    send_email(unique_jobs)

if __name__ == "__main__":
    main()
