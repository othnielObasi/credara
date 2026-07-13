import time

from app.services.outbox_drain import process_once


def main() -> None:
    while True:
        count = process_once()
        time.sleep(5 if count == 0 else 1)


if __name__ == '__main__':
    main()
