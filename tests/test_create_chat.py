# This script sends multiple requests to a FastAPI endpoint and measures the response time.
# It requires the 'requests' library. You can install it with: pip install requests
#
# To run this script, your FastAPI application must be running at http://127.0.0.1:8000.

import requests
import time
import uuid

def test_endpoint(base_url, num_requests):
    """
    Sends multiple POST requests to the specified endpoint and prints the response times.

    Args:
        base_url (str): The base URL of the FastAPI application.
        num_requests (int): The number of requests to send.
    """
    endpoint = f"{base_url}/chat/create"
    total_time = 0
    
    print(f"Sending {num_requests} requests to {endpoint}...")
    
    for i in range(num_requests):
        # Generate a unique user ID for each request to simulate a new user
        user_id = str(uuid.uuid4())
        params = {"user_id": user_id}
        
        start_time = time.time()
        try:
            response = requests.post(endpoint, params=params)
            end_time = time.time()
            
            # Raise an exception for bad status codes (4xx or 5xx)
            response.raise_for_status()
            
            response_time = end_time - start_time
            total_time += response_time
            print(f"Request {i+1}/{num_requests}: {response_time:.4f} seconds")
            
        except requests.exceptions.RequestException as e:
            print(f"Request {i+1}/{num_requests} failed: {e}")
            
    if num_requests > 0:
        average_time = total_time / num_requests
        print("\n--- Summary ---")
        print(f"Total requests: {num_requests}")
        print(f"Total time: {total_time:.4f} seconds")
        print(f"Average time per request: {average_time:.4f} seconds")
    else:
        print("No requests were sent.")


if __name__ == "__main__":
    # Ensure your FastAPI server is running at this URL
    api_url = "http://127.0.0.1:8000"
    
    # You can change this to the desired number of requests
    number_of_requests = 1
    
    test_endpoint(api_url, number_of_requests)
