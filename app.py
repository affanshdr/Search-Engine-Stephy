import math # .....
from flask import Flask, request, render_template, redirect, url_for
import pickle
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from sklearn.metrics.pairwise import cosine_similarity
import re
import os

# TES
app = Flask(__name__)

MODEL_DIR = "models/"
BM25_MODEL_PATH = os.path.join(MODEL_DIR, 'bm25_model.pkl')
CORPUS_DF_PATH = os.path.join(MODEL_DIR, 'df_corpus.pkl')
SBERT_EMBEDDINGS_PATH = os.path.join(MODEL_DIR, 'sbert_embeddings.npy')
SBERT_MODEL_PATH = os.path.join(MODEL_DIR, 'sbert_model.pkl')

RESULTS_PER_PAGE = 10 # ......

ASSETS = {}
BM25_K1 = 1.2
BM25_B = 0.75

def load_assets():
    global ASSETS
    try:
        with open(BM25_MODEL_PATH, 'rb') as f:
            ASSETS['bm25_model'] = pickle.load(f)

        ASSETS['corpus_df'] = pd.read_pickle(CORPUS_DF_PATH)
        ASSETS['sbert_embeddings'] = np.load(SBERT_EMBEDDINGS_PATH)

        with open(SBERT_MODEL_PATH, 'rb') as f:
            model_name = pickle.load(f)
        
        ASSETS['sbert_model'] = SentenceTransformer(model_name)
        print("Semua aset Indexing (BM25 & SBERT) berhasil dimuat")

    except FileNotFoundError as e:
        print(f"ERROR: File aset tidak ditemukan: {e}")
        raise FileNotFoundError(f"Gagal memuat aset: {e}")
    except Exception as e:
        print(f"ERROR saat memuat aset: {e}")
        raise Exception(f"Gagal memuat model: {e}")

def search_bm25(query_tokens, top_k):
    doc_scores = ASSETS['bm25_model'].get_scores(query_tokens)
    ranked_indices = np.argsort(doc_scores)[::-1]

    results = ASSETS['corpus_df'].iloc[ranked_indices[:top_k]].copy()
    results['score'] = doc_scores[ranked_indices[:top_k]]
    results['algorithm'] = 'BM25'

    return results

def search_sbert(query, top_k):
    query_embedding = ASSETS['sbert_model'].encode(query, convert_to_tensor=False)
    
    similarities = cosine_similarity(query_embedding.reshape(1, -1), ASSETS['sbert_embeddings'])[0]
    
    ranked_indices = np.argsort(similarities)[::-1]
    
    results = ASSETS['corpus_df'].iloc[ranked_indices[:top_k]].copy()
    results['score'] = similarities[ranked_indices[:top_k]]
    results['algorithm'] = 'S-BERT'
    
    return results

def run_combined_search(raw_query, top_k=50):
    bm25_query_tokens = str(raw_query).lower().split()

    bm25_results = search_bm25(bm25_query_tokens, top_k)
    sbert_results = search_sbert(raw_query, top_k)

    bm25_results = bm25_results.reset_index(drop=True)
    sbert_results = sbert_results.reset_index(drop=True)

    combined_df = pd.concat([
        bm25_results,
        sbert_results
    ])

    combined_df['rank'] = combined_df.groupby('algorithm').cumcount() + 1
    combined_df = combined_df.sort_values(by='algorithm', ascending=False)

    return combined_df[[
        'judul', 'url', 'score', 'algorithm', 'sumber', 'tanggal_terbit', 'rank', 'url_thumbnail'
    ]].to_dict('records')

def get_latest_news(num_items=9):
    df = ASSETS['corpus_df'].copy()

    if 'timestamp' in df.columns:
        latest_df = df.sort_values(by='timestamp', ascending=False)
    else:
        latest_df = df.sort_values(by='id_dokumen', ascending=False)

    # Mulai dari indeks ke-4 (skip 3 item rusak)
    latest_df = latest_df.iloc[11:11 + num_items]

    return latest_df[[
        'judul', 'url', 'url_thumbnail', 'tanggal_terbit', 'sumber'
    ]].to_dict('records')


@app.route('/', methods=['GET'])
def index():
    latest_news = get_latest_news(num_items=9)
    return render_template('index.html', latest_news=latest_news)

# @app.route('/search', methods=['GET'])
# def search_results():
#     query = request.args.get('query')
#     results = []

#     if query:
#         try:
#             results = run_combined_search(query, top_k=5)
#         except Exception as e:
#             print(f"ERROR saat melakukan pencarian: {e}")
#             results = []

#     if query:
#         return render_template('result.html', results=results, query=query)
#     else:
#         return redirect(url_for('index'))
    
@app.route('/search', methods=['GET'])
def search_results():
    query = request.args.get('query')
    page = request.args.get('page', 1, type=int)  # <- tambah ini
    results = []
    total_results = 0  # <- tambah ini
    total_pages = 0    # <- tambah ini
    
    if query:
        try:
            all_results = run_combined_search(query, top_k=50)
            total_results = len(all_results)  # <- tambah ini
            total_pages = math.ceil(total_results / RESULTS_PER_PAGE)  # <- tambah ini
            
            # Pagination - tambah 3 baris ini
            start_idx = (page - 1) * RESULTS_PER_PAGE
            end_idx = start_idx + RESULTS_PER_PAGE
            results = all_results[start_idx:end_idx]
            
        except Exception as e:
            print(f"ERROR saat melakukan pencarian: {e}")
            results = []

    if query:
        return render_template('result.html', 
                             results=results, 
                             query=query,
                             page=page,                    # <- tambah
                             total_results=total_results,  # <- tambah
                             total_pages=total_pages,      # <- tambah
                             results_per_page=RESULTS_PER_PAGE)  # <- tambah
    else:
        return redirect(url_for('index'))
    
@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')



if __name__ == '__main__':
    try:
        load_assets()
        app.run(debug=True)
    except FileNotFoundError:
        print("\n SERVER GAGAL DIMULAI, model tidak ditemukan: {e}")
    except Exception as e:
        print("\n SERVER GAGAL DIMULAI, Terjadi error saat inisialisasi: {e}")

