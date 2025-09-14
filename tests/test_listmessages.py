import requests
import time

def test_chat_messages(base_url, chat_id, num_requests):
    """
    Sends multiple GET requests to the /chat/messages endpoint and prints response times.

    Args:
        base_url (str): The base URL of the FastAPI application.
        chat_id (str): The chat ID to query.
        num_requests (int): The number of requests to send.
    """
    endpoint = f"{base_url}/chat/messages"
    total_time = 0

    print(f"Sending {num_requests} requests to {endpoint} with chat_id={chat_id}...")

    for i in range(num_requests):
        params = {"chat_id": chat_id}

        start_time = time.time()
        try:
            response = requests.get(endpoint, params=params)
            end_time = time.time()

            # Raise error for non-200 responses
            response.raise_for_status()

            response_time = end_time - start_time
            total_time += response_time

            print(f"Request {i+1}/{num_requests}: {response_time:.4f} seconds")
            print("Response JSON:", response.json())  # ✅ print response body

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
    api_url = "http://127.0.0.1:8000"

    # Replace with a valid chat_id from your DB
    chat_id = "chat_4c5d3f07ce45"

    # Change to desired number of requests
    number_of_requests = 10

    test_chat_messages(api_url, chat_id, number_of_requests)
