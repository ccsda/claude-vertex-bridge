# Getting a Service Account Key from Google Cloud Console

Follow these steps to create a service account and download its key:

1. Go to the Google Cloud Console: https://console.cloud.google.com

2. Select your project "orojectid-fitfloprod"

3. Navigate to "IAM & Admin" > "Service Accounts" in the left sidebar

4. Click "CREATE SERVICE ACCOUNT" at the top

5. Fill in the service account details:
   - Name: `vertex-ai-bridge` (or any name you prefer)
   - Description: "Service account for OpenAI to Vertex AI bridge service"
   - Click "CREATE AND CONTINUE"

6. Grant the service account these roles:
   - "Vertex AI User" (roles/aiplatform.user)
   - "Service Account User" (roles/iam.serviceAccountUser)
   Click "CONTINUE"

7. Click "DONE"

8. In the service accounts list, find your new service account
   Click the three dots (⋮) menu > "Manage keys"

9. Click "ADD KEY" > "Create new key"
   Select "JSON" format
   Click "CREATE"

The key file will automatically download to your computer. Move this file to a secure location and note its path. We'll use this path in the .env file.

IMPORTANT: Keep this key secure and never commit it to version control!
