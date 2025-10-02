from __future__ import annotations

# Convertible bond keywords (Korean + short codes)
CB_REGEX = r"(전환사채|\bCB\b|교환사채|\bEB\b|신주인수권부사채|\bBW\b)"

# Event keywords that usually indicate meaningful CB activity
EVENT_REGEX = r"(리픽싱|전환가\s*(?:재조정|조정)|전환청구|조기상환|콜옵션|풋옵션|발행결정|매입|취득)"

# Combined pattern: capture strings that mention CB + one of the event keywords
COMBINED = rf"(?:{CB_REGEX}).*?(?:{EVENT_REGEX})|(?:{EVENT_REGEX}).*?(?:{CB_REGEX})"
