import requests
from bs4 import BeautifulSoup, NavigableString, Comment
from datetime import datetime
import pandas as pd
import os
import time
import re
import urllib3

# Nonaktifkan pesan peringatan SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Konfigurasi ---
CRAWLED_URL_FILE = "../data/crawled_urls.txt"
OUTPUT_CSV_FILE = "../data/scraped_articles.csv"
LOG_FILE = "../data/scrape_logs.txt"

PORTALS_TO_SCRAPE = [
    "Detik-Inet",
    "Gamebrott",
    "Kotakgame",
    "Indogamers",
    "Jagatplay"
]

os.makedirs(os.path.dirname(OUTPUT_CSV_FILE), exist_ok=True)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def log_to_file(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    print(log_entry.strip())
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry)

def read_all_urls_to_scrape(filepath, portal_names):
    log_to_file(f"Membaca SEMUA URL dari {filepath}...")
    all_tasks = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if ';' in line:
                    portal, url = line.strip().split(';', 1)
                    if portal in portal_names:
                        all_tasks.append((portal, url))
        log_to_file(f"Total URL target ditemukan: {len(all_tasks)}")
        return all_tasks
    except FileNotFoundError:
        log_to_file(f"ERROR: File {filepath} tidak ditemukan.")
        return []

def get_already_scraped_urls(filepath):
    """Membaca CSV dan mengembalikan set URL yang sudah di-scrape."""
    if not os.path.exists(filepath):
        return set()
    try:
        df = pd.read_csv(filepath)
        if 'url' in df.columns:
            return set(df['url'])
        else:
            log_to_file("WARNING: Kolom 'url' tidak ditemukan di CSV. Tidak bisa melanjutkan. Harap hapus file CSV lama atau tambahkan kolom 'url'.")
            # Mengembalikan set kosong agar skrip bisa berjalan (tapi akan menimpa) atau hentikan paksa
            return set()
    except pd.errors.EmptyDataError:
        return set() # File ada tapi kosong
    except Exception as e:
        log_to_file(f"Error saat membaca CSV yang ada: {e}. Mengasumsikan file kosong.")
        return set()

# (Semua fungsi scraper individu tidak berubah)
def scrape_gamebrott_article(url, soup):
    title_tag = soup.select_one('h1.jeg_post_title')
    title = title_tag.get_text(strip=True) if title_tag else 'N/A'
    thumb_tag = soup.select_one('.jeg_featured.featured_image .thumbnail-container img')
    thumbnail_url = thumb_tag['src'] if thumb_tag and thumb_tag.has_attr('src') else 'N/A'
    date_tag = soup.select_one('.jeg_meta_date a')
    publish_date = date_tag.get_text(strip=True) if date_tag else 'N/A'
    content_div = soup.select_one('.content-inner')
    if content_div:
        paragraphs = content_div.find_all('p')
        content = '\n'.join([p.get_text(strip=True) for p in paragraphs])
    else: content = 'N/A'
    return {"judul": title, "konten": content, "tanggal_terbit": publish_date, "url_thumbnail": thumbnail_url}
def scrape_kotakgame_article(url, soup):
    title_tag = soup.select_one('h3.judulh3 span.txt9')
    title = title_tag.get_text(strip=True) if title_tag else 'N/A'
    thumb_tag = soup.select_one('div.wrapimg img')
    if thumb_tag and thumb_tag.has_attr('src'):
        relative_url = thumb_tag['src']
        thumbnail_url = f"https://www.kotakgame.com{relative_url}" if relative_url.startswith('/') else relative_url
    else: thumbnail_url = 'N/A'
    date_span = soup.select_one('.boxcreate .txtcreate2')
    if date_span:
        full_text = date_span.get_text(strip=True)
        try:
            match = re.search(r'\|\s*(.*)', full_text)
            publish_date = match.group(1).strip() if match else 'N/A'
        except (AttributeError, IndexError): publish_date = full_text
    else: publish_date = 'N/A'
    content_div = soup.select_one('div.isinewsp')
    content = ""
    if content_div:
        for blockquote in content_div.find_all('blockquote'): blockquote.decompose()
        for insta_block in content_div.find_all(text=re.compile("View this post on Instagram")):
            if insta_block.parent.name in ['div', 'p', 'span']: insta_block.parent.decompose()
        content_full = content_div.get_text(separator='\n', strip=True)
        content_lines = []
        for line in content_full.split('\n'):
            if "Baca ini juga" in line or "Selain berita utama di atas" in line: break
            content_lines.append(line)
        content = '\n'.join(content_lines)
    if not content: content = 'N/A'
    return {"judul": title, "konten": content.strip(), "tanggal_terbit": publish_date, "url_thumbnail": thumbnail_url}
