import os
import unicodedata
import time

# macOS fork 안전 경고 회피 (watchdog + AppKit 충돌 방지)
os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


WATCH_DIRECTORY = "" # ex "/Users/sungbooyoon"

# Google Drive/CloudStorage 등의 임시/보호 경로에서 rename 시도 시 EPERM/EACCES가 자주 발생하므로 스킵
SKIP_SUBSTRINGS = [
    "/Library/CloudStorage/GoogleDrive-",
    "/Library/CloudStorage/OneDrive",
    "/Library/CloudStorage/Dropbox",
    "/.tmp/",
]


def should_skip(path: str) -> bool:
    return any(s in path for s in SKIP_SUBSTRINGS)

def normalize_path(path: str):
    """
    파일 또는 폴더 이름을 NFC로 정규화
    """
    # CloudStorage 임시/보호 경로는 건드리지 않음
    if should_skip(path):
        return

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
    except PermissionError as e:
        # CloudStorage/보호 폴더 등에서 흔한 케이스: 계속 감시가 돌도록 경고만 남기고 무시
        print(f"[WARN] rename skipped (permission): {path} -> {e}")
    except OSError as e:
        # macOS/CloudStorage에서 흔한 케이스: Errno 1 (Operation not permitted), Errno 13 (Permission denied)
        if getattr(e, "errno", None) in (1, 13):
            print(f"[WARN] rename skipped (os): {path} -> {e}")
        else:
            print(f"[ERROR] rename failed: {path} -> {e}")
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
        if should_skip(event.src_path):
            return
        normalize_filenames_in_directory(event.src_path)

    def on_modified(self, event):
        if should_skip(event.src_path):
            return
        normalize_filenames_in_directory(event.src_path)

    def on_moved(self, event):
        # moved 이벤트는 dest_path 기준으로 정규화
        if should_skip(event.dest_path):
            return
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