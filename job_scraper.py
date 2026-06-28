import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import datetime
import google.generativeai as genai
import time

# --- CONFIGURATION ---
SENDER_EMAIL = os.environ.get("SENDER_EMAIL") 
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "fathir.ramadhan04@gmail.com")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

KEYWORDS = ["React", "Node.js", "KOL", "Administrasi", "Arsip", "Pustakawan", "Document Control"]
LOCATIONS = ["Jakarta", "Remote"]

def generate_cover_letter(job_title):
    if not GEMINI_API_KEY:
        return "Fitur AI belum aktif. Tambahkan GEMINI_API_KEY di GitHub Secrets."
    try:
        prompt = f"Write a very short, one-paragraph cover letter snippet (max 3 sentences) in English applying for the '{job_title}' role. My profile: Fathir Ramadhan, final-year Library Science student at UIN Jakarta. Experience: National Library of Indonesia (Archive Digitization, React/Node.js web dev), KOL Specialist at Exioncare. Skills: React.js, Node.js, Admin, Archives, Communication. Make it punchy, professional, and directly highlight why my unique background fits this role. Do not include placeholders like [Company Name] or greetings/sign-offs, just the core paragraph."
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        
        response = requests.post(url, headers=headers, json=data, timeout=15)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        else:
            return f"API Error {response.status_code}: {response.text[:100]}"
    except Exception as e:
        return f"Request Error: {e}"

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
                        # Limit to 2 jobs per keyword-location combo to avoid rate limits & long emails
                        if len(jobs) >= 2:
                            break
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        
    return jobs

def send_email(jobs_found):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("Error: Email credentials not set.")
        return

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🚀 Loker & Draf AI - {datetime.date.today()}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    html = f"""\
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.5;">
        <h2>Halo Fathir! 👋</h2>
        <p>Berikut loker terbaru untukmu, dilengkapi dengan **Draf Cover Letter dari AI**:</p>
        <hr>
    """
    
    if jobs_found:
        for job in jobs_found:
            html += f"""
            <div style="margin-bottom: 25px; padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
                <h3 style="margin-top: 0; color: #0056b3;">{job['title']}</h3>
                <p style="font-size: 13px; color: #666; margin-bottom: 10px;">Kategori: {job['keyword']} | Lokasi: {job['location']}</p>
                <div style="background-color: #f9f9f9; padding: 10px; border-left: 4px solid #4CAF50; font-size: 14px; font-style: italic;">
                    <strong>🤖 Draf AI Cover Letter:</strong><br><br>
                    {job['ai_cover_letter']}
                </div>
                <br>
                <a href="{job['link']}" style="display: inline-block; background-color: #0056b3; color: white; padding: 8px 15px; text-decoration: none; border-radius: 4px; font-weight: bold;">Lamar Sekarang &rarr;</a>
            </div>
            """
    else:
        html += "<p><em>Belum ada lowongan baru hari ini.</em></p>"

    html += """
        <hr>
        <p style="font-size: 12px; color: #777;">Automasi oleh Job Scraper + Gemini AI.</p>
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
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():
    print("Starting Job Scraper Phase 2...")
    all_jobs = []
    
    for kw in KEYWORDS:
        for loc in LOCATIONS:
            jobs = scrape_kalibrr(kw, loc)
            all_jobs.extend(jobs)
            
    # Remove duplicates
    unique_jobs = list({job['link']: job for job in all_jobs}.values())
    
    # Cap at 10 jobs total to avoid massive emails & API limits
    unique_jobs = unique_jobs[:10]
    
    print(f"Generating AI Cover Letters for {len(unique_jobs)} jobs...")
    for job in unique_jobs:
        job['ai_cover_letter'] = generate_cover_letter(job['title'])
        print(f"- Generated for: {job['title']}")
    
    send_email(unique_jobs)

if __name__ == "__main__":
    main()