def scrape_indogamers_article(url, soup):
    title_tag = soup.select_one('h1[class*="style_article__title__"]')
    title = title_tag.get_text(strip=True) if title_tag else 'N/A'
    thumb_tag = soup.select_one('div[class*="style_image__article__"] img')
    if thumb_tag and thumb_tag.has_attr('srcset'):
        last_url_part = thumb_tag['srcset'].split(',')[-1].strip()
        relative_url = last_url_part.split(' ')[0]
        thumbnail_url = f"https://indogamers.com{relative_url}"
    else: thumbnail_url = 'N/A'
    date_container = soup.select_one('div[class*="style_author__box__"]')
    publish_date = 'N/A'
    if date_container:
        all_spans = date_container.find_all('span')
        for span in all_spans:
            span_text = span.get_text(strip=True)
            if re.search(r'\b(Senin|Selasa|Rabu|Kamis|Jumat|Sabtu|Minggu)\b', span_text):
                publish_date = span_text.split(',')[0].strip()
                break
    content_div = soup.find('article')
    content = 'N/A'
    if content_div:
        paragraphs = content_div.find_all('p')
        content = '\n'.join([p.get_text(strip=True) for p in paragraphs if not p.has_attr('class') or 'caption' not in ''.join(p['class'])])
    return {"judul": title, "konten": content, "tanggal_terbit": publish_date, "url_thumbnail": thumbnail_url}
def scrape_jagatplay_article(url, soup):
    title = 'N/A'; thumbnail_url = 'N/A'; publish_date = 'N/A'; content = 'N/A'
    title_tag = soup.select_one('div.jgpost__header h1')
    if title_tag: title = title_tag.get_text(strip=True)
    thumb_div = soup.select_one('div.jgpost__feat-img')
    if thumb_div and thumb_div.has_attr('style'):
        match = re.search(r"url\(['\"]?(.*?)['\"]?\)", thumb_div['style'])
        if match: thumbnail_url = match.group(1)
    date_container = soup.select_one('div.jgauthor__posted')
    if date_container:
        child_divs = date_container.find_all('div', recursive=False)
        for div in child_divs:
            if not div.find('a'):
                publish_date = div.get_text(strip=True)
                break
    content_container = soup.select_one('div.jgpost__content')
    if content_container:
        post_content_comment = content_container.find(string=lambda text: isinstance(text, Comment) and "Post Content" in text)
        if post_content_comment:
            content_list = []
            for sibling in post_content_comment.find_next_siblings():
                if sibling.name == 'div' and ('iklan-inline1' in sibling.get('class', []) or 'heateor_sss_sharing_container' in sibling.get('class', [])): break
                if sibling.name == 'p': content_list.append(sibling.get_text(strip=True))
            if content_list: content = '\n'.join(filter(None, content_list))
    return {"judul": title, "konten": content.strip(), "tanggal_terbit": publish_date, "url_thumbnail": thumbnail_url}
