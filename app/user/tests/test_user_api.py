from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
VIEW_USER_URL = reverse('user:detail')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_successfully(self):
        payload = {
            'email': 'test@progyny.com',
            'password': 'secret',
            'name': 'Test'
        }

        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(**response.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', response.data)

    def test_user_exists(self):
        payload = {
            'email': 'test@progyny.com',
            'password': 'secret',
            'name': 'Test'
        }
        create_user(**payload)

        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEquals(response.status_code,
                          status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        payload = {
            'email': 'test@progyny.com',
            'password': 'pw',
            'name': 'Test'
        }

        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEquals(response.status_code,
                          status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        payload = {
            'email': 'test@progyny.com',
            'password': 'secret',
        }
        create_user(**payload)

        response = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', response.data)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        create_user(email='test@progyny.com', password='secret')
        payload = {
            'email': 'test@progyny.com',
            'password': 'wrong',
        }

        response = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', response.data)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        payload = {
            'email': 'test@progyny.com',
            'password': 'secret',
        }

        response = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', response.data)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_password(self):
        payload = {
            'email': 'test@progyny.com',
            'password': '',
        }

        response = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', response.data)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_user_unauthorized(self):
        response = self.client.get(VIEW_USER_URL)

        self.assertEquals(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):

    def setUp(self):
        self.user = create_user(
            email='test@progyny.com',
            password='secret',
            name='name'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_user_detail_valid(self):
        response = self.client.get(VIEW_USER_URL)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data, {
            'email': self.user.email,
            'name': self.user.name
        })
    
    def test_post_detail_not_allowed(self):
        response = self.client.post(VIEW_USER_URL, {})

        self.assertEquals(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_update_user_detail_success(self):
        payload = {
            'email': 'new@progyny.com',
            'password': 'newpassword',
            'name': 'newname'
        }

        response = self.client.patch(VIEW_USER_URL, payload)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
    
        self.assertEquals(self.user.email, payload['email'])
        self.assertEquals(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
