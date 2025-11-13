import pandas as pd
import os
import requests
from glob import glob

# Configuration
api_endpoint = "https://your-api.com/critique_image"  # Replace with real endpoint
input_folder = "./data"
output_folder = "./Output"
os.makedirs(output_folder, exist_ok=True)

# Send image + prompt to API
def query_external_api(image_url, critique_prompt, output_path):
    try:
        # Download input image locally
        local_image_path = "temp_image.jpg"
        img_data = requests.get(image_url).content
        with open(local_image_path, "wb") as f:
            f.write(img_data)
        
        # Send POST request
        files = {"image": open(local_image_path, "rb")}
        data = {"critique": critique_prompt}
        response = requests.post(api_endpoint, files=files, data=data)
        
        # Clean up local image
        os.remove(local_image_path)
        
        # Check response
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            
            if "application/json" in content_type:
                # API returned JSON, contain image URL
                resp_json = response.json()
                returned_image_url = resp_json.get("image_url")  # adjust key
                
                if not returned_image_url:
                    return "Error: No image URL in JSON response"
                
                # Download image from returned URL
                img_out_data = requests.get(returned_image_url).content
                with open(output_path, "wb") as f:
                    f.write(img_out_data)
            else:
                # API returned image bytes directly
                with open(output_path, "wb") as f:
                    f.write(response.content)
            
            return output_path
        else:
            return f"Error {response.status_code}: {response.text}"
    
    except Exception as e:
        return f"Exception: {e}"


# --- Process a single Excel file ---
def process_file(file_path):
    df = pd.read_excel(file_path)
    excel_name = os.path.splitext(os.path.basename(file_path))[0]
    
    # Create a subfolder in output_folder
    folder_path = os.path.join(output_folder, excel_name)
    os.makedirs(folder_path, exist_ok=True)

    for idx, row in df.iterrows():
        image_url = row.get("Image_URL")
        critique_prompt = row.get("Critique", "")
        post_id = str(row.get("Post_ID"))
        
        if not image_url or pd.isna(image_url):
            print(f"Skipping row {idx}: No Image_URL")
            continue
        
        output_image_path = os.path.join(folder_path, f"{post_id}_output.png")
        result = query_external_api(image_url, critique_prompt, output_image_path)
        print(f"Saved: {result}")

# --- Main: process all .xlsx files ---
excel_files = glob(os.path.join(input_folder, "*.xlsx"))
for file_path in excel_files:
    process_file(file_path)
