import time
import requests

def clean_sql_output(text: str) -> str:
    text = text.strip()

    # remove possible special tokens
    text = text.split("<eot_id>")[0].strip()
    text = text.split("<|eot_id|>")[0].strip()

    # remove markdown fences
    if text.startswith("```"):
        lines = text.splitlines()

        # remove first ```sql or ```
        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        # remove last ```
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    # optional: keep only from first SELECT
    upper = text.upper()
    idx = upper.find("SELECT")
    if idx != -1:
        text = text[idx:].strip()

    return text

def safe_load_info_file(filepath, warmup_time=2):
    t0 = time.time()
    print("Waiting for Server Warmup")
    time.sleep(warmup_time)
    print("Warmup Finished")
    env = {}
    with open(filepath, "r") as f:
        print("\n","=="*10)
        print(f"Server Info File: {filepath}")
        print("=="*10, "\n")

        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def wait_vllm_ready(info_path, timeout=300, interval=2):
    info = safe_load_info_file(info_path)

    base_url = info["BASE_URL"].rstrip("/")
    model_name = info.get("MODEL_NAME")
    url = base_url + "/models"

    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                model_ids = [m["id"] for m in data.get("data", [])]

                print("\nvLLM ready.")
                print(f"Available models: {model_ids}\n")
                return info

        except requests.RequestException:
            pass

        print(f"Waiting for vLLM at {url} ...")
        time.sleep(interval)

    raise RuntimeError(f"vLLM not ready after {timeout}s: {url}")