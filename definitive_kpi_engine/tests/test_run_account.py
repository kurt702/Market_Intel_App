import unittest

from run_account import build_parser


class RunAccountTests(unittest.TestCase):
    def test_reporting_year_cli_argument_is_accepted(self):
        args = build_parser().parse_args(
            ["--account", "Rush", "--input", "input", "--output", "output", "--reporting-year", "2024"]
        )
        self.assertEqual(args.reporting_year, "2024")


if __name__ == "__main__":
    unittest.main()
