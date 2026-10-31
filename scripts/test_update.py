import os
import tempfile
import unittest

import update

HEADER = "host,access_posture,challenge_vendor,js_required,robots_posture,machine_interface,machine_interface_path,checked_at"


def csv(*rows, n_filler=0):
    lines = [HEADER] + list(rows)
    lines += [f"f{i:05d}.example,open,none,false,allow,none,,2026-10-31T00:00:00Z" for i in range(n_filler)]
    return "\n".join(lines) + "\n"


class UpdateTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.snap = os.path.join(self.dir, "data", "sites.csv")
        self.changes = os.path.join(self.dir, "changes")

    def run_update(self, text, day="2026-11-01", min_rows=10):
        return update.apply(text, self.snap, self.changes, day, min_rows=min_rows)

    def read_changes(self, day="2026-11-01"):
        path = os.path.join(self.changes, day[:4], f"{day}.csv")
        return open(path).read().splitlines() if os.path.exists(path) else None

    def test_wrong_header_is_refused(self):
        with self.assertRaises(update.Invalid):
            self.run_update("host,something\nexample.com,x\n" + "a.example,b\n" * 20)

    def test_too_few_rows_is_refused(self):
        with self.assertRaises(update.Invalid):
            self.run_update(csv(n_filler=5))

    def test_a_shrink_below_90_percent_is_refused(self):
        self.run_update(csv(n_filler=100))
        with self.assertRaises(update.Invalid):
            self.run_update(csv(n_filler=80), day="2026-11-02")

    def test_a_bad_hostname_is_refused(self):
        with self.assertRaises(update.Invalid):
            self.run_update(csv("not a host,open,none,false,allow,none,,2026-10-31T00:00:00Z", n_filler=20))

    def test_first_run_writes_the_snapshot_and_records_every_value_as_new(self):
        result = self.run_update(csv("a.example,open,none,false,allow,llms_txt,/llms.txt,2026-10-31T00:00:00Z", n_filler=20))
        self.assertTrue(os.path.exists(self.snap))
        lines = self.read_changes()
        self.assertEqual("host,field,old,new", lines[0])
        self.assertIn("a.example,machine_interface,,llms_txt", lines)
        self.assertEqual(21, result["sites"])

    def test_a_changed_field_is_one_change_row_and_checked_at_alone_is_not_a_change(self):
        self.run_update(csv("a.example,open,none,false,allow,none,,2026-10-31T00:00:00Z", n_filler=20))
        result = self.run_update(csv("a.example,bot_challenged,cloudflare,false,allow,none,,2026-11-02T00:00:00Z",
                                     n_filler=20).replace("2026-10-31", "2026-11-02"), day="2026-11-02")
        lines = self.read_changes("2026-11-02")
        self.assertEqual(["host,field,old,new",
                          "a.example,access_posture,open,bot_challenged",
                          "a.example,challenge_vendor,none,cloudflare"], lines)
        self.assertEqual(2, result["changes"])

    def test_an_unchanged_day_writes_no_change_file(self):
        self.run_update(csv(n_filler=20))
        result = self.run_update(csv(n_filler=20), day="2026-11-02")
        self.assertIsNone(self.read_changes("2026-11-02"))
        self.assertEqual(0, result["changes"])

    def test_the_snapshot_is_sorted_by_host(self):
        self.run_update(csv("zz.example,open,none,false,allow,none,,x", "aa.example,open,none,false,allow,none,,x", n_filler=20))
        hosts = [l.split(",")[0] for l in open(self.snap).read().splitlines()[1:]]
        self.assertEqual(sorted(hosts), hosts)


if __name__ == "__main__":
    unittest.main()
