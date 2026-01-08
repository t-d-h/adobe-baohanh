import time

import requests

def get_otp_from_otp79s(local_prefix, timeout=60, poll_interval=3):
    """Poll the otp79s API for an OTP entry matching local_prefix.

    The API response is expected to contain a key 'adobe-bs' with a list of
    items like {"code":"220047","email":"awefad-343412341235",...}.
    We match against the `email` field using the local_prefix (without domain).
    Returns the code string on success, or empty string on timeout/failure.
    """
    url = "https://api.otp79s.com/api/codes"
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            entries = data.get('adobe-bs') or []
            for item in entries:
                try:
                    if 'email' in item and local_prefix in item['email']:
                        return str(item.get('code', ''))
                except Exception:
                    continue
        except Exception:
            pass
        time.sleep(poll_interval)
    return ""
