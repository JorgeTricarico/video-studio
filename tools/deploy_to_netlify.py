import os
import sys
import json
import zipfile
import urllib.request
import urllib.error
import time

TOKEN = 'nfp_iUtF5syw757JnXXGpoX7sB3cwVFJ3jtu4ad3'
SITE_NAME = 'cuento-firule-isai-lila'

files_to_pack = [
    ('index.html', 'index.html'),
    ('styles.css', 'styles.css'),
    ('app.js', 'app.js'),
    ('_redirects', '_redirects'),
    ('netlify/functions/track.js', 'netlify/functions/track.js'),
    ('cuento_firule_isai.mp4', 'cuento_firule_isai.mp4'),
    ('audio_final_master.mp3', 'audio_final_master.mp3'),
    ('qr_imprimible_jardin.png', 'qr_imprimible_jardin.png'),
    ('qr_code_solo.png', 'qr_code_solo.png'),
    ('assets/firule/00_dibujo_original_isai.jpg', 'assets/firule/00_dibujo_original_isai.jpg'),
    ('assets/firule/00_dibujo_original_4x3.jpg', 'assets/firule/00_dibujo_original_4x3.jpg'),
    ('assets/firule/01_portada_ia.jpg', 'assets/firule/01_portada_ia.jpg'),
    ('assets/firule/02_paseo_parque.jpg', 'assets/firule/02_paseo_parque.jpg'),
    ('assets/firule/02b_tropiezo_pantufla_pasillo.jpg', 'assets/firule/02b_tropiezo_pantufla_pasillo.jpg'),
    ('assets/firule/02c_firule_vereda_vecinos.jpg', 'assets/firule/02c_firule_vereda_vecinos.jpg'),
    ('assets/firule/04_cuneta_enamorado.jpg', 'assets/firule/04_cuneta_enamorado.jpg'),
    ('assets/firule/04b_enamorados_vereda.jpg', 'assets/firule/04b_enamorados_vereda.jpg'),
    ('assets/firule/05_final_casa.jpg', 'assets/firule/05_final_casa.jpg'),
]

zip_path = 'dist_netlify.zip'
print(f"[*] Packaging {len(files_to_pack)} files into {zip_path}...")
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for src, dst in files_to_pack:
        if os.path.exists(src):
            zf.write(src, dst)
            print(f"  + Added: {dst} ({os.path.getsize(src)/(1024*1024):.2f} MB)")
        else:
            print(f"  ! Warning: {src} not found!")

zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
print(f"[*] Archive size: {zip_size_mb:.2f} MB")

# 1. Check or create site
headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json'
}

req = urllib.request.Request('https://api.netlify.com/api/v1/sites', headers=headers)
with urllib.request.urlopen(req) as resp:
    sites = json.loads(resp.read().decode())

target_site = None
for s in sites:
    if s.get('name') == SITE_NAME:
        target_site = s
        break

if target_site:
    site_id = target_site['id']
    site_url = target_site['ssl_url']
    print(f"[*] Found existing site: {SITE_NAME} (ID: {site_id}) -> {site_url}")
else:
    print(f"[*] Creating new site: {SITE_NAME}...")
    create_payload = json.dumps({'name': SITE_NAME}).encode()
    req_create = urllib.request.Request(
        'https://api.netlify.com/api/v1/sites',
        data=create_payload,
        headers=headers,
        method='POST'
    )
    try:
        with urllib.request.urlopen(req_create) as resp:
            new_site = json.loads(resp.read().decode())
            site_id = new_site['id']
            site_url = new_site['ssl_url']
            print(f"[OK] Created site: {SITE_NAME} (ID: {site_id}) -> {site_url}")
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode()
        print(f"[!] Name {SITE_NAME} might be taken ({err_msg}). Trying unique random name...")
        req_rand = urllib.request.Request(
            'https://api.netlify.com/api/v1/sites',
            data=b'{}',
            headers=headers,
            method='POST'
        )
        with urllib.request.urlopen(req_rand) as resp:
            new_site = json.loads(resp.read().decode())
            site_id = new_site['id']
            site_url = new_site['ssl_url']
            print(f"[OK] Created site with ID {site_id} -> {site_url}")

# 2. Deploy ZIP
print(f"[*] Deploying ZIP to Netlify site {site_id}...")
with open(zip_path, 'rb') as f:
    zip_bytes = f.read()

deploy_headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/zip'
}

req_deploy = urllib.request.Request(
    f'https://api.netlify.com/api/v1/sites/{site_id}/deploys',
    data=zip_bytes,
    headers=deploy_headers,
    method='POST'
)

with urllib.request.urlopen(req_deploy) as resp:
    deploy_info = json.loads(resp.read().decode())
    deploy_id = deploy_info['id']
    state = deploy_info['state']
    print(f"[OK] Deploy initiated! Deploy ID: {deploy_id} | State: {state}")

# 3. Wait for deploy to be ready
print("[*] Waiting for Netlify build/deployment to be ready...")
for _ in range(30):
    time.sleep(3)
    req_check = urllib.request.Request(
        f'https://api.netlify.com/api/v1/sites/{site_id}/deploys/{deploy_id}',
        headers={'Authorization': f'Bearer {TOKEN}'}
    )
    with urllib.request.urlopen(req_check) as resp:
        chk = json.loads(resp.read().decode())
        curr_state = chk.get('state')
        print(f"  ... state: {curr_state}")
        if curr_state == 'ready':
            print(f"\n[SUCCESS] SITE IS LIVE ON NETLIFY!")
            print(f"URL: {site_url}")
            # Save URL to a text file for subsequent tools
            with open("assets/firule/live_site_url.txt", "w") as uf:
                uf.write(site_url)
            break
        elif curr_state in ('error', 'failed'):
            print(f"[FAIL] Deploy failed with state: {curr_state}")
            sys.exit(1)
