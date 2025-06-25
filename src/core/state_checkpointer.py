"""
Enhanced state checkpointing system for LangGraph integration
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import asdict
import pickle

from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata
from src.models.state import AgentState, TicketStatus
from src.cache.redis_client import RedisClient
from src.database.connection import get_database
from src.core.config import get_settings
from src.core.logging import get_logger
logger = get_logger(__name__)


class EnhancedCheckpointSaver(BaseCheckpointSaver):
    """Enhanced checkpoint saver with Redis and PostgreSQL persistence"""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_client = None
        self.db = None
        self.in_memory_cache = {}
        self.checkpoint_ttl = 7 * 24 * 3600  # 7 days in seconds
        
    async def initialize(self):
        """Initialize Redis and database connections"""
        try:
            self.redis_client = RedisClient()
            await self.redis_client.initialize()
            
            self.db = await get_database()
            
            logger.info("Enhanced checkpoint saver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize checkpoint saver: {e}")
            raise
    
    async def aget(
        self, 
        config: Dict[str, Any], 
        **kwargs
    ) -> Optional[Checkpoint]:
        """Retrieve checkpoint from storage"""
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return None
            
        try:
            # Try in-memory cache first
            cache_key = f"checkpoint_{thread_id}"
            if cache_key in self.in_memory_cache:
                cached_data = self.in_memory_cache[cache_key]
                if datetime.now() - cached_data["timestamp"] < timedelta(minutes=5):
                    logger.debug(f"Retrieved checkpoint from memory cache: {thread_id}")
                    return cached_data["checkpoint"]
            
            # Try Redis cache
            if self.redis_client:
                redis_key = f"checkpoint:{thread_id}"
                checkpoint_data = await self.redis_client.get(redis_key)
                if checkpoint_data:
                    checkpoint = self._deserialize_checkpoint(checkpoint_data)
                    # Update in-memory cache
                    self.in_memory_cache[cache_key] = {
                        "checkpoint": checkpoint,
                        "timestamp": datetime.now()
                    }
                    logger.debug(f"Retrieved checkpoint from Redis: {thread_id}")
                    return checkpoint
            
            # Try database persistence
            if self.db:
                checkpoint = await self._get_checkpoint_from_db(thread_id)
                if checkpoint:
                    # Update caches
                    await self._update_caches(thread_id, checkpoint)
                    logger.debug(f"Retrieved checkpoint from database: {thread_id}")
                    return checkpoint
            
            logger.debug(f"No checkpoint found for thread: {thread_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve checkpoint for {thread_id}: {e}")
            return None
    
    async def aput(
        self,
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        **kwargs
    ) -> None:
        """Store checkpoint to all storage layers"""
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            logger.warning("No thread_id provided for checkpoint storage")
            return
        
        try:
            # Store in in-memory cache
            cache_key = f"checkpoint_{thread_id}"
            self.in_memory_cache[cache_key] = {
                "checkpoint": checkpoint,
                "timestamp": datetime.now()
            }
            
            # Store in Redis
            if self.redis_client:
                redis_key = f"checkpoint:{thread_id}"
                checkpoint_data = self._serialize_checkpoint(checkpoint)
                await self.redis_client.setex(
                    redis_key, 
                    self.checkpoint_ttl, 
                    checkpoint_data
                )
            
            # Store in database (async for better performance)
            if self.db:
                asyncio.create_task(
                    self._store_checkpoint_in_db(thread_id, checkpoint, metadata)
                )
            
            logger.debug(f"Checkpoint stored for thread: {thread_id}")
            
        except Exception as e:
            logger.error(f"Failed to store checkpoint for {thread_id}: {e}")
    
    async def alist(
        self,
        config: Dict[str, Any],
        limit: Optional[int] = 10,
        **kwargs
    ) -> List[CheckpointMetadata]:
        """List checkpoints for a configuration"""
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return []
        
        try:
            if self.db:
                return await self._list_checkpoints_from_db(thread_id, limit)
            else:
                return []
                
        except Exception as e:
            logger.error(f"Failed to list checkpoints for {thread_id}: {e}")
            return []
    
    async def aput_writes(
        self,
        config: Dict[str, Any],
        writes: List[Any],
        task_id: str,
        **kwargs
    ) -> None:
        """Store write operations"""
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return
        
        try:
            # Store writes in Redis for quick access
            if self.redis_client:
                writes_key = f"writes:{thread_id}:{task_id}"
                writes_data = json.dumps(writes, default=str)
                await self.redis_client.setex(writes_key, 3600, writes_data)  # 1 hour TTL
            
            logger.debug(f"Writes stored for thread {thread_id}, task {task_id}")
            
        except Exception as e:
            logger.error(f"Failed to store writes for {thread_id}: {e}")
    
    def _serialize_checkpoint(self, checkpoint: Checkpoint) -> str:
        """Serialize checkpoint for storage"""
        try:
            # Convert checkpoint to JSON-serializable format
            checkpoint_dict = {
                "values": self._serialize_agent_state(checkpoint.values),
                "next": checkpoint.next,
                "config": checkpoint.config,
                "metadata": checkpoint.metadata,
                "parent_config": checkpoint.parent_config
            }
            
            return json.dumps(checkpoint_dict, default=str)
            
        except Exception as e:
            logger.error(f"Failed to serialize checkpoint: {e}")
            # Fallback to pickle
            return pickle.dumps(checkpoint).decode('latin-1')
    
    def _deserialize_checkpoint(self, checkpoint_data: str) -> Checkpoint:
        """Deserialize checkpoint from storage"""
        try:
            # Try JSON first
            checkpoint_dict = json.loads(checkpoint_data)
            
            return Checkpoint(
                values=self._deserialize_agent_state(checkpoint_dict["values"]),
                next=checkpoint_dict.get("next"),
                config=checkpoint_dict.get("config"),
                metadata=checkpoint_dict.get("metadata"),
                parent_config=checkpoint_dict.get("parent_config")
            )
            
        except json.JSONDecodeError:
            # Fallback to pickle
            return pickle.loads(checkpoint_data.encode('latin-1'))
    
    def _serialize_agent_state(self, state: AgentState) -> Dict[str, Any]:
        """Serialize AgentState to JSON-compatible format"""
        try:
            if hasattr(state, 'dict'):
                return state.dict()
            else:
                return asdict(state)
                
        except Exception as e:
            logger.error(f"Failed to serialize agent state: {e}")
            return {}
    
    def _deserialize_agent_state(self, state_dict: Dict[str, Any]) -> AgentState:
        """Deserialize AgentState from JSON format"""
        try:
            # Convert datetime strings back to datetime objects
            if "session_start" in state_dict and isinstance(state_dict["session_start"], str):
                state_dict["session_start"] = datetime.fromisoformat(state_dict["session_start"])
            
            if "last_activity" in state_dict and isinstance(state_dict["last_activity"], str):
                state_dict["last_activity"] = datetime.fromisoformat(state_dict["last_activity"])
            
            # Convert conversation history timestamps
            if "conversation_history" in state_dict:
                for turn in state_dict["conversation_history"]:
                    if "timestamp" in turn and isinstance(turn["timestamp"], str):
                        turn["timestamp"] = datetime.fromisoformat(turn["timestamp"])
            
            # Convert resolution attempts timestamps
            if "resolution_attempts" in state_dict:
                for attempt in state_dict["resolution_attempts"]:
                    if "timestamp" in attempt and isinstance(attempt["timestamp"], str):
                        attempt["timestamp"] = datetime.fromisoformat(attempt["timestamp"])
            
            # Convert escalation history timestamps
            if "escalation_history" in state_dict:
                for escalation in state_dict["escalation_history"]:
                    if "timestamp" in escalation and isinstance(escalation["timestamp"], str):
                        escalation["timestamp"] = datetime.fromisoformat(escalation["timestamp"])
            
            return AgentState(**state_dict)
            
        except Exception as e:
            logger.error(f"Failed to deserialize agent state: {e}")
            return AgentState(session_id="", conversation_id="")
    
    async def _get_checkpoint_from_db(self, thread_id: str) -> Optional[Checkpoint]:
        """Retrieve checkpoint from database"""
        try:
            query = """
            SELECT checkpoint_data, metadata, created_at
            FROM conversation_checkpoints
            WHERE thread_id = $1
            ORDER BY created_at DESC
            LIMIT 1
            """
            
            async with self.db.acquire() as conn:
                row = await conn.fetchrow(query, thread_id)
                
                if row:
                    checkpoint_data = row["checkpoint_data"]
                    return self._deserialize_checkpoint(checkpoint_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get checkpoint from database: {e}")
            return None
    
    async def _store_checkpoint_in_db(
        self, 
        thread_id: str, 
        checkpoint: Checkpoint, 
        metadata: CheckpointMetadata
    ):
        """Store checkpoint in database"""
        try:
            checkpoint_data = self._serialize_checkpoint(checkpoint)
            
            query = """
            INSERT INTO conversation_checkpoints (
                thread_id, checkpoint_data, metadata, created_at
            ) VALUES ($1, $2, $3, $4)
            ON CONFLICT (thread_id) DO UPDATE SET
                checkpoint_data = EXCLUDED.checkpoint_data,
                metadata = EXCLUDED.metadata,
                created_at = EXCLUDED.created_at
            """
            
            async with self.db.acquire() as conn:
                await conn.execute(
                    query,
                    thread_id,
                    checkpoint_data,
                    json.dumps(metadata, default=str),
                    datetime.now()
                )
            
            logger.debug(f"Checkpoint stored in database for thread: {thread_id}")
            
        except Exception as e:
            logger.error(f"Failed to store checkpoint in database: {e}")
    
    async def _list_checkpoints_from_db(
        self, 
        thread_id: str, 
        limit: int
    ) -> List[CheckpointMetadata]:
        """List checkpoints from database"""
        try:
            query = """
            SELECT metadata, created_at
            FROM conversation_checkpoints
            WHERE thread_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """
            
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, thread_id, limit)
                
                checkpoints = []
                for row in rows:
                    metadata = json.loads(row["metadata"])
                    checkpoints.append(CheckpointMetadata(**metadata))
                
                return checkpoints
            
        except Exception as e:
            logger.error(f"Failed to list checkpoints from database: {e}")
            return []
    
    async def _update_caches(self, thread_id: str, checkpoint: Checkpoint):
        """Update both in-memory and Redis caches"""
        try:
            # Update in-memory cache
            cache_key = f"checkpoint_{thread_id}"
            self.in_memory_cache[cache_key] = {
                "checkpoint": checkpoint,
                "timestamp": datetime.now()
            }
            
            # Update Redis cache
            if self.redis_client:
                redis_key = f"checkpoint:{thread_id}"
                checkpoint_data = self._serialize_checkpoint(checkpoint)
                await self.redis_client.setex(
                    redis_key, 
                    self.checkpoint_ttl, 
                    checkpoint_data
                )
            
        except Exception as e:
            logger.error(f"Failed to update caches for {thread_id}: {e}")
    
    async def cleanup_old_checkpoints(self, older_than_days: int = 30):
        """Clean up old checkpoints from all storage layers"""
        try:
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
            
            # Cleanup database
            if self.db:
                query = """
                DELETE FROM conversation_checkpoints
                WHERE created_at < $1
                """
                
                async with self.db.acquire() as conn:
                    result = await conn.execute(query, cutoff_date)
                    logger.info(f"Cleaned up old checkpoints from database: {result}")
            
            # Cleanup in-memory cache (older than 1 hour)
            cache_cutoff = datetime.now() - timedelta(hours=1)
            keys_to_remove = [
                key for key, value in self.in_memory_cache.items()
                if value["timestamp"] < cache_cutoff
            ]
            
            for key in keys_to_remove:
                del self.in_memory_cache[key]
            
            if keys_to_remove:
                logger.info(f"Cleaned up {len(keys_to_remove)} entries from memory cache")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old checkpoints: {e}")
    
    async def get_conversation_state(self, conversation_id: str) -> Optional[AgentState]:
        """Get current conversation state"""
        config = {"configurable": {"thread_id": conversation_id}}
        checkpoint = await self.aget(config)
        
        if checkpoint and checkpoint.values:
            return checkpoint.values
        
        return None
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.redis_client:
                await self.redis_client.close()
            
            # Clear in-memory cache
            self.in_memory_cache.clear()
            
            logger.info("Checkpoint saver cleanup completed")
            
        except Exception as e:
            logger.error(f"Failed to cleanup checkpoint saver: {e}")


class ConversationStateManager:
    """High-level state management for conversations"""
    
    def __init__(self):
        self.checkpointer = EnhancedCheckpointSaver()
        self.active_conversations = {}
        
    async def initialize(self):
        """Initialize the state manager"""
        await self.checkpointer.initialize()
        
        # Start cleanup task
        asyncio.create_task(self._periodic_cleanup())
        
        logger.info("Conversation state manager initialized")
    
    async def get_or_create_state(self, conversation_id: str) -> AgentState:
        """Get existing conversation state or create new one"""
        try:
            # Check active conversations first
            if conversation_id in self.active_conversations:
                return self.active_conversations[conversation_id]
            
            # Try to retrieve from checkpointer
            state = await self.checkpointer.get_conversation_state(conversation_id)
            
            if state:
                # Reactivate conversation
                self.active_conversations[conversation_id] = state
                logger.info(f"Reactivated conversation state: {conversation_id}")
                return state
            
            # Create new conversation state
            new_state = AgentState(
                session_id=f"session_{conversation_id}",
                conversation_id=conversation_id,
                session_start=datetime.now(),
                last_activity=datetime.now()
            )
            
            self.active_conversations[conversation_id] = new_state
            logger.info(f"Created new conversation state: {conversation_id}")
            
            return new_state
            
        except Exception as e:
            logger.error(f"Failed to get or create state for {conversation_id}: {e}")
            # Return minimal state as fallback
            return AgentState(
                session_id=f"session_{conversation_id}",
                conversation_id=conversation_id
            )
    
    async def update_state(self, conversation_id: str, state: AgentState):
        """Update conversation state"""
        try:
            # Update active conversation
            self.active_conversations[conversation_id] = state
            state.last_activity = datetime.now()
            
            # Store checkpoint (async)
            config = {"configurable": {"thread_id": conversation_id}}
            checkpoint = Checkpoint(
                values=state,
                next=None,
                config=config,
                metadata=CheckpointMetadata(
                    source="conversation_update",
                    step=len(state.conversation_history),
                    writes={}
                ),
                parent_config=None
            )
            
            await self.checkpointer.aput(config, checkpoint, checkpoint.metadata)
            
            logger.debug(f"Updated state for conversation: {conversation_id}")
            
        except Exception as e:
            logger.error(f"Failed to update state for {conversation_id}: {e}")
    
    async def close_conversation(self, conversation_id: str):
        """Close conversation and cleanup resources"""
        try:
            if conversation_id in self.active_conversations:
                state = self.active_conversations[conversation_id]
                state.status = TicketStatus.CLOSED
                
                # Final checkpoint
                await self.update_state(conversation_id, state)
                
                # Remove from active conversations
                del self.active_conversations[conversation_id]
                
                logger.info(f"Closed conversation: {conversation_id}")
            
        except Exception as e:
            logger.error(f"Failed to close conversation {conversation_id}: {e}")
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of inactive conversations"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                cutoff_time = datetime.now() - timedelta(hours=2)
                inactive_conversations = [
                    conv_id for conv_id, state in self.active_conversations.items()
                    if state.last_activity < cutoff_time
                ]
                
                for conv_id in inactive_conversations:
                    await self.close_conversation(conv_id)
                
                # Cleanup old checkpoints
                await self.checkpointer.cleanup_old_checkpoints()
                
                if inactive_conversations:
                    logger.info(f"Cleaned up {len(inactive_conversations)} inactive conversations")
                
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    async def cleanup(self):
        """Cleanup state manager resources"""
        try:
            # Close all active conversations
            for conv_id in list(self.active_conversations.keys()):
                await self.close_conversation(conv_id)
            
            # Cleanup checkpointer
            await self.checkpointer.cleanup()
            
            logger.info("Conversation state manager cleanup completed")
            
        except Exception as e:
            logger.error(f"Failed to cleanup state manager: {e}")