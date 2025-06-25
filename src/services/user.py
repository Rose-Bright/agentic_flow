"""
User Service - Manages user operations and authentication
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import uuid

from ..models.user import (
    User,
    UserCreate,
    UserUpdate,
    UserSession,
    UserRole,
    Token,
    TokenPayload
)
from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.security import get_password_hash, verify_password, create_access_token

logger = get_logger(__name__)


class UserService:
    """Service for managing users and authentication"""
    
    def __init__(self):
        self.settings = get_settings()
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, UserSession] = {}
        self.user_roles: Dict[str, UserRole] = {}
        self.initialized = False
    
    async def initialize(self):
        """Initialize the user service"""
        if self.initialized:
            return
        
        logger.info("Initializing User Service...")
        
        try:
            # Load default user roles
            await self._load_default_roles()
            
            # Create default admin user
            await self._create_default_admin()
            
            self.initialized = True
            logger.info("User Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize User Service: {e}")
            raise
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        try:
            # Check if user already exists
            existing_user = await self.get_by_email(user_data.email)
            if existing_user:
                raise ValueError(f"User with email {user_data.email} already exists")
            
            # Generate user ID
            user_id = str(uuid.uuid4())
            
            # Hash password
            hashed_password = get_password_hash(user_data.password)
            
            # Create user
            user = User(
                id=user_id,
                email=user_data.email,
                full_name=user_data.full_name,
                hashed_password=hashed_password,
                roles=user_data.roles,
                is_active=True,
                is_admin="admin" in user_data.roles,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                metadata=user_data.metadata
            )
            
            # Store user
            self.users[user_id] = user
            
            logger.info(f"Created user: {user.email}")
            return user
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            return self.users.get(user_id)
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            for user in self.users.values():
                if user.email == email:
                    return user
            return None
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        try:
            user = await self.get_by_email(email)
            if not user:
                return None
            
            if not user.is_active:
                return None
            
            if not verify_password(password, user.hashed_password):
                return None
            
            # Update last login
            user.last_login = datetime.utcnow()
            user.updated_at = datetime.utcnow()
            
            logger.info(f"User authenticated: {email}")
            return user
            
        except Exception as e:
            logger.error(f"Error authenticating user {email}: {e}")
            return None
    
    async def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[User]:
        """Update user information"""
        try:
            user = await self.get_by_id(user_id)
            if not user:
                return None
            
            # Update fields if provided
            if user_update.email is not None:
                user.email = user_update.email
            if user_update.full_name is not None:
                user.full_name = user_update.full_name
            if user_update.password is not None:
                user.hashed_password = get_password_hash(user_update.password)
            if user_update.roles is not None:
                user.roles = user_update.roles
                user.is_admin = "admin" in user_update.roles
            if user_update.is_active is not None:
                user.is_active = user_update.is_active
            if user_update.metadata is not None:
                user.metadata.update(user_update.metadata)
            
            user.updated_at = datetime.utcnow()
            
            logger.info(f"Updated user: {user.email}")
            return user
            
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            return None
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user (soft delete by deactivating)"""
        try:
            user = await self.get_by_id(user_id)
            if not user:
                return False
            
            # Soft delete by deactivating
            user.is_active = False
            user.updated_at = datetime.utcnow()
            
            # Invalidate all user sessions
            await self._invalidate_user_sessions(user_id)
            
            logger.info(f"Deleted (deactivated) user: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False
    
    async def create_access_token(self, user: User) -> Token:
        """Create access token for user"""
        try:
            # Create token payload
            token_payload = TokenPayload(
                sub=user.id,
                exp=datetime.utcnow() + timedelta(minutes=self.settings.access_token_expire_minutes),
                roles=user.roles,
                metadata={"email": user.email, "full_name": user.full_name}
            )
            
            # Generate access token
            access_token = create_access_token(
                subject=user.id,
                expires_delta=timedelta(minutes=self.settings.access_token_expire_minutes)
            )
            
            # Create token response
            token = Token(
                access_token=access_token,
                token_type="bearer",
                expires_in=self.settings.access_token_expire_minutes * 60
            )
            
            logger.info(f"Created access token for user: {user.email}")
            return token
            
        except Exception as e:
            logger.error(f"Error creating access token for user {user.id}: {e}")
            raise
    
    async def create_session(
        self,
        user: User,
        ip_address: str,
        user_agent: str
    ) -> UserSession:
        """Create user session"""
        try:
            session_id = str(uuid.uuid4())
            
            session = UserSession(
                session_id=session_id,
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                started_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            
            self.sessions[session_id] = session
            
            logger.info(f"Created session for user: {user.email}")
            return session
            
        except Exception as e:
            logger.error(f"Error creating session for user {user.id}: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get user session"""
        try:
            session = self.sessions.get(session_id)
            
            if session and session.expires_at > datetime.utcnow():
                # Update last activity
                session.last_activity = datetime.utcnow()
                return session
            elif session:
                # Session expired, remove it
                del self.sessions[session_id]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None
    
    async def invalidate_session(self, session_id: str) -> bool:
        """Invalidate user session"""
        try:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"Invalidated session: {session_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error invalidating session {session_id}: {e}")
            return False
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False
    ) -> List[User]:
        """List users with pagination"""
        try:
            users = list(self.users.values())
            
            # Filter active/inactive users
            if not include_inactive:
                users = [user for user in users if user.is_active]
            
            # Apply pagination
            return users[skip:skip + limit]
            
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []
    
    async def get_user_roles(self, user_id: str) -> List[UserRole]:
        """Get roles for a user"""
        try:
            user = await self.get_by_id(user_id)
            if not user:
                return []
            
            roles = []
            for role_name in user.roles:
                role = self.user_roles.get(role_name)
                if role:
                    roles.append(role)
            
            return roles
            
        except Exception as e:
            logger.error(f"Error getting user roles for {user_id}: {e}")
            return []
    
    async def assign_role(self, user_id: str, role_name: str) -> bool:
        """Assign role to user"""
        try:
            user = await self.get_by_id(user_id)
            if not user:
                return False
            
            if role_name not in user.roles:
                user.roles.append(role_name)
                user.updated_at = datetime.utcnow()
                
                # Update admin status
                user.is_admin = "admin" in user.roles
                
                logger.info(f"Assigned role {role_name} to user: {user.email}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error assigning role {role_name} to user {user_id}: {e}")
            return False
    
    async def remove_role(self, user_id: str, role_name: str) -> bool:
        """Remove role from user"""
        try:
            user = await self.get_by_id(user_id)
            if not user:
                return False
            
            if role_name in user.roles:
                user.roles.remove(role_name)
                user.updated_at = datetime.utcnow()
                
                # Update admin status
                user.is_admin = "admin" in user.roles
                
                logger.info(f"Removed role {role_name} from user: {user.email}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing role {role_name} from user {user_id}: {e}")
            return False
    
    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        try:
            user = await self.get_by_id(user_id)
            if not user:
                return False
            
            # Verify old password
            if not verify_password(old_password, user.hashed_password):
                return False
            
            # Update password
            user.hashed_password = get_password_hash(new_password)
            user.updated_at = datetime.utcnow()
            
            # Invalidate all user sessions to force re-login
            await self._invalidate_user_sessions(user_id)
            
            logger.info(f"Changed password for user: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error changing password for user {user_id}: {e}")
            return False
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            current_time = datetime.utcnow()
            expired_sessions = [
                session_id for session_id, session in self.sessions.items()
                if session.expires_at <= current_time
            ]
            
            for session_id in expired_sessions:
                del self.sessions[session_id]
            
            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
    
    # Private helper methods
    async def _load_default_roles(self):
        """Load default user roles"""
        self.user_roles = {
            "admin": UserRole(
                name="admin",
                permissions=[
                    "read_all", "write_all", "delete_all", "manage_users",
                    "manage_agents", "manage_tools", "manage_system"
                ],
                scope="global",
                metadata={"description": "Full system administrator"}
            ),
            "supervisor": UserRole(
                name="supervisor",
                permissions=[
                    "read_all", "write_conversations", "manage_agents",
                    "escalate_conversations", "view_metrics", "transfer_conversations"
                ],
                scope="department",
                metadata={"description": "Department supervisor"}
            ),
            "agent": UserRole(
                name="agent",
                permissions=[
                    "read_customer_data", "write_conversations", "use_tools",
                    "escalate_conversations", "view_own_metrics"
                ],
                scope="conversations",
                metadata={"description": "Customer service agent"}
            ),
            "technical_agent": UserRole(
                name="technical_agent",
                permissions=[
                    "read_customer_data", "write_conversations", "use_tools",
                    "run_diagnostics", "escalate_conversations", "schedule_visits"
                ],
                scope="technical_support",
                metadata={"description": "Technical support agent"}
            ),
            "billing_agent": UserRole(
                name="billing_agent",
                permissions=[
                    "read_customer_data", "write_conversations", "use_tools",
                    "process_payments", "apply_credits", "view_billing_data"
                ],
                scope="billing_support",
                metadata={"description": "Billing support agent"}
            ),
            "sales_agent": UserRole(
                name="sales_agent",
                permissions=[
                    "read_customer_data", "write_conversations", "use_tools",
                    "generate_quotes", "process_orders", "view_sales_data"
                ],
                scope="sales_support",
                metadata={"description": "Sales support agent"}
            ),
            "readonly": UserRole(
                name="readonly",
                permissions=["read_conversations", "view_metrics"],
                scope="limited",
                metadata={"description": "Read-only access"}
            )
        }
    
    async def _create_default_admin(self):
        """Create default admin user if none exists"""
        try:
            # Check if admin already exists
            admin_email = "admin@contactcenter.ai"
            existing_admin = await self.get_by_email(admin_email)
            
            if not existing_admin:
                admin_data = UserCreate(
                    email=admin_email,
                    password="ContactCenter2024!",  # Should be changed on first login
                    full_name="System Administrator",
                    roles=["admin"],
                    metadata={"created_by": "system", "default_admin": True}
                )
                
                await self.create_user(admin_data)
                logger.info("Created default admin user")
                
        except Exception as e:
            logger.error(f"Error creating default admin user: {e}")
    
    async def _invalidate_user_sessions(self, user_id: str):
        """Invalidate all sessions for a user"""
        try:
            sessions_to_remove = [
                session_id for session_id, session in self.sessions.items()
                if session.user_id == user_id
            ]
            
            for session_id in sessions_to_remove:
                del self.sessions[session_id]
            
            if sessions_to_remove:
                logger.info(f"Invalidated {len(sessions_to_remove)} sessions for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error invalidating sessions for user {user_id}: {e}")
    
    async def cleanup(self):
        """Cleanup user service resources"""
        try:
            logger.info("Cleaning up User Service...")
            
            # Clean up expired sessions
            await self.cleanup_expired_sessions()
            
            self.initialized = False
            logger.info("User Service cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during user service cleanup: {e}")
            raise


# Dependency injection function
async def get_user_service() -> UserService:
    """Get user service instance"""
    service = UserService()
    if not service.initialized:
        await service.initialize()
    return service