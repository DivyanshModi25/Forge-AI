import time
import urllib.error
import urllib.request


def check_health(url:str, timeout_seconds:int = 30) -> dict:
    """Check whether an HTTP endpoint becomes healthy."""

    deadline = time.monotonic() + timeout_seconds
    last_error = "No response received."

    while time.monotonic() < deadline:
        try:
            request = urllib.request.Request(
                url,
                method="GET",
            )

            with urllib.request.urlopen(
                request,
                timeout=3,
            ) as response:
                status_code = response.status

                if 200 <= status_code < 400:
                    return {
                        "healthy": True,
                        "url": url,
                        "status_code": status_code,
                    }

                last_error = f"HTTP status {status_code}"

        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = str(exc)

        time.sleep(2)

    return {
        "healthy": False,
        "url": url,
        "error": last_error,
    }


if __name__ == "__main__":

    print(check_health("http://localhost:8080"))