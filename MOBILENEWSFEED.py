import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime
from pytz import timezone
from groq import Groq
import requests
import re

# Configuring the page layout
st.set_page_config(layout="wide")

# Custom CSS for mobile optimization
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    
    body {
        font-family: 'Roboto', sans-serif;
        background-color: #f0f2f6;
        color: #1e1e1e;
    }
    .stApp {
        max-width: 100%;
        padding: 1rem;
    }
    .banner {
        background-image: url('https://github.com/M00N69/BUSCAR/blob/main/logo%2002%20copie.jpg?raw=true');
        background-size: contain;
        background-repeat: no-repeat;
        background-position: center;
        height: 100px;
        margin-bottom: 1rem;
    }
    .stButton > button {
        width: 100%;
        border-radius: 20px;
        background-color: #2398B2;
        color: white;
    }
    .article-card {
        background-color: white;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .article-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .article-meta {
        font-size: 0.8rem;
        color: #666;
        margin-bottom: 0.5rem;
    }
    .article-summary {
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    .article-buttons {
        display: flex;
        justify-content: space-between;
    }
    </style>
    <div class="banner"></div>
    """,
    unsafe_allow_html=True
)

# Initialize session state variables
if 'showing_readme' not in st.session_state:
    st.session_state['showing_readme'] = True

if 'review_articles' not in st.session_state:
    st.session_state['review_articles'] = []

# URL of the README.md on GitHub
readme_url = "https://raw.githubusercontent.com/M00N69/FOODNEWSFEED/main/README.md"

def load_readme(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        return "Sorry, we couldn't load the README file from GitHub."

# Toggle button to switch between README and main content
if st.button("Toggle About this APP"):
    st.session_state['showing_readme'] = not st.session_state['showing_readme']

# Define your list of RSS feeds
rss_feeds = {
    "Food safety Magazine": "https://www.food-safety.com/rss/topic/296",
    "Food SafetyTech": "https://foodsafetytech.com/feed/",
    "Food Navigator": "https://www.foodnavigator.com/Info/Latest-News",
    "Food GOV UK": "https://www.food.gov.uk/rss-feed/news",
    "US CDC": "https://www2c.cdc.gov/podcasts/createrss.asp?c=146",
    "US FDA Press Release": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/press-releases/rss.xml",
    "Food in Canada": "https://fetchrss.com/rss/66c715e5337ecb14670d0f2266c715d0a44ee6bd2b011812.xml",
    "CODEX Hygiene meeting": "https://www.fao.org/fao-who-codexalimentarius/meetings/detail/rss/fr/?meeting=CCFH&session=54",
    "RASFF EU Feed": "https://webgate.ec.europa.eu/rasff-window/backend/public/consumer/rss/all/",
    "EFSA": "https://www.efsa.europa.eu/en/all/rss",
    "EU Food Safety": "https://food.ec.europa.eu/node/2/rss_en",
    "Food Quality & Safety": "https://www.foodqualityandsafety.com/category/eupdate/feed/",
    "Food Safety News": "https://feeds.lexblog.com/foodsafetynews/mRcs",
    "Food Manufacture": "https://www.foodmanufacture.co.uk/Info/FoodManufacture-RSS",
    "Food Packaging Forum": "https://www.foodpackagingforum.org/news/feed/",
    "French Recalls RAPPELCONSO": "https://rappel.conso.gouv.fr/rss?categorie=01",
    "Legifrance Alimentaire": "https://legifrss.org/latest?nature=decret&q=alimentaire",
    "INRS secu": "https://www.inrs.fr/rss/?feed=actualites",
    "ANSES": "https://www.anses.fr/fr/flux-actualites.rss",
    "Food Ingredient first": "https://resource.innovadatabase.com/rss/fifnews.xml"
}

# Function to parse all RSS feeds
def parse_feeds(selected_feeds):
    data = []
    for feed_name, feed_url in rss_feeds.items():
        if feed_name in selected_feeds:
            parsed_feed = feedparser.parse(feed_url)
            for entry in parsed_feed.entries[:25]:  # Get the latest 25 articles
                published_date = "Unknown"
                if hasattr(entry, 'published_parsed'):
                    published_date = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d")
                else:
                    description = entry.description if hasattr(entry, 'description') else ""
                    date_match = re.search(r'(\d{2}/\d{2}/\d{4})', description)
                    if date_match:
                        published_date = datetime.strptime(date_match.group(1), "%d/%m/%Y").strftime("%Y-%m-%d")
                
                data.append({
                    "feed": feed_name,
                    "title": entry.title,
                    "link": entry.link,
                    "summary": entry.summary,
                    "published": published_date,
                    "image": entry.get("media_content", [None])[0].get("url", None) if "media_content" in entry else None
                })
    
    df = pd.DataFrame(data).sort_values(by="published", ascending=False)  # Sort by date, latest first
    return df

# Function to summarize the content of an article via Groq
def summarize_article_with_groq(url):
    client = get_groq_client()
    messages = [
        {"role": "system", "content": "Please summarize the following article:"},
        {"role": "user", "content": url}
    ]

    model_id = "llama-3.1-8b-instant"  # Ensure this model can handle URLs

    chat_completion = client.chat.completions.create(
        messages=messages,
        model=model_id
    )

    return chat_completion.choices[0].message.content

def get_groq_client():
    return Groq(api_key=st.secrets["GROQ_API_KEY"])

# Main section to display either the README or the articles
if st.session_state['showing_readme']:
    readme_content = load_readme(readme_url)
    st.markdown(readme_content)
else:
    st.header("Food News Feed")

    # Sidebar for mobile
    with st.expander("Settings"):
        st.subheader("Select News Sources")
        feeds = list(rss_feeds.keys())
        default_feeds = ["Food Quality & Safety"]
        selected_feeds = st.multiselect("Select Feeds:", feeds, default=default_feeds)

        st.subheader("Date Range")
        col1, col2 = st.columns(2)
        with col1:
            min_date = st.date_input("Start date", value=pd.to_datetime("2023-01-01"))
        with col2:
            max_date = st.date_input("End date", value=datetime.now().date())

        paris_timezone = timezone('Europe/Paris')
        st.write(f"Last Update: {datetime.now(paris_timezone).strftime('%Y-%m-%d %H:%M:%S')}")

    # Parse feeds based on selected sources
    feeds_df = parse_feeds(selected_feeds)

    # Filter articles by date
    feeds_df['published'] = pd.to_datetime(feeds_df['published'], errors='coerce')
    filtered_df = feeds_df[(feeds_df['published'] >= pd.to_datetime(min_date)) & (feeds_df['published'] <= pd.to_datetime(max_date))]

    st.subheader("Latest Articles")

    if not filtered_df.empty:
        for i, row in filtered_df.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="article-card">
                    <div class="article-title">{row['title']}</div>
                    <div class="article-meta">
                        {row['published'].strftime('%Y-%m-%d') if pd.notnull(row['published']) else 'Unknown'} | {row['feed']}
                    </div>
                    <div class="article-summary">{row['summary'][:150]}...</div>
                    <div class="article-buttons">
                        <a href="{row['link']}" target="_blank">Read More</a>
                        <button onclick="add_to_review({i})">Add to Review</button>
                        <button onclick="summarize_article({i})">Summarize</button>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"Add to Review", key=f"add_{i}"):
                    if "review_articles" not in st.session_state:
                        st.session_state["review_articles"] = []
                    st.session_state["review_articles"].append(row.to_dict())
                    st.success(f"Article added to review: {row['title']}")
                
                if st.button(f"Summarize", key=f"summarize_{i}"):
                    summary = summarize_article_with_groq(row['link'])
                    st.info(f"Summary for {row['title']}:\n\n{summary}")

    else:
        st.write("No articles available for the selected sources and date range.")

    # Display selected articles for review
    if st.session_state["review_articles"]:
        st.subheader("Your Review")
        for i, article in enumerate(st.session_state["review_articles"]):
            st.markdown(f"""
            <div class="article-card">
                <div class="article-title">{article['title']}</div>
                <div class="article-meta">
                    {article['published']} | {article['feed']}
                </div>
                <div class="article-summary">{article['summary'][:150]}...</div>
                <a href="{article['link']}" target="_blank">Read More</a>
            </div>
            """, unsafe_allow_html=True)

        st.text_area("Add your review here:", height=150)

        if st.button("Generate Report"):
            st.success("Report generated successfully!")

    st.write("App finished setup.")
