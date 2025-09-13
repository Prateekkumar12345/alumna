# This script sends multiple simple queries to a PostgreSQL database and measures the response time.
# It requires the 'sqlalchemy' library. You can install it with: pip install "sqlalchemy[psycopg2]"
#
# To run this script, replace the DATABASE_URI with your connection string.

from sqlalchemy import create_engine, text
import time

def test_db_connection(database_uri, num_requests):
    """
    Sends multiple simple queries to a PostgreSQL database using SQLAlchemy and prints the response times.

    Args:
        database_uri (str): The connection string for the PostgreSQL database.
        num_requests (int): The number of requests to send.
    """
    total_time = 0

    try:
        # Create a SQLAlchemy engine once, outside the loop for efficiency
        engine = create_engine(database_uri)
    except Exception as e:
        print(f"Failed to create database engine: {e}")
        return

    print(f"Sending {num_requests} requests to the database...")

    for i in range(num_requests):
        start_time = time.time()
        
        try:
            # Use a connection from the engine and execute a simple query
            with engine.connect() as connection:
                connection.execute(text("SELECT version();"))

            end_time = time.time()
            response_time = end_time - start_time
            total_time += response_time
            print(f"Request {i+1}/{num_requests}: {response_time:.4f} seconds")

        except Exception as e:
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
    # Your PostgreSQL connection string
    DATABASE_URI = "postgresql://ml_user:ml_password@3.7.255.54:5432/ml_db"

    # You can change this to the desired number of requests
    number_of_requests = 10

    test_db_connection(DATABASE_URI, number_of_requests)
