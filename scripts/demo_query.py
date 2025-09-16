import os, sys
print('CWD=', os.getcwd())
print('sys.path[0]=', sys.path[0])
print('files=', os.listdir('.'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi.testclient import TestClient
from main import app

if __name__ == "__main__":
    client = TestClient(app)
    resp = client.get(
        "/api/internships",
        params={"q": "intern", "live": "1", "limit": "96", "page": "1"},
    )
    print("status:", resp.status_code)
    js = resp.json()
    total = js.get("data", {}).get("total")
    items = js.get("data", {}).get("internships", [])
    print("total:", total)
    print("returned:", len(items))
    for it in items[:5]:
        print("-", it.get("title"))
