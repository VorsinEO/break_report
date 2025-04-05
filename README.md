# Equipment Breakdown Report App

A Streamlit-based mobile app for submitting equipment breakdown reports in the mining industry.

## Setup

### Local Development

1. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your credentials using either method A or B:

#### Method A: Using .env file
1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit the `.env` file with your credentials:
```
OPENAI_API_KEY=your_openai_api_key_here  # From https://platform.openai.com/api-keys
N8N_WEBHOOK_URL=your_webhook_url_here    # Your N8N webhook endpoint
IMGBB_API_KEY=your_imgbb_api_key_here    # From https://api.imgbb.com/
```

#### Method B: Using Streamlit secrets locally
1. Create the `.streamlit` directory:
```bash
mkdir .streamlit
```

2. Create and edit `.streamlit/secrets.toml`:
```toml
# OpenAI API configuration
OPENAI_API_KEY = "your-api-key-here"

# N8N Webhook configuration
N8N_WEBHOOK_URL = "your-webhook-url-here"

# ImgBB API configuration
IMGBB_API_KEY = "your-imgbb-api-key-here"
```

Note: Both `.env` and `.streamlit/secrets.toml` are git-ignored for security.

### Deployment

When deploying to Streamlit Cloud:

1. Go to your app's settings in the Streamlit Cloud dashboard
2. Under "Secrets", add the following configuration:
```toml
[secrets]
OPENAI_API_KEY = "your_openai_api_key_here"
N8N_WEBHOOK_URL = "your_webhook_url_here"
IMGBB_API_KEY = "your_imgbb_api_key_here"
```

The app will automatically use Streamlit secrets when deployed and fall back to local .env file when running locally.

## Running the App

Run the Streamlit app with:
```bash
streamlit run app.py
```

The app will be accessible at `http://localhost:8501` by default.

## Example Test Cases

Here are some example scenarios you can use to test the app:

### 1. Basic Equipment Failure
Start with:
```
The dump truck 743 won't start this morning. When I turn the key, nothing happens.
```
Expected fields:
- Equipment Type: Dump Truck
- Equipment ID: 743
- Problem: Engine won't start, no response when turning key
- Date: today

### 2. Hydraulic System Issue
Start with:
```
Excavator 205 has a hydraulic leak from the boom cylinder. Started noticing it yesterday afternoon.
```
Expected fields:
- Equipment Type: Excavator
- Equipment ID: 205
- Problem: Hydraulic leak in boom cylinder
- Date: yesterday

### 3. Tire Problem
Start with:
```
Front right tire on haul truck HT-892 has significant wear and needs replacement. Noticed during morning inspection on April 5th.
```
Expected fields:
- Equipment Type: Haul Truck
- Equipment ID: HT-892
- Problem: Front right tire significant wear, needs replacement
- Date: April 5th

### 4. Electronic System Issue
Start with:
```
The display panel on loader 156 is showing error code E-45. Started flickering last week on Monday.
```
Expected fields:
- Equipment Type: Loader
- Equipment ID: 156
- Problem: Display panel showing error code E-45, flickering
- Date: last Monday

### 5. Mechanical Problem with Photo
Start with:
```
Found a crack in the bucket of excavator EX-445. Uploading a photo of the damage.
```
Expected fields:
- Equipment Type: Excavator
- Equipment ID: EX-445
- Problem: Crack in bucket
- Date: today
- Photo URL: [Will be added after upload]

## Features

- Mobile-first design
- Step-by-step equipment breakdown reporting
- Integration with GPT-4 for intelligent form filling
- Local CSV storage of reports
- Webhook integration for external processing
- Real-time chat interface
- Support for both local development and cloud deployment
- Image upload support via ImgBB

## Data Storage

Reports are stored in a local `reports.csv` file with the following fields:
- report_id: UUID for each report
- timestamp: UTC timestamp in ISO format
- equipment_type: Type of equipment (e.g., Dump Truck, Excavator)
- equipment_id: Equipment identifier
- problem_description: Description of the issue
- incident_date: When the problem occurred
- photo_url: URL of uploaded image (if any)
- submitted_by: Email of the person submitting the report
- chat_summary: Formatted summary of the report

## Security Notes

- Never commit your `.env` file to version control
- The `.gitignore` file is configured to exclude sensitive files
- Use Streamlit secrets for production deployment
- Regularly rotate your API keys for security
- Ensure uploaded images don't contain sensitive information 