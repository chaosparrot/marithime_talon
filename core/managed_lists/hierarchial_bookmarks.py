import re
import os

# Regex taken from validator_collection package
URL_REGEX = re.compile(
    r"^"
    # protocol identifier
    r"(?:(?:https?|ftp)://)"
    # user:pass authentication
    r"(?:\S+(?::\S*)?@)?"
    r"(?:"
    # IP address exclusion
    # private & local networks
    r"(?!(?:10|127)(?:\.\d{1,3}){3})"
    r"(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})"
    r"(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})"
    # IP address dotted notation octets
    # excludes loopback network 0.0.0.0
    # excludes reserved space >= 224.0.0.0
    # excludes network & broadcast addresses
    # (first & last IP address of each class)
    r"(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])"
    r"(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}"
    r"(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))"
    r"|"
    r"(?:"
    r"(?:localhost|invalid|test|example)|("
    # host name
    r"(?:(?:[A-z\u00a1-\uffff0-9]-*_*)*[A-z\u00a1-\uffff0-9]+)"
    # domain name
    r"(?:\.(?:[A-z\u00a1-\uffff0-9]-*)*[A-z\u00a1-\uffff0-9]+)*"
    # TLD identifier
    r"(?:\.(?:[A-z\u00a1-\uffff]{2,}))"
    r")))"
    # port number
    r"(?::\d{2,5})?"
    # resource path
    r"(?:/\S*)?"
    r"$"
    , re.UNICODE)

# Supports URLs and paths
class HierarchialBookmarks:

    websites = None
    paths = None

    def __init__(self):
        self.directory = ""
        self.websites = {}
        self.paths = {}

    def is_url(self, value: str) -> bool:
        return URL_REGEX.match(value.lower())

    def is_path(self, value: str) -> bool:
        return os.path.exists(value)
    
    def can_bookmark(self, value: str) -> bool:
        return self.is_url(value) or self.is_path(value)

    def persist(self, value: str, name: str):
        if self.is_path(value):
            self.paths[name] = value
        elif self.is_url(value):
            self.websites[name] = value
