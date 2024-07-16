import unittest
from app import app
import os

class TestPublicationsAPI(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_publications_api(self):
        # Replace with your specific test cases
        response = self.app.get('/publications/2023')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertIn('count', data)

if __name__ == '__main__':
    unittest.main()
