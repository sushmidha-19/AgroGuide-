import streamlit as st
import mysql.connector
import requests
from transformers import pipeline


# ----------------------------------------------------------
# 1️⃣ DATABASE CONNECTION
# ----------------------------------------------------------
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",          # default for WAMP
        password="Madhuu@16",          # enter your MySQL password if any
        database="agroguide"
    )

def add_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        st.success("✅ Account created! Please login.")
    except:
        st.error("⚠️ Username already exists.")
    conn.close()

def login_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
    result = cursor.fetchone()
    conn.close()
    return result

def log_query(username, question, answer):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO queries (username, question, answer) VALUES (%s, %s, %s)", (username, question, answer))
    conn.commit()
    conn.close()

def get_user_queries(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT question, answer FROM queries WHERE username=%s ORDER BY id DESC", (username,))
    data = cursor.fetchall()
    conn.close()
    return data

# ----------------------------------------------------------
# 2️⃣ LOAD AI MODEL
# ----------------------------------------------------------
@st.cache_resource
def load_model():
    return pipeline("text2text-generation", model="google/flan-t5-large")

# ----------------------------------------------------------
# 3️⃣ PAGE FUNCTIONS
# ----------------------------------------------------------
def page_home():
    st.title("🌿 AgroGuide: Your AI Farming Assistant")
    st.write("Ask about crops, soil, weather, fertilizers, or pests — and get instant AI guidance!")

    generator = load_model()

    question = st.text_area("💬 Ask your question:", placeholder="Example: How can I increase tomato yield in dry conditions?")
    if st.button("Ask AI"):
        if question.strip():
            with st.spinner("Thinking... please wait..."):
                response = generator(question, max_length=200, do_sample=True)[0]['generated_text']
            st.success("🌾 AgroGuide Suggests:")
            st.write(response)
            log_query(st.session_state.username, question, response)
        else:
            st.warning("Please enter a question first.")
    st.caption("Powered by FLAN-T5 — no API key required.")

def page_crop_recommend():
    st.title("🌾 Crop Recommendation System")
    soil = st.selectbox("Soil Type", ["Loamy", "Sandy", "Clay", "Black", "Red"])
    rain = st.slider("Average Rainfall (mm)", 100, 1000, 300)
    temp = st.slider("Temperature (°C)", 10, 45, 25)

    if st.button("Recommend Crop"):
        if soil == "Loamy" and 200 < rain < 800:
            st.success("✅ Recommended: Rice, Wheat, or Maize.")
        elif soil == "Sandy" and rain < 300:
            st.success("✅ Recommended: Millet, Groundnut, or Cotton.")
        elif soil == "Clay" and rain > 600:
            st.success("✅ Recommended: Rice or Sugarcane.")
        else:
            st.info("Try mixed cropping or consult your local agriculture officer.")

def page_fertilizer():
    st.title("🧪 Fertilizer Suggestion")
    crop = st.selectbox("Crop", ["Wheat", "Rice", "Maize", "Tomato", "Potato"])
    n = st.number_input("Nitrogen (N)", 0, 150, 50)
    p = st.number_input("Phosphorus (P)", 0, 150, 40)
    k = st.number_input("Potassium (K)", 0, 150, 30)

    if st.button("Suggest Fertilizer"):
        if n < 50:
            st.success("💡 Add Urea — Nitrogen-rich fertilizer.")
        elif p < 40:
            st.success("💡 Add DAP — Phosphorus fertilizer.")
        elif k < 30:
            st.success("💡 Add MOP — Potassium fertilizer.")
        else:
            st.success("✅ Soil nutrient levels are balanced!")

# ----------------------------------------------------------
# 🌤️ WEATHER PAGE — with One Call API 3.0
# ----------------------------------------------------------
def page_weather():
    st.subheader("🌦 Weather Forecast")
    city = st.text_input("Enter your city:")
    api_key = "46c0bc4fd8b7d9363b51b1b3dac4060d"  # Replace with your OpenWeather API key

    if st.button("Get Weather"):
        if city:
            try:
                geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={api_key}"
                geo_data = requests.get(geo_url).json()

                # ✅ Check if data is valid
                if isinstance(geo_data, list) and len(geo_data) > 0:
                    lat = geo_data[0]['lat']
                    lon = geo_data[0]['lon']

                    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
                    weather_data = requests.get(weather_url).json()

                    st.success(f"🌡️ Temperature in {city}: {weather_data['main']['temp']}°C")
                    st.write(f"☁️ Condition: {weather_data['weather'][0]['description'].title()}")
                    st.write(f"💧 Humidity: {weather_data['main']['humidity']}%")
                    st.write(f"💨 Wind Speed: {weather_data['wind']['speed']} m/s")
                else:
                    st.warning("City not found! Please check the spelling.")
            except Exception as e:
                st.error(f"Error fetching data: {e}")
        else:
            st.warning("Please enter a city name.")
def page_knowledge():
    st.title("📘 Farming Knowledge Center")
    st.write("""
    ### 🌾 Crop Rotation
    Helps maintain soil fertility and reduce pest buildup.

    ### 💧 Drip Irrigation
    Conserves water while ensuring efficient plant growth.

    ### 🪱 Organic Compost
    Improves soil structure, moisture retention, and nutrient content.

    ### 🐝 Pollination Support
    Encourage bee-friendly farming to boost yields.

    ### 🌿 Sustainable Practices
    Avoid overuse of fertilizers and pesticides for long-term soil health.
    """)

def page_history():
    st.title("📊 Your Query History")
    data = get_user_queries(st.session_state.username)
    if data:
        for q, a in data:
            with st.expander(f"❓ {q}"):
                st.write(f"**💬 Answer:** {a}")
    else:
        st.info("No queries yet.")

# ----------------------------------------------------------
# 4️⃣ LOGIN & SIGN-UP
# ----------------------------------------------------------
def login_page():
    st.title("🌾 AgroGuide Login Portal")
    option = st.radio("Select Option", ["Login", "Sign Up"])

    if option == "Login":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid username or password.")

    elif option == "Sign Up":
        username = st.text_input("Create Username")
        password = st.text_input("Create Password", type="password")
        if st.button("Create Account"):
            add_user(username, password)

# ----------------------------------------------------------
# 5️⃣ MAIN APP NAVIGATION
# ----------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if st.session_state.logged_in:
    st.sidebar.title("🧭 Navigation")
    st.sidebar.write(f"👤 Logged in as: {st.session_state.username}")
    page = st.sidebar.selectbox(
        "Select Page",
        ["Home", "Crop Recommendation", "Fertilizer Suggestion", "Weather Info", "Knowledge Center", "Query History", "Logout"]
    )

    if page == "Home":
        page_home()
    elif page == "Crop Recommendation":
        page_crop_recommend()
    elif page == "Fertilizer Suggestion":
        page_fertilizer()
    elif page == "Weather Info":
        page_weather()
    elif page == "Knowledge Center":
        page_knowledge()
    elif page == "Query History":
        page_history()
    elif page == "Logout":
        st.session_state.logged_in = False
        st.success("Logged out successfully!")
        st.rerun()

else:
    login_page()
