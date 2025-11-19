"""Session management for Chainlit UI."""

import uuid
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import mvk_sdk as mvk
from mvk_sdk import Metric


@dataclass
class UserSession:
    """User session state."""

    user_id: str
    session_id: str  # Entire user journey
    authenticated: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    conversation_history: list[Dict[str, Any]] = field(default_factory=list)

    def add_message(self, role: str, content: str, conversation_id: Optional[str] = None, feedback: Optional[str] = None):
        """Add a message to conversation history."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "conversation_id": conversation_id,
        }

        if feedback:
            message["feedback"] = feedback

        self.conversation_history.append(message)

    def get_recent_messages(self, n: int = 5) -> list[Dict[str, Any]]:
        """Get the most recent n messages."""
        return self.conversation_history[-n:]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "authenticated": self.authenticated,
            "created_at": self.created_at.isoformat(),
            "message_count": len(self.conversation_history)
        }


class SessionManager:
    """Manage user sessions."""

    def __init__(self):
        self._sessions: Dict[str, UserSession] = {}

    def create_session(self, user_id: str) -> UserSession:
        """
        Create a new user session.

        Args:
            user_id: Username

        Returns:
            UserSession instance
        """
        session_id = f"session_{uuid.uuid4().hex[:16]}"

        session = UserSession(
            user_id=user_id,
            session_id=session_id,
            authenticated=False
        )

        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get session by ID."""
        return self._sessions.get(session_id)

    def authenticate_session(self, session_id: str, password: str, correct_password: str) -> bool:
        """
        Authenticate a session.

        Args:
            session_id: Session ID
            password: Provided password
            correct_password: Expected password

        Returns:
            True if authenticated
        """
        import secrets
        
        session = self.get_session(session_id)
        if not session:
            return False

        if secrets.compare_digest(password, correct_password):
            session.authenticated = True
            return True

        return False

    def is_authenticated(self, session_id: str) -> bool:
        """Check if session is authenticated."""
        session = self.get_session(session_id)
        return session.authenticated if session else False

    def add_conversation(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
        conversation_id: str
    ):
        """
        Add a conversation to session history.

        Args:
            session_id: Session ID
            user_message: User's query
            assistant_message: Assistant's response
            conversation_id: Conversation ID for this query
        """
        session = self.get_session(session_id)
        if not session:
            return

        session.add_message("user", user_message, conversation_id=conversation_id)
        session.add_message("assistant", assistant_message, conversation_id=conversation_id)

    def add_feedback(self, session_id: str, conversation_id: str, feedback: str):
        """
        Add feedback for a specific conversation.

        Args:
            session_id: Session ID
            conversation_id: Conversation ID
            feedback: Feedback type ("helpful" or "not_helpful")
        """
        session = self.get_session(session_id)
        if not session:
            return

        # Find the assistant message with this conversation_id and add feedback
        for message in reversed(session.conversation_history):
            if message.get("role") == "assistant" and message.get("conversation_id") == conversation_id:
                message["feedback"] = feedback
                break

        # Track feedback in MVK
        mvk.add_metered_usage(
            Metric(
                metric_kind="user.feedback",
                quantity=1 if feedback == "helpful" else 0,
                uom="feedback"
            )
        )

    def get_conversation_context(self, session_id: str, n: int = 5) -> str:
        """
        Get recent conversation context as formatted string.

        Args:
            session_id: Session ID
            n: Number of recent messages to include

        Returns:
            Formatted conversation history
        """
        session = self.get_session(session_id)
        if not session:
            return ""

        messages = session.get_recent_messages(n)
        context = "Recent conversation:\n\n"

        for msg in messages:
            role = msg["role"].capitalize()
            content = msg["content"][:200]  # Truncate long messages
            context += f"{role}: {content}\n\n"

        return context


# Export singleton instance
session_manager = SessionManager()
