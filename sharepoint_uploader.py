import os
from pathlib import Path
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File

# 🔒 Production Security Rule: Fetch credentials securely from environment variables
SITE_URL = os.getenv("VFD_SHAREPOINT_SITE", "https://sharepoint.com")
CLIENT_ID = os.getenv("VFD_AZURE_CLIENT_ID", "your-azure-client-id-goes-here")
CLIENT_SECRET = os.getenv("VFD_AZURE_CLIENT_SECRET", "your-azure-client-secret-goes-here")

TARGET_FOLDER_URL = "/sites/TestSite/Shared Documents/General/VA"


def upload_to_sharepoint(local_file_path: str, target_folder: str) -> bool:
    """Authenticates securely via App-Only credentials and streams local files

    directly into corporate SharePoint document libraries.
    """
    path_obj = Path(local_file_path)
    if not path_obj.exists():
        print(f"[ERROR] Local payload target does not exist: {local_file_path}")
        return False

    print(f"[INFO] Initiating secure authentication connection to: {SITE_URL}")
    ctx_auth = AuthenticationContext(SITE_URL)

    # Use App-Only credentials framework for automated background daemon pipelines
    if ctx_auth.acquire_token_for_app(CLIENT_ID, CLIENT_SECRET):
        try:
            ctx = ClientContext(SITE_URL, ctx_auth)
            
            print(f"[INFO] Streaming {path_obj.name} to target directory...")
            with open(path_obj, "rb") as file_content:
                target_file_url = f"{target_folder}/{path_obj.name}"
                File.save_binary(ctx, target_file_url, file_content)
                
            print(f"[SUCCESS] Enterprise document synced successfully to: {target_file_url}")
            return True

        except Exception as e:
            print(f"[ERROR] Critical infrastructure failure during cloud sync: {str(e)}")
            return False
    else:
        print(f"[AUTH ERROR] Failed securely binding token context: {ctx_auth.get_last_error()}")
        return False


if __name__ == "__main__":
    print("[INFO] Launching Enterprise Cloud Ingestion Service...")
    sample_payload = "processed_veteran_document.pdf"
    
    if not os.path.exists(sample_payload):
        with open(sample_payload, "w") as f:
            f.write("Mock processed veteran referral metadata context for cloud upload test.")

    upload_to_sharepoint(sample_payload, TARGET_FOLDER_URL)
    
    if os.path.exists(sample_payload):
        os.remove(sample_payload)
