import pytest
from unittest.mock import patch, MagicMock
from src.providers.google_chat.api import people_api


@pytest.mark.asyncio
class TestPeopleAPI:

    @pytest.fixture
    def dummy_creds(self):
        return MagicMock()

    @pytest.fixture
    def dummy_person(self):
        return {
            "resourceName": "people/123",
            "names": [{"displayName": "Alice Smith", "givenName": "Alice", "familyName": "Smith"}],
            "emailAddresses": [{"value": "alice@example.com"}],
            "photos": [{"url": "http://photo.url/pic.jpg"}]
        }

    @patch("src.providers.google_chat.api.people_api.get_people_service")
    def test_get_user_profile_success(self, mock_service, dummy_creds, dummy_person):
        mock_get = mock_service.return_value.people.return_value.get
        mock_get.return_value.execute.return_value = dummy_person

        result = people_api.get_user_profile("users/123", dummy_creds)

        assert result["display_name"] == "Alice Smith"
        assert result["email"] == "alice@example.com"
        assert result["profile_photo"] == "http://photo.url/pic.jpg"

    @patch("src.providers.google_chat.api.people_api.get_people_service")
    def test_get_user_profile_failure(self, mock_service, dummy_creds):
        mock_get = mock_service.return_value.people.return_value.get
        mock_get.return_value.execute.side_effect = Exception("fail")

        result = people_api.get_user_profile("users/123", dummy_creds)

        assert result is None

    @patch("src.providers.google_chat.api.people_api.get_people_service")
    def test_batch_get_user_profiles_success(self, mock_service, dummy_creds, dummy_person):
        mock_get_batch = mock_service.return_value.people.return_value.getBatchGet
        mock_get_batch.return_value.execute.return_value = {
            "responses": [{"person": dummy_person}]
        }

        result = people_api.batch_get_user_profiles(["123"], dummy_creds)

        assert isinstance(result, list)
        assert result[0]["email"] == "alice@example.com"

    @patch("src.providers.google_chat.api.people_api.get_people_service")
    def test_batch_get_user_profiles_partial(self, mock_service, dummy_creds):
        mock_get_batch = mock_service.return_value.people.return_value.getBatchGet
        mock_get_batch.return_value.execute.return_value = {
            "responses": [{"person": {}}, {}]  # second entry lacks "person"
        }

        result = people_api.batch_get_user_profiles(["1", "2"], dummy_creds)

        assert result == [{}, None]

    @patch("src.providers.google_chat.api.people_api.get_people_service")
    def test_batch_get_user_profiles_error(self, mock_service, dummy_creds):
        mock_get_batch = mock_service.return_value.people.return_value.getBatchGet
        mock_get_batch.return_value.execute.side_effect = Exception("API failed")

        result = people_api.batch_get_user_profiles(["123"], dummy_creds)

        assert result == []

    def test_get_user_email_and_display_name(self, dummy_person):
        parsed = people_api._parse_person_info(dummy_person)
        assert people_api.get_user_email(parsed) == "alice@example.com"
        assert people_api.get_user_display_name(parsed) == "Alice Smith"
