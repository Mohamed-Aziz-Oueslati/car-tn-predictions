import requests, time

# UPDATE THIS!
BASE_URL = "https://stunt-wanting-agility.ngrok-free.dev"

# 1. Upload
print("Uploading...")
with open("car.jpg", "rb") as f:
    resp = requests.post(f"{BASE_URL}/generate", files={'file': f})
    job_id = resp.json()['job_id']
    print(f"Started job: {job_id}")

# 2. Poll
while True:
    try:
        status_resp = requests.get(f"{BASE_URL}/status/{job_id}", timeout=10)
        status = status_resp.json().get('status', 'unknown')
        print(f"Status: {status}")
        
        if status == 'completed':
            dl = requests.get(f"{BASE_URL}/download/{job_id}")
            with open("model.glb", "wb") as f: f.write(dl.content)
            print("Done! Downloaded as model.glb")
            break
        elif status == 'failed':
            print("Generation failed.")
            break
    except Exception as e:
        print("Server busy/unresponsive, retrying in 15s...")
        
    time.sleep(15)