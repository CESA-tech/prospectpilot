import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'credentials.json')
TOKEN_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'token.pickle')


def get_gmail_service():
    """Gmail API bağlantısı kur. İlk çalıştırmada tarayıcı açar, izin ister."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)

    return build("gmail", "v1", credentials=creds)


def check_reply(to_email: str, subject: str) -> bool:
    """
    Belirtilen alıcıdan, belirtilen subject'e cevap gelmiş mi kontrol eder.
    Inbox'ta o kişiden gelen email varsa True döner.
    """
    service = get_gmail_service()

    # Alıcının emailinden gelen mesajları ara
    query = f"from:{to_email}"
    results = service.users().messages().list(userId="me", q=query, maxResults=10).execute()
    messages = results.get("messages", [])

    if not messages:
        return False

    # Subject eşleşmesi kontrol et (Re: veya orijinal konu)
    clean_subject = subject.lower().replace("re: ", "").strip()

    for msg in messages:
        detail = service.users().messages().get(userId="me", id=msg["id"], format="metadata",
                                                metadataHeaders=["Subject"]).execute()
        headers = detail.get("payload", {}).get("headers", [])
        for h in headers:
            if h["name"] == "Subject":
                msg_subject = h["value"].lower().replace("re: ", "").strip()
                if clean_subject in msg_subject or msg_subject in clean_subject:
                    return True

    return False


if __name__ == "__main__":
    print("Gmail bağlantısı test ediliyor...")
    service = get_gmail_service()
    print("Bağlantı başarılı!")
