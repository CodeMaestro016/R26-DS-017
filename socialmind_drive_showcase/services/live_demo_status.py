"""Reachability check for Component 3's remote CARLA live demo.

Unlike Component 2 (a local subprocess this app launches and monitors
directly via ComponentLauncher), Component 3's live demo runs on a separate
rented GPU instance and is only reachable through whatever network path
(SSH tunnel, opened port, etc.) currently connects this machine to it.
There is nothing to launch or supervise here -- this just answers one
question for the UI: right now, does something respond at that URL?
"""

import urllib.error
import urllib.request


def is_live_demo_reachable(url, timeout=2.0):
    """True if an HTTP request to `url` gets any response at all.

    Deliberately tolerant of every failure mode (connection refused, DNS
    failure, timeout, non-200 status that still proves something is there,
    etc.) -- callers only care about "is the tunnel/instance up", not why
    it might not be.
    """
    try:
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except urllib.error.HTTPError:
        # Any HTTP response (even an error status) means something is
        # listening and answering -- that's reachable for our purposes.
        return True
    except Exception:
        return False
