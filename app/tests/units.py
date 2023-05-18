import unittest

from app import get_test_client


class FlaskAppTestCase(unittest.TestCase):

    def setUp(self):
        self.app = get_test_client()

    def tearDown(self):
        pass

    def test_show_env(self):
        response = self.app.get('/env')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

    def test_test_db(self):
        response = self.app.get('/test_db')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        try:
            self.assertEqual(response.json['message'], 'Connection to the database successful')
        except KeyError:
            print("Received unexpected response: ", response.json)
            raise


if __name__ == '__main__':
    unittest.main()
