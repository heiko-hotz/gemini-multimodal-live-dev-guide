# Deploy Project Pastra to Cloud Run

## Welcome

This tutorial will help you deploy Project Pastra to Google Cloud Run.

<walkthrough-project-setup></walkthrough-project-setup>

## Set Up API Keys

First, you'll need to set up your API keys:

1. Get your Gemini API key from [AI Studio](https://aistudio.google.com/app/apikey) (Required)
   ```bash
   read -p "Enter your Gemini API key: " GEMINI_API_KEY
   ```

2. Get your OpenWeather API key from [OpenWeather](https://openweathermap.org/api) (Optional)
   ```bash
   read -p "Enter your OpenWeather API key (press Enter to skip): " OPENWEATHER_API_KEY
   ```

3. Get your Finnhub API key from [Finnhub](https://finnhub.io/register) (Optional)
   ```bash
   read -p "Enter your Finnhub API key (press Enter to skip): " FINNHUB_API_KEY
   ```

<walkthrough-footnote>The Gemini API key is required for core functionality. OpenWeather and Finnhub API keys are optional and enable additional features.</walkthrough-footnote>

## Configure Project

Setting up your Google Cloud Project:

```bash
export PROJECT_ID={{project-id}}
gcloud config set project $PROJECT_ID
```

## Enable Required APIs

Enable the necessary Google Cloud APIs:

```bash
gcloud services enable cloudbuild.googleapis.com run.googleapis.com
```

## Build and Deploy

Now let's build and deploy the application:

```bash
# Build the container
gcloud builds submit --tag gcr.io/$PROJECT_ID/project-pastra-dev-api

# Set up environment variables
ENV_VARS="GEMINI_API_KEY=$GEMINI_API_KEY"
[ ! -z "$OPENWEATHER_API_KEY" ] && ENV_VARS="$ENV_VARS,OPENWEATHER_API_KEY=$OPENWEATHER_API_KEY"
[ ! -z "$FINNHUB_API_KEY" ] && ENV_VARS="$ENV_VARS,FINNHUB_API_KEY=$FINNHUB_API_KEY"

# Deploy to Cloud Run
gcloud run deploy project-pastra-dev-api \
  --image gcr.io/$PROJECT_ID/project-pastra-dev-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "$ENV_VARS"
```

## Success!

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

Your Project Pastra instance is now deployed! Click the service URL shown above to open your application.

Remember to:
1. Grant the necessary permissions when prompted (microphone, camera)
2. Start interacting with your AI assistant!

Note: Weather and stock market features will be disabled if you skipped the optional API keys.

## Cleanup (Optional)

To avoid incurring charges, you can delete the deployment when you're done:

```bash
gcloud run services delete project-pastra-dev-api --region us-central1
``` 