import os
import re
import secrets
import threading
from contextlib import contextmanager
from pathlib import Path

from flask import Flask, jsonify, request
from waitress import serve


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "so_dien_thoai.txt"
EXAMPLE_PHONE = "0912345678"
PRIZES = (
    ("voucher", "Voucher 49.000đ", 10),
    ("bim-bim", "1 gói Bim Bim", 30),
    ("banh-tam-xoan", "1 gói Bánh Tăm Xoắn", 30),
    ("o-mai-man", "1 gói Ô Mai Mận", 30),
)
PARTICIPATION_LOCK = threading.Lock()


def normalize_phone(value):
    if not isinstance(value, str) or not re.fullmatch(r"0[0-9]{9}", value):
        return None
    return value


def load_participated_numbers(storage_file):
    numbers = set()
    if not storage_file.exists():
        return numbers

    with storage_file.open("r", encoding="utf-8") as data:
        for line_number, line in enumerate(data, start=1):
            number = line.strip()
            if not number:
                continue
            normalized = normalize_phone(number)
            if normalized is None or normalized != number:
                raise RuntimeError(
                    f"Invalid phone number in {storage_file}, line {line_number}"
                )
            numbers.add(number)
    return numbers


@contextmanager
def locked_phone_file(storage_file):
    storage_file.parent.mkdir(parents=True, exist_ok=True)
    lock_path = storage_file.with_name(storage_file.name + ".lock")
    with lock_path.open("a+b") as lock_file:
        lock_file.seek(0, os.SEEK_END)
        if lock_file.tell() == 0:
            lock_file.write(b"\0")
            lock_file.flush()
            os.fsync(lock_file.fileno())
        lock_file.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)

        try:
            with storage_file.open("a+", encoding="utf-8", newline="\n") as data:
                data.seek(0)
                numbers = set()
                for line_number, line in enumerate(data, start=1):
                    number = line.strip()
                    if not number:
                        continue
                    normalized = normalize_phone(number)
                    if normalized is None or normalized != number:
                        raise RuntimeError(
                            f"Invalid phone number in {storage_file}, line {line_number}"
                        )
                    numbers.add(number)
                yield data, numbers
        finally:
            lock_file.seek(0)
            if os.name == "nt":
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def choose_prize():
    selection = secrets.randbelow(100)
    for prize_id, name, probability in PRIZES:
        if selection < probability:
            return prize_id, name
        selection -= probability
    raise RuntimeError("Prize probabilities must total 100")


def create_app(storage_file=DATA_FILE, allowed_origins=None):
    storage_file = Path(storage_file)
    allowed_origins = set(
        allowed_origins
        if allowed_origins is not None
        else filter(
            None,
            (origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")),
        )
    )
    load_participated_numbers(storage_file)

    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 1024

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin")
        if origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            response.headers["Vary"] = "Origin"
        return response

    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    @app.post("/api/spin")
    def spin():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(error="Yêu cầu không hợp lệ."), 400

        phone = normalize_phone(payload.get("phone"))
        if phone is None:
            return jsonify(error="Vui lòng nhập đúng số điện thoại của bạn."), 400
        if phone == EXAMPLE_PHONE:
            return jsonify(error="Đây là số điện thoại ví dụ. Vui lòng nhập số điện thoại của bạn."), 400

        try:
            with PARTICIPATION_LOCK:
                with locked_phone_file(storage_file) as (data, participated_numbers):
                    if phone in participated_numbers:
                        return jsonify(error="Số điện thoại này đã tham gia quay thưởng!"), 409

                    prize_id, prize_name = choose_prize()
                    data.seek(0, os.SEEK_END)
                    data.write(phone + "\n")
                    data.flush()
                    os.fsync(data.fileno())
        except OSError:
            app.logger.exception("Could not lock or persist a participation record")
            return jsonify(error="Hệ thống chưa lưu được lượt quay. Vui lòng thử lại sau."), 503

        return jsonify(phone=phone, prize={"id": prize_id, "name": prize_name})

    return app


app = create_app()


if __name__ == "__main__":
    serve(app, host="127.0.0.1", port=5000, threads=8)
