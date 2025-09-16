import requests

def test_internships_endpoint():
    url = "http://localhost:8001/api/internships"
    params = {
        "q": "intern",
        "live": 1,
        "limit": 5,
        "page": 1
    }
    
    try:
        response = requests.get(url, params=params)
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(response.json())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_internships_endpoint()
