from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import transaction
from app.auth.security import hash_password, verify_password
from app.errors import ConflictError, UnauthorizedError
from app.models import User, Workspace, WorkspaceMember
from app.repositories.base import UserRepository, WorkspaceRepository
from app.schemas.auth import RegisterRequest, RegisterResponse, UserResponse

# Compared against when the email is unknown, so "no such user" takes as long as
# "wrong password" and response time does not reveal which emails are registered.
_DUMMY_PASSWORD_HASH = hash_password("not-a-real-password")


class UserService:
    def __init__(self, session: Session, users: UserRepository, workspaces: WorkspaceRepository):
        self.session = session
        self.users = users
        self.workspaces = workspaces

    def register(self, payload: RegisterRequest) -> RegisterResponse:
        email = payload.email.strip().lower()
        # Friendly fast path. Not sufficient on its own: two concurrent requests can both
        # pass this check, so the UNIQUE constraint on users.email is the real guarantee.
        if self.users.get_by_email(email) is not None:
            raise ConflictError("EMAIL_ALREADY_EXISTS", "Email is already registered")

        try:
            # User + Personal Workspace + OWNER membership: all three or none.
            with transaction(self.session):
                user = self.users.add(
                    User(name=payload.name, email=email, password_hash=hash_password(payload.password))
                )  # flush → user.id usable
                workspace = self.workspaces.add(Workspace(name=f"{payload.name}'s Workspace", owner_user_id=user.id))
                self.workspaces.add_member(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="OWNER"))
        except IntegrityError as exc:
            if "uq_users_email" in str(exc.orig):
                raise ConflictError("EMAIL_ALREADY_EXISTS", "Email is already registered") from exc
            raise

        return RegisterResponse(user=UserResponse.model_validate(user), personal_workspace_id=workspace.id)

    def authenticate(self, email: str, password: str) -> User:
        user = self.users.get_by_email(email.strip().lower())
        password_ok = verify_password(password, user.password_hash if user else _DUMMY_PASSWORD_HASH)
        # Same message for "no such email" and "wrong password": don't reveal which emails exist.
        if user is None or not password_ok:
            raise UnauthorizedError("Invalid email or password")
        return user