def scrape_detikinet_article(url, soup):
    title = 'N/A'; thumbnail_url = 'N/A'; publish_date = 'N/A'; content = 'N/A'
    title_tag = soup.select_one('h1.detail__title')
    if title_tag: title = title_tag.get_text(strip=True)
    date_tag = soup.select_one('div.detail__date')
    if date_tag:
        full_date_text = date_tag.get_text(strip=True)
        try:
            date_part = full_date_text.split(', ')[1]
            publish_date = date_part.split(' WIB')[0].strip()
        except IndexError: publish_date = full_date_text
    thumb_tag = soup.select_one('figure.detail__media-image img')
    if thumb_tag and thumb_tag.has_attr('src'): thumbnail_url = thumb_tag['src']
    content_div = soup.select_one('div#detikdetailtext')
    if content_div:
        elements_to_remove_selectors = ['.collapsible', '.parallaxindetail', '.noncontent', '.staticdetail_container', '.aevp', 'script', 'style', 'table.pic_artikel_sisip_table']
        for selector in elements_to_remove_selectors:
            for element in content_div.select(selector): element.decompose()
        last_strong = content_div.find_all('strong')
        if last_strong and re.match(r'\(\w+/\w+\)', last_strong[-1].get_text(strip=True)): last_strong[-1].decompose()
        paragraphs = content_div.find_all('p')
        content_list = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
        if content_list: content = '\n'.join(content_list)
    return {"judul": title, "konten": content, "tanggal_terbit": publish_date, "url_thumbnail": thumbnail_url}

def main():
    log_to_file("===== Memulai Proses Scraping Skala Penuh (Mode Resume + Real-time Save) =====")
    
    all_tasks = read_all_urls_to_scrape(CRAWLED_URL_FILE, PORTALS_TO_SCRAPE)
    
    header = ['id_dokumen', 'sumber', 'url', 'judul', 'konten', 'tanggal_terbit', 'url_thumbnail']
    
    already_scraped_urls = get_already_scraped_urls(OUTPUT_CSV_FILE)
    if already_scraped_urls:
        log_to_file(f"Ditemukan {len(already_scraped_urls)} URL yang sudah diproses. Akan melanjutkan.")
    
    doc_id_counter = len(already_scraped_urls) + 1
    
    if not os.path.exists(OUTPUT_CSV_FILE) or not already_scraped_urls:
        log_to_file(f"File {OUTPUT_CSV_FILE} tidak ada atau kosong. Membuat file baru dengan header.")
        pd.DataFrame(columns=header).to_csv(OUTPUT_CSV_FILE, index=False)
        doc_id_counter = 1 # Pastikan counter disetel ulang jika file baru
    
    total_urls_to_process = len(all_tasks)
    newly_scraped_count = 0
    
    for i, (portal, url) in enumerate(all_tasks):
        # Lewati URL yang sudah ada
        if url in already_scraped_urls:
            continue
            
        log_to_file(f"  ({i+1}/{total_urls_to_process}) Scraping: {url}")
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=15, verify=False)
            if response.status_code != 200:
                log_to_file(f"    -> Gagal mengakses (Status: {response.status_code})")
                continue
            soup = BeautifulSoup(response.content, 'html.parser')

            data = None
            if portal == "Gamebrott": data = scrape_gamebrott_article(url, soup)
            elif portal == "Kotakgame": data = scrape_kotakgame_article(url, soup)
            elif portal == "Indogamers": data = scrape_indogamers_article(url, soup)
            elif portal == "Jagatplay": data = scrape_jagatplay_article(url, soup)
            elif portal == "Detik-Inet": data = scrape_detikinet_article(url, soup)
            
            if data:
                data['id_dokumen'] = f"doc_{doc_id_counter:05d}"
                data['sumber'] = portal
                data['url'] = url
                
                df_row = pd.DataFrame([data])
                df_row = df_row[header]
                
                df_row.to_csv(OUTPUT_CSV_FILE, mode='a', index=False, header=False)
                
                doc_id_counter += 1
                newly_scraped_count += 1

            time.sleep(0.5)

        except Exception as e:
            log_to_file(f"    -> Terjadi error kritis saat scraping {url}: {e}")

    log_to_file(f"Scraping selesai. Total {newly_scraped_count} artikel BARU berhasil disimpan ke {OUTPUT_CSV_FILE}.")
    log_to_file(f"Proses selesai.\n")

if __name__ == "__main__":
    main()