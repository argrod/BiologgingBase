import unittest

from readIn import dtFormat

class TestDtFormat(unittest.TestCase):
    def test_dtFormat():
        """
        Ensure incorrect datetime formats are corrected. Primary issue is removal of second period and any
        """

        data = "2018-08-08 12:00:01.001%.000+:00"
        result = dtFormat(data)
        self.assertEqual(result,"2018-08-08 12:00:01.001")

if __name__ == '__main__':
    unittest.main()
