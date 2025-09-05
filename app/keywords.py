CB_REGEX = r"(전환사채|\bCB\b|교환사채|\bEB\b|신주인수권부사채|\bBW\b)"
EVENT_REGEX = r"(리픽싱|전환가(액)?\s*조정|전환청구|조기상환|콜옵션|풋옵션|오버행|발행결정|납입)"
COMBINED = rf"(?:{CB_REGEX}).*?(?:{EVENT_REGEX})|(?:{EVENT_REGEX}).*?(?:{CB_REGEX})"
