
import os
import requests
import subprocess
from huggingface_hub import HfApi

print("Starting generation...")

TITLE = """legend"""
SCRIPT_TEXT = """in the land of myth."""
STYLE = """cinematic"""

NVIDIA_KEY = "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"
KIE_AI_KEY = "1cf7c5c2e976e97a12647ed3358b5ec5"
HF_TOKEN = "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"

def get_prompt(sentence):
    print(f"Prompting NVIDIA for: {sentence[:30]}...")
    headers = {"Authorization": f"Bearer {NVIDIA_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "meta/llama3-70b-instruct", 
        "messages": [{"role": "user", "content": f"Create a detailed visual prompt for this sentence in a {STYLE} style. Just return the prompt text. Sentence: {sentence}"}]
    }
    try:
        r = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", headers=headers, json=payload)
        return r.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"{STYLE} style image of: {sentence}" 

def get_image(prompt, idx):
    print(f"Generating image {idx+1}...")
    headers = {"Authorization": f"Bearer {KIE_AI_KEY}", "Content-Type": "application/json"}
    payload = {"model": "z-image", "prompt": prompt}
    try:
        r = requests.post("https://api.kie.ai/v1/images/generations", headers=headers, json=payload)
        url = r.json()['data'][0]['url']
        with open(f"image_{idx}.png", 'wb') as f:
            f.write(requests.get(url).content)
    except Exception as e:
        subprocess.run(['ffmpeg', '-f', 'lavfi', '-i', 'color=c=black:s=1280x720', '-vframes', '1', f"image_{idx}.png"])

def get_audio(sentence, idx):
    print(f"Generating audio {idx+1}...")
    subprocess.run(["edge-tts", "--text", sentence, "--write-media", f"audio_{idx}.mp3"])

def main():
    sentences = [s.strip() for s in SCRIPT_TEXT.split('.') if s.strip() and len(s) > 2]
    
    with open('concat.txt', 'w', encoding='utf-8') as concat_file:
        for idx, sentence in enumerate(sentences):
            prompt = get_prompt(sentence)
            get_image(prompt, idx)
            get_audio(sentence, idx)
            
            subprocess.run([
                'ffmpeg', '-loop', '1', '-i', f'image_{idx}.png', 
                '-i', f'audio_{idx}.mp3', '-c:v', 'libx264', '-tune', 'stillimage', 
                '-c:a', 'aac', '-b:a', '192k', '-pix_fmt', 'yuv420p', '-shortest', f'clip_{idx}.mp4'
            ])
            concat_file.write(f"file 'clip_{idx}.mp4'\n")
            
    print("Stitching final video...")
    out_file = f"{TITLE.replace(' ', '_')}.mp4"
    subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'concat.txt', '-c', 'copy', out_file])
    
    print("Uploading to Hugging Face...")
    api = HfApi(token=HF_TOKEN)
    repo_id = "sommydivinetech/test-video-dataset" 
    try:
        api.create_repo(repo_id=repo_id, repo_type="dataset", exist_ok=True)
        url = api.upload_file(path_or_fileobj=out_file, path_in_repo=out_file, repo_id=repo_id, repo_type="dataset")
        print(f"COMPLETED! Final video URL: {url}")
    except Exception as e:
        print(f"Upload failed: {e}")

if __name__ == "__main__":
    main()
