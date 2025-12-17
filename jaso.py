import os
import unicodedata
import time

# macOS fork 안전 경고 회피 (watchdog + AppKit 충돌 방지)
os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


WATCH_DIRECTORY = "" # ex. "/Users/sungbooyoon"


def normalize_path(path: str):
    """
    파일 또는 폴더 이름을 NFC로 정규화
    """
    if not os.path.lexists(path):
        return

    directory, name = os.path.split(path)
    if not name:
        return

    normalized_name = unicodedata.normalize("NFC", name)

    if name == normalized_name:
        return

    new_path = os.path.join(directory, normalized_name)

    try:
        os.rename(path, new_path)
    except FileExistsError:
        # 동일 이름 충돌 시 무시 (필요하면 (1) 붙이도록 확장 가능)
        pass
    except Exception as e:
        print(f"[ERROR] rename failed: {path} -> {e}")


def normalize_filenames_in_directory(directory: str):
    """
    주어진 디렉토리 및 하위 전체를 깊이 우선으로 NFC 정규화
    """
    if not os.path.isdir(directory):
        normalize_path(directory)
        return

    # 하위부터 처리 (안전)
    for root, dirs, files in os.walk(directory, topdown=False):
        for fname in files:
            normalize_path(os.path.join(root, fname))
        for dname in dirs:
            normalize_path(os.path.join(root, dname))

    # 최상위 디렉토리 자체도 처리
    normalize_path(directory)


class Handler(FileSystemEventHandler):
    """
    파일 시스템 이벤트 핸들러
    """

    def on_created(self, event):
        normalize_filenames_in_directory(event.src_path)

    def on_modified(self, event):
        normalize_filenames_in_directory(event.src_path)

    def on_moved(self, event):
        normalize_filenames_in_directory(event.dest_path)


def main():
    if not os.path.isdir(WATCH_DIRECTORY):
        raise RuntimeError(f"Directory not found: {WATCH_DIRECTORY}")

    print(f"[INFO] Watching directory: {WATCH_DIRECTORY}")

    event_handler = Handler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIRECTORY, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main()