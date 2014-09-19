import unittest

from flask import json

from unittest.mock import patch

from flaskr_tests import FlaskrWithMongoTest, user_in_db, EMAIL_ADDRESS as USER_EMAIL_ADDRESS

NFC_TAG_ID = "tag_id"
VOTE_POSITIVE_REQUEST = """{
"mac":"MAC",
"tagId": "TAG_ID",
"isPositive": true,
"timestamp": "2014-09-18T10:32:59+00:00"
}"""
VOTE_NEGATIVE_REQUEST = """{
"mac":"MAC",
"tagId": "TAG_ID",
"isPositive": false,
"timestamp": "2014-09-18T10:32:59+00:00"
}"""


class NfcEndpointTest(FlaskrWithMongoTest, unittest.TestCase):
    def test_should_get_list_of_all_users(self):
        self.db.users.insert(user_in_db())
        self.db.users.insert(user_in_db(confirmed=True))

        response = self.app.get('/contacts')

        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(json.loads(response.data), [{"name": "Jan Kowalski", "email": "jan@kowalski.com"}])

    def test_returns_404_if_user_not_found(self):
        response = self.app.put('/contact/%s/%s' % (USER_EMAIL_ADDRESS, NFC_TAG_ID))

        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.status_code, 404)

    def test_should_assign_new_tag_to_user(self):
        self.db.users.insert(user_in_db(confirmed=True))

        response = self.app.put('/contact/%s/%s' % (USER_EMAIL_ADDRESS, NFC_TAG_ID))

        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.status_code, 201)
        self.assertIn(NFC_TAG_ID, self.db.users.find_one()['nfcTags'])

    def test_returns_200_if_tag_already_associated_with_given_user(self):
        self.db.users.insert(user_in_db(confirmed=True))

        self.app.put('/contact/%s/%s' % (USER_EMAIL_ADDRESS, NFC_TAG_ID))
        response = self.app.put('/contact/%s/%s' % (USER_EMAIL_ADDRESS, NFC_TAG_ID))

        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.status_code, 200)

    def test_returns_409_if_tag_already_associated_with_given_user(self):
        self.db.users.insert(user_in_db(confirmed=True, email="bob@example.com"))
        first_response = self.app.put('/contact/%s/%s' % ("bob@example.com", NFC_TAG_ID))
        self.assertEqual(first_response.status_code, 201)

        self.db.users.insert(user_in_db(confirmed=True))
        second_response = self.app.put('/contact/%s/%s' % (USER_EMAIL_ADDRESS, NFC_TAG_ID))

        self.assertEqual(second_response.content_type, "application/json")
        self.assertEqual(second_response.status_code, 409)

    def test_should_find_user_for_given_tag(self):
        self.db.users.insert(user_in_db(confirmed=True, nfcTags=[NFC_TAG_ID]))

        response = self.app.get('/contact/%s' % NFC_TAG_ID)

        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.status_code, 200)

    def test_returns_404_if_user_not_found_by_tag(self):
        response = self.app.get('/contact/%s' % NFC_TAG_ID)

        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.status_code, 404)

    def test_should_register_new_votes(self):
        response = self.app.post('/vote', data=VOTE_POSITIVE_REQUEST, content_type="application/json")

        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.status_code, 201)

    def test_should_register_changed_votes(self):
        first_response = self.app.post('/vote', data=VOTE_POSITIVE_REQUEST, content_type="application/json")
        self.assertEqual(first_response.status_code, 201)

        second_response = self.app.post('/vote', data=VOTE_NEGATIVE_REQUEST, content_type="application/json")

        self.assertEqual(second_response.content_type, "application/json")
        self.assertEqual(second_response.status_code, 200)

    def test_should_register_not_changed_votes(self):
        first_response = self.app.post('/vote', data=VOTE_POSITIVE_REQUEST, content_type="application/json")
        self.assertEqual(first_response.status_code, 201)

        second_response = self.app.post('/vote', data=VOTE_POSITIVE_REQUEST, content_type="application/json")

        self.assertEqual(second_response.content_type, "application/json")
        self.assertEqual(second_response.status_code, 304)


if __name__ == '__main__':
    unittest.main()