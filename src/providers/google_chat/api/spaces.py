from typing import List, Dict

from googleapiclient.discovery import build

from src.providers.google_chat.api.auth import get_credentials


async def list_chat_spaces() -> List[Dict]:
    """Lists all Google Chat spaces the bot has access to."""
    try:
        creds = get_credentials()
        if not creds:
            raise Exception("No valid credentials found. Please authenticate first.")

        service = build('chat', 'v1', credentials=creds)
        spaces = service.spaces().list(pageSize=30).execute()
        return spaces.get('spaces', [])
    except Exception as e:
        raise Exception(f"Failed to list chat spaces: {str(e)}")

async def manage_space_members(space_name: str, operation: str, user_emails: List[str]) -> Dict:
    """Manage space membership - add or remove members.

    Args:
        space_name: The name/identifier of the space
        operation: Either 'add' or 'remove'
        user_emails: List of user email addresses to add or remove

    Returns:
        Response with information about the operation

    Raises:
        Exception: If authentication fails or operation fails
    """
    try:
        creds = get_credentials()
        if not creds:
            raise Exception("No valid credentials found. Please authenticate first.")

        service = build('chat', 'v1', credentials=creds)

        if not space_name.startswith('spaces/'):
            space_name = f"spaces/{space_name}"

        if operation.lower() not in ['add', 'remove']:
            raise ValueError("Operation must be either 'add' or 'remove'")

        results = {
            "operation": operation,
            "space": space_name,
            "successful": [],
            "failed": []
        }

        for email in user_emails:
            try:
                if operation.lower() == 'add':
                    # Add member to space
                    member_body = {
                        "member": {
                            "name": f"users/{email}",
                            "type": "HUMAN"
                        }
                    }
                    service.spaces().members().create(
                        parent=space_name,
                        body=member_body
                    ).execute()
                    results["successful"].append(email)
                else:
                    # Remove member from space
                    member_name = f"{space_name}/members/users/{email}"
                    service.spaces().members().delete(name=member_name).execute()
                    results["successful"].append(email)
            except Exception as e:
                results["failed"].append({
                    "email": email,
                    "error": str(e)
                })

        return results

    except ValueError:
        raise  # Let specific errors propagate for validation checks

    except Exception as e:
        raise Exception(f"Failed to manage space members: {str(e)}")

