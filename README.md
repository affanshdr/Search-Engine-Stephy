# Gamebrank — Search Engine for Indonesian Video Game News

A domain-specific information retrieval system for Indonesian-language game news. Gamebrank crawls articles from 4 major Indonesian game news portals and lets users search through them using two ranking approaches: BM25 (lexical) and Sentence-BERT (semantic).

---

## Screenshots

**Homepage**

<!-- Add screenshot of homepage here -->

![Homepage](images/homepage.png)

**Search Results**

<!-- Add screenshot of search results page here -->

![Search Results](images/search_results.png)

---

## Features

- Crawls and indexes articles from Kotakgame, Gamebrott, Jagatplay, and Indogamers
- Full text preprocessing pipeline with selective stemming and domain-specific whitelist
- Dual retrieval: BM25 for keyword-based search, Sentence-BERT for semantic search
- Each result card shows article title (hyperlinked), source portal, publication date, content snippet, and thumbnail

---

## Tech Stack

| Component  | Technology                                     |
| ---------- | ---------------------------------------------- |
| Backend    | Python, Flask                                  |
| Frontend   | HTML, CSS                                      |
| Crawling   | Requests, BeautifulSoup                        |
| NLP        | Sastrawi, NLTK                                 |
| Retrieval  | rank-bm25, Sentence-Transformers (HuggingFace) |
| Evaluation | Cross-Encoder MS-MARCO                         |

---

## Project Structure

```
gamebrank/
├── app.py                  # Flask application entry point
├── evaluation/
│   ├── df_corpus_clean.csv     # Cleaned dataset
│   ├── eval_result.txt         # Evaluation result for both algorithms
│   ├── generated_queries.json  # LLM generated queries for evaluation
│   ├── ground_truth.json       # Ground truth for evaluation
│   ├── retrieval_pool.json     #
│   └── sample_berita_100.csv   # 100 random articles sample for evaluation
├── data/
│   └── scraped_articles.csv   # Not included in repo. Crawled article links.
├── models/ # Not included in repo
├── notebook/
│   └── ir_pipeline.ipynb   # Full scraping to evaluation pipeline
├── templates/
│   ├── about.html          # About Page
│   ├── index.html          # Homepage
│   └── results.html        # Search results page
├── static/
│   └── style.css
└── requirements.txt
```

---

## Evaluation Results

Evaluation was conducted on 400 queries against a dataset of 2,020 articles. Relevance ground truth was generated automatically using a Cross-Encoder MS-MARCO model from HuggingFace. Results are based on top-10 retrieved documents per query.

| Metric         | BM25 (Lexical) | S-BERT (Semantic) |
| -------------- | -------------- | ----------------- |
| Mean Precision | 0.2566         | 0.2002            |
| Mean Recall    | 0.8443         | 0.6596            |
| Mean F1-Score  | 0.3378         | 0.2616            |
| MAP            | 0.7358         | 0.5005            |

BM25 outperformed S-BERT across all metrics. The main reason is that game news content is heavily keyword-driven — exact terms like game titles ("Mobile Legends", "PUBG Mobile") and technical jargon require exact matching rather than semantic understanding. S-BERT is likely less effective here because it was not fine-tuned on Indonesian game-domain text.

---

## Authors

- [Affan Suhendar](https://github.com/affanshdr) — 2308107010003
- [Muhammad Faruqi](https://github.com/mfaruqi35) — 2308107010005

Universitas Syiah Kuala, Informatics — Information Retrieval Course, November 2025
