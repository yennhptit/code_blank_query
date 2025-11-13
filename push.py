from huggingface_hub import HfApi, HfFolder
import os
import time
from tqdm import tqdm
import shutil

HF_TOKEN = ""  # Hugging Face token
REPO_ID = "yuu1234/CrittiqueImageReviewer"
BRANCH = "main"
BATCH_SIZE = 500
DELETE_LOCAL = False

LOCAL_ROOT = "Output"

HfFolder.save_token(HF_TOKEN)
api = HfApi()

def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def safe_remove(path):
    try:
        os.remove(path)
    except:
        pass

image_extensions = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp")

files = []
for root, dirs, filenames in os.walk(LOCAL_ROOT):
    for f in filenames:
        if f.lower().endswith(image_extensions):
            files.append(os.path.join(root, f))

print(f"Found {len(files)} image files.")

for batch_id, batch_files in enumerate(chunk_list(files, BATCH_SIZE), start=1):
    temp_dir = f"/tmp/_hf_batch_{batch_id}"
    os.makedirs(temp_dir, exist_ok=True)

    for f in batch_files:
        shutil.copy(f, os.path.join(temp_dir, os.path.basename(f)))

    try:
        api.upload_folder(
            folder_path=temp_dir,
            repo_id=REPO_ID,
            repo_type="dataset",
            revision=BRANCH,
            token=HF_TOKEN,
            commit_message=f"Upload batch {batch_id} ({len(batch_files)} files)",
        )

        if DELETE_LOCAL:
            for f in batch_files:
                safe_remove(f)

    except Exception as e:
        print(f"Error uploading batch {batch_id}: {e}")
        time.sleep(5)

    # Remove temp folder
    shutil.rmtree(temp_dir, ignore_errors=True)

print("Done.")
