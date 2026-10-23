import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from server import create_app, normalize_phone


class SpinApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = Path(self.temp_dir.name) / "so_dien_thoai.txt"
        self.app = create_app(self.storage_file, {"https://shop.example"})
        self.app.config["TESTING"] = True

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_normalizes_vietnamese_phone_formats(self):
        self.assertEqual(normalize_phone("0912345678"), "0912345678")
        self.assertIsNone(normalize_phone("0912 345 678"))
        self.assertIsNone(normalize_phone("+84 912-345-678"))
        self.assertIsNone(normalize_phone("abc0912345678"))
        self.assertIsNone(normalize_phone("091234567"))
        self.assertIsNone(normalize_phone("1912345678"))

    def test_spin_persists_only_normalized_phone(self):
        with patch("server.secrets.randbelow", return_value=0):
            response = self.app.test_client().post(
                "/api/spin", json={"phone": "0913333333"}
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["phone"], "0913333333")
        self.assertEqual(response.json["prize"], {"id": "voucher", "name": "Voucher 49.000đ"})
        self.assertEqual(self.storage_file.read_text(encoding="utf-8"), "0913333333\n")

    def test_all_probability_boundaries_map_to_the_configured_prizes(self):
        selections = (0, 9, 10, 39, 40, 69, 70, 99)
        expected_ids = (
            "voucher",
            "voucher",
            "bim-bim",
            "bim-bim",
            "banh-tam-xoan",
            "banh-tam-xoan",
            "o-mai-man",
            "o-mai-man",
        )
        client = self.app.test_client()

        with patch("server.secrets.randbelow", side_effect=selections):
            results = [
                client.post("/api/spin", json={"phone": f"09{index:08d}"}).json["prize"]["id"]
                for index in range(len(selections))
            ]

        self.assertEqual(results, list(expected_ids))

    def test_duplicate_number_is_rejected(self):
        client = self.app.test_client()
        with patch("server.secrets.randbelow", return_value=20):
            first = client.post("/api/spin", json={"phone": "0913333333"})
            second = client.post("/api/spin", json={"phone": "0913333333"})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 409)
        self.assertEqual(second.json["error"], "Số điện thoại này đã tham gia quay thưởng!")
        self.assertEqual(self.storage_file.read_text(encoding="utf-8"), "0913333333\n")

    def test_example_phone_is_rejected_in_any_supported_format(self):
        client = self.app.test_client()
        examples = ("0912345678",)

        with patch("server.secrets.randbelow") as random_number:
            responses = [
                client.post("/api/spin", json={"phone": phone})
                for phone in examples
            ]

        self.assertEqual([response.status_code for response in responses], [400])
        self.assertTrue(
            all("số điện thoại ví dụ" in response.json["error"] for response in responses)
        )
        self.assertFalse(self.storage_file.exists())
        random_number.assert_not_called()

    def test_simultaneous_requests_allow_only_one_spin(self):
        def submit():
            with self.app.test_client() as client:
                return client.post("/api/spin", json={"phone": "0987654321"}).status_code

        with patch("server.secrets.randbelow", return_value=50):
            with ThreadPoolExecutor(max_workers=12) as executor:
                statuses = list(executor.map(lambda _: submit(), range(12)))

        self.assertEqual(statuses.count(200), 1)
        self.assertEqual(statuses.count(409), 11)
        self.assertEqual(self.storage_file.read_text(encoding="utf-8"), "0987654321\n")

    def test_simultaneous_requests_from_separate_app_instances_allow_one_spin(self):
        second_app = create_app(self.storage_file)
        apps = (self.app, second_app)

        def submit(index):
            with apps[index % len(apps)].test_client() as client:
                return client.post(
                    "/api/spin", json={"phone": "0976543210"}
                ).status_code

        with patch("server.secrets.randbelow", return_value=50):
            with ThreadPoolExecutor(max_workers=12) as executor:
                statuses = list(executor.map(submit, range(12)))

        self.assertEqual(statuses.count(200), 1)
        self.assertEqual(statuses.count(409), 11)
        self.assertEqual(self.storage_file.read_text(encoding="utf-8"), "0976543210\n")

    def test_existing_numbers_are_loaded_after_restart(self):
        self.storage_file.write_text("0901234567\n", encoding="utf-8")
        restarted_app = create_app(self.storage_file)
        response = restarted_app.test_client().post(
            "/api/spin", json={"phone": "0901234567"}
        )
        self.assertEqual(response.status_code, 409)

    def test_cors_only_allows_configured_origin(self):
        allowed = self.app.test_client().post(
            "/api/spin",
            json={"phone": "0933333333"},
            headers={"Origin": "https://shop.example"},
        )
        denied = self.app.test_client().post(
            "/api/spin",
            json={"phone": "0944444444"},
            headers={"Origin": "https://unapproved.example"},
        )
        self.assertEqual(allowed.headers["Access-Control-Allow-Origin"], "https://shop.example")
        self.assertNotIn("Access-Control-Allow-Origin", denied.headers)


if __name__ == "__main__":
    unittest.main()
