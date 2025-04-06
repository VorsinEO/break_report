import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import csv
import uuid
from datetime import datetime
import requests
import base64
from io import BytesIO
from PIL import Image

# Load environment variables - first check Streamlit secrets, fallback to .env
if "OPENAI_API_KEY" not in st.secrets:
    load_dotenv()
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    os.environ["N8N_WEBHOOK_URL"] = os.getenv("N8N_WEBHOOK_URL")
    os.environ["IMGBB_API_KEY"] = os.getenv("IMGBB_API_KEY")

# Configure APIs with fallback mechanism
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", os.environ["OPENAI_API_KEY"]))
webhook_url = st.secrets.get("N8N_WEBHOOK_URL", os.environ["N8N_WEBHOOK_URL"])
imgbb_api_key = st.secrets.get("IMGBB_API_KEY", os.environ["IMGBB_API_KEY"])

# Page config for mobile-first design
st.set_page_config(
    page_title="Create Breakdown Report",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile-first design
st.markdown("""
    <style>
    .stApp {
        max-width: 100%;
        padding: 1rem;
    }
    .stChatMessage {
        max-width: 100%;
    }
    .uploadedImage {
        max-width: 300px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add the system message as the first message
    st.session_state.messages.append({
        "role": "system",
        "content": """You are an assistant for mechanics working in the mining industry.
 Your job is to collect the following fields step-by-step:
- equipment type (e.g., Dump Truck, Excavator)
- equipment ID (e.g., 743)
- problem description
- incident date (can be "today" or a date)
- photo URL (will be provided by the system)

Ask only one question at a time. When all info is collected, summarize it in a clear list using this exact format:
Equipment Type: [type]
Equipment ID: [id]
Problem: [description]
Date: [date]
Photo URL: [url or "(none)"]

Then ask: "Would you like me to submit this report?"
"""
    })

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

if "current_image_url" not in st.session_state:
    st.session_state.current_image_url = None

if "show_submit_button" not in st.session_state:
    st.session_state.show_submit_button = False

if "last_response" not in st.session_state:
    st.session_state.last_response = None

def upload_to_imgbb(image_file):
    """Upload image to ImgBB and return the URL"""
    try:
        # Read and encode the image
        image = Image.open(image_file)
        
        # Convert to RGB if RGBA
        if image.mode == 'RGBA':
            image = image.convert('RGB')
            
        # Save to buffer
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        image_binary = buffer.getvalue()
        
        # Encode to base64
        base64_image = base64.b64encode(image_binary).decode('utf-8')
        
        # Upload to ImgBB
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": imgbb_api_key,
            "image": base64_image,
        }
        
        response = requests.post(url, data=payload)
        response.raise_for_status()
        
        # Get the image URL
        result = response.json()
        if result["success"]:
            return result["data"]["url"]
        else:
            st.error("Failed to upload image to ImgBB")
            return None
            
    except Exception as e:
        st.error(f"Error uploading image: {str(e)}")
        return None

# Title
st.title("Create Breakdown Report")

# User email input at the top
if not st.session_state.user_email:
    st.session_state.user_email = st.text_input("Enter your email:", placeholder="your.name@mineco.com")

# Image upload
uploaded_file = st.file_uploader("Upload an image of the problem (optional)", type=['png', 'jpg', 'jpeg'])
if uploaded_file:
    # Display the uploaded image
    st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
    
    # Upload to ImgBB
    with st.spinner("Uploading image..."):
        image_url = upload_to_imgbb(uploaded_file)
        if image_url:
            st.session_state.current_image_url = image_url
            st.success("Image uploaded successfully!")
            
            # Add system message about the image
            st.session_state.messages.append({
                "role": "system",
                "content": f"A photo has been uploaded. Please use this URL in your summary: {image_url}"
            })

# Display chat messages
for message in st.session_state.messages:
    if message["role"] != "system":  # Don't display system messages
        with st.chat_message(message["role"]):
            st.write(message["content"])

def parse_report_fields(summary):
    """Extract fields from the assistant's summary"""
    lines = summary.split('\n')
    fields = {}
    
    for line in lines:
        if ': ' in line:
            key, value = line.split(': ', 1)
            key = key.strip().lower().replace(' ', '_')
            fields[key] = value.strip()
    
    # If we have an uploaded image URL, use it regardless of what's in the summary
    if st.session_state.current_image_url:
        fields['photo_url'] = st.session_state.current_image_url
    
    return {
        'equipment_type': fields.get('equipment_type', ''),
        'equipment_id': fields.get('equipment_id', ''),
        'problem_description': fields.get('problem', ''),
        'incident_date': fields.get('date', ''),
        'photo_url': fields.get('photo_url', ''),
    }

def save_report(summary):
    """Save report to CSV and send to webhook"""
    report_id = str(uuid.uuid4())[:8]  # Using first 8 characters for brevity
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Parse fields from the summary
    fields = parse_report_fields(summary)
    
    # Create chat summary
    chat_summary = f"Equipment: {fields['equipment_type']} ({fields['equipment_id']})\nProblem: {fields['problem_description']}\nDate: {fields['incident_date']}\nPhoto: {fields['photo_url'] or '(none)'}"
    
    # Prepare row data
    row_data = {
        'report_id': report_id,
        'timestamp': timestamp,
        'equipment_type': fields['equipment_type'],
        'equipment_id': fields['equipment_id'],
        'problem_description': fields['problem_description'],
        'incident_date': fields['incident_date'],
        'photo_url': fields['photo_url'],
        'submitted_by': st.session_state.user_email,
        'chat_summary': chat_summary
    }
    
    # Save to CSV
    csv_file = "reports.csv"
    file_exists = os.path.isfile(csv_file)
    
    with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['report_id', 'timestamp', 'equipment_type', 'equipment_id', 
                           'problem_description', 'incident_date', 'photo_url', 
                           'submitted_by', 'chat_summary'])
        writer.writerow([row_data[field] for field in ['report_id', 'timestamp', 'equipment_type', 
                        'equipment_id', 'problem_description', 'incident_date', 'photo_url',
                        'submitted_by', 'chat_summary']])
    
    # Send to webhook
    if webhook_url:
        try:
            requests.post(webhook_url, json=row_data)
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to send to webhook: {str(e)}")
    
    st.toast("Report saved successfully!")
    return row_data

# Chat input
if st.session_state.user_email:  # Only show chat if email is provided
    if prompt := st.chat_input("Describe the problem..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get assistant response using new OpenAI API format
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=st.session_state.messages
        )
        
        assistant_response = response.choices[0].message.content
        st.session_state.last_response = assistant_response
        
        # Add assistant response to chat
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
        
        # Display assistant response
        with st.chat_message("assistant"):
            st.write(assistant_response)
        
        # Check if the message suggests submission
        if any(word in assistant_response.lower() for word in ["submit", "ready to send"]):
            st.session_state.show_submit_button = True

    # Show submit button outside of chat message context if needed
    if st.session_state.show_submit_button and st.session_state.last_response:
        if st.button("Confirm Submission", key="submit_button"):
            report_data = save_report(st.session_state.last_response)
            st.success(f"Report {report_data['report_id']} submitted successfully!")
            # Reset submission state
            st.session_state.show_submit_button = False
            st.session_state.last_response = None
else:
    st.info("Please enter your email address to start the chat.") 