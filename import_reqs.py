import os
import json
import requests
import pandas as pd
from flask_cors import CORS, cross_origin
import openai
from flask import Flask, request, jsonify, render_template
from datetime import datetime
import uuid
from firebase_admin import credentials, firestore, initialize_app, auth
import stripe

# Initialize Firestore DB & sets API Keys
cred = credentials.Certificate(
    'N/A.json')
openai.api_key = ("NA")
hubspot_key = 'N/A'
hubspot_url = 'N/A' + hubspot_key
stripe.api_key = "N/A"

default_app = initialize_app(cred)
db = firestore.client()
# SCRAPPER = db.collection('Scrapped')
REVIEW_POST = db.collection('Posts')
USERS = db.collection('Users')
PRODUCT = db.collection('Product')
COMPANY = db.collection('Companies')
GPT3QA = db.collection('GPT3-QA')
SUGGESTION = db.collection('Petitions')
LOGS = db.collection('Logs')
ADVANCED_ANALYTICS = db.collection('Advanced_analytics')
CONSUMER_PRODUCTS = db.collection('ConsumerProducts')
TUTOR_BOT = db.collection('Tutor_Bot')