import streamlit as st
import requests
from gtts import gTTS
import base64
import os

st.set_page_config(page_title="Indian Product Health Scanner", page_icon="🥗")

# --- कस्टम स्टाइलिंग ---
st.markdown("""
    <style>
    .main-title { text-align: center; color: #1E88E5; font-size: 28px; font-weight: bold; }
    .sub-title { text-align: center; color: #555; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>🥗 AI फ़ूड & प्रोडक्ट हेल्थ स्कैनर</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>बारकोड स्कैन करें और तुरंत हिंदी/इंग्लिश में वॉइस फ़ीडबैक पाएं</div>", unsafe_allow_html=True)

# --- वॉइस जनरेशन फ़ंक्शन ---
def speak_text(text, lang='hi'):
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save("temp_speech.mp3")
    with open("temp_speech.mp3", "rb") as f:
        audio_bytes = f.read()
    b64 = base64.b64encode(audio_bytes).decode()
    audio_html = f"""
        <audio autoplay="true">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)
    os.remove("temp_speech.mp3")

# --- Open Food Facts API से डेटा लाना ---
def get_product_data(barcode):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == 1:
                return data["product"]
    except Exception as e:
        return None
    return None

# --- HTML/JS लाइव कैमरा बारकोड स्कैनर ---
scanner_html = """
<script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
<div id="reader" style="width: 100%; max-width: 500px; margin: auto;"></div>
<div id="result" style="text-align: center; font-weight: bold; margin-top: 10px;"></div>

<script>
function onScanSuccess(decodedText, decodedResult) {
    document.getElementById('result').innerText = "स्कैन कोड: " + decodedText;
    // Streamlit में कोड भेजना
    const urlParams = new URLSearchParams(window.location.search);
    urlParams.set('barcode', decodedText);
    window.location.search = urlParams.toString();
}

function onScanFailure(error) {
    // बैकग्राउंड स्कैन चलता रहेगा
}

let html5QrcodeScanner = new Html5QrcodeScanner(
    "reader", { fps: 10, qrbox: {width: 250, height: 150} }, /* verbose= */ false);
html5QrcodeScanner.render(onScanSuccess, onScanFailure);
</script>
"""

st.components.v1.html(scanner_html, height=360)

# --- URL से बारकोड पढ़ना ---
query_params = st.query_params
scanned_barcode = query_params.get("barcode", None)

# यदि यूजर मैनुअल कोड डालकर टेस्ट करना चाहे
manual_barcode = st.text_input("या फिर बारकोड नंबर यहाँ दर्ज करें (उदा: 8901058852312):")
if manual_barcode:
    scanned_barcode = manual_barcode

# --- जब बारकोड मिले तब प्रोसेस करें ---
if scanned_barcode:
    st.info(f"🔍 बारकोड स्कैन हुआ: *{scanned_barcode}*")
    
    with st.spinner("डेटाबेस से डिटेल निकाली जा रही है..."):
        product = get_product_data(scanned_barcode)
    
    if product:
        product_name = product.get("product_name", "अज्ञात प्रोडक्ट")
        brand = product.get("brands", "अज्ञात ब्रांड")
        ingredients = product.get("ingredients_text", "सामग्री की जानकारी उपलब्ध नहीं है।")
        nutriscore = product.get("nutriscore_grade", "N/A").upper()
        
        st.success(f"### 📦 {product_name} ({brand})")
        st.write(f"*न्यूट्रिशन ग्रेड (Health Grade):* {nutriscore}")
        st.write(f"*सामग्री (Ingredients):* {ingredients}")

        # वॉइस मैसेज तैयार करें
        voice_script = f"प्रोडक्ट का नाम है {product_name}। इसका हेल्थ ग्रेड {nutriscore} है।"
        if nutriscore in ['A', 'B']:
            voice_script += " यह सेहत के लिए अच्छा विकल्प है।"
        elif nutriscore in ['D', 'E']:
            voice_script += " इसमें चीनी या फैट की मात्रा अधिक हो सकती है, ध्यान से इस्तेमाल करें।"

        # हिंदी में बोलकर बताएगा
        speak_text(voice_script, lang='hi')

    else:
        st.error("यह प्रोडक्ट डेटाबेस में नहीं मिला। कृपया दूसरा बारकोड स्कैन करें।")
        speak_text("यह प्रोडक्ट डेटाबेस में नहीं मिला।", lang='hi')
