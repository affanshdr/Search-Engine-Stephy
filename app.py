from flask import Flask, request, render_template
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

app = Flask(__name__)

print("tes")