import requests
import json
import argparse
import time

def loadInfoFile(filepath: str) -> dict:
    '''
    load information file from LLM deployment
    1. GPU_NODE
    2. PORT
    3. BASE_URL
    4. MODEL_NAME
    '''
    env = {}
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, value = line.split("=", 1)
            env[key] = value
    return env

def poster(fileInfo: dict, usrRequest: str) -> None:
    # a random chat, go to /chat/completions port
    url = fileInfo["BASE_URL"]+"/chat/completions"
    model = fileInfo["MODEL_NAME"]

    prompt = usrRequest

    t0 = time.time()
    response = requests.post (
        url,
        json = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 512,
            "temperature": 0,
        },
        timeout = 60
    )
    t1 = time.time()

    # in case of HTTP error
    response.raise_for_status()
    data = response.json()

    llm_response = data["choices"][0]["message"].get("content","")
    finish_reason = data["choices"][0].get("finish_reason", None)

    print(f"Elapsed: {t1 - t0:.3f} s")
    print("LLM OUTPUT: ", llm_response)
    print("Finish Reason: ", finish_reason)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--info", required = True, 
                        help = "File Path of vLLM Deployment Information.")
    parser.add_argument("-u", "--usr_request", required = True, 
                        help = "User Request to LLM.")
    args = parser.parse_args()

    filepath = args.info
    fileInfo = loadInfoFile(filepath)

    usrRequest = args.usr_request
    poster(fileInfo, usrRequest)

if __name__ == "__main__":
    main()
