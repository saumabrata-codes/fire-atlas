import requests

from backend.app.ingestion.firms.config import get_firms_api_key


def main():

    print("Checking NASA FIRMS MAP_KEY...")

    try:
        api_key = get_firms_api_key()

        if not api_key:
            print("ERROR: NASA FIRMS API key is missing.")
            return

        url = (
            "https://firms.modaps.eosdis.nasa.gov/"
            "mapserver/mapkey_status/"
        )

        response = requests.get(
            url,
            params={"MAP_KEY": api_key},
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        if isinstance(data, dict) and "transaction_limit" in data:

            print("\nSUCCESS: MAP_KEY is valid.")

            print(
                "Transaction limit:",
                data.get("transaction_limit")
            )

            print(
                "Current transactions:",
                data.get("current_transactions", "Not provided")
            )

        else:
            print("\nVerification unsuccessful.")
            print("NASA returned an unexpected response.")

    except requests.exceptions.Timeout:
        print("\nERROR: NASA FIRMS request timed out.")

    except requests.exceptions.ConnectionError:
        print("\nERROR: Could not connect to NASA FIRMS.")

    except requests.exceptions.HTTPError as error:
        print("\nERROR: NASA FIRMS returned an HTTP error.")
        print("HTTP status:", error.response.status_code)

    except Exception as error:
        print("\nVerification failed.")
        print("Error type:", type(error).__name__)


if __name__ == "__main__":
    main()