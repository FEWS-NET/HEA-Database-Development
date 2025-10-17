import logging


class SuppressWebSocketPings(logging.Filter):

    def filter(self, record):
        suppress_phrases = [
            "sending keepalive ping",
            "received keepalive pong",
            "> PING",
            "< PONG",
            "% sending keepalive",
            "% received keepalive",
            "ASGI 'lifespan' protocol appears unsupported.",
        ]

        message = record.getMessage()

        for phrase in suppress_phrases:
            if phrase in message:
                return False  # Don't log this message

        return True


class SuppressRevProxyNoise(logging.Filter):

    def filter(self, record):
        # Suppress these RevProxy messages
        suppress_phrases = [
            "ProxyView created",
            "Normalizing response headers",
            "Checking for invalid cookies",
            "Starting streaming HTTP Response",
        ]

        message = record.getMessage()

        for phrase in suppress_phrases:
            if phrase in message:
                return False

        return True
