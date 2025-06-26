"""
Customer profile and interaction management tools
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.core.logging import get_logger

logger = get_logger(__name__)


class CustomerTools:
    """Customer profile and interaction management tools"""
    
    @staticmethod
    async def get_customer_profile(customer_id: str) -> Dict[str, Any]:
        """Get comprehensive customer profile information"""
        try:
            # Simulate customer profile lookup
            mock_profiles = {
                "CUST001": {
                    "customer_id": "CUST001",
                    "name": "John Doe",
                    "email": "john.doe@email.com",
                    "phone": "5551234567",
                    "tier": "gold",
                    "account_status": "active",
                    "registration_date": "2023-01-15T00:00:00",
                    "lifetime_value": 2500.00,
                    "billing_address": {
                        "street": "123 Main St",
                        "city": "Anytown", 
                        "state": "CA",
                        "zip": "12345"
                    },
                    "payment_method": "auto_pay",
                    "preferences": {
                        "communication_channel": "email",
                        "language": "english",
                        "notifications": True
                    },
                    "satisfaction_scores": [4.5, 4.2, 4.8, 4.6],
                    "account_notes": "Preferred customer, quick response required"
                },
                "CUST002": {
                    "customer_id": "CUST002",
                    "name": "Jane Smith",
                    "email": "jane.smith@email.com", 
                    "phone": "5559876543",
                    "tier": "platinum",
                    "account_status": "active",
                    "registration_date": "2022-11-20T00:00:00",
                    "lifetime_value": 5000.00,
                    "billing_address": {
                        "street": "456 Oak Ave",
                        "city": "Springfield",
                        "state": "NY", 
                        "zip": "67890"
                    },
                    "payment_method": "credit_card",
                    "preferences": {
                        "communication_channel": "phone",
                        "language": "english",
                        "notifications": True
                    },
                    "satisfaction_scores": [4.9, 4.8, 5.0, 4.7], 
                    "account_notes": "VIP customer, escalate immediately if needed"
                },
                "CUST003": {
                    "customer_id": "CUST003",
                    "name": "Test Customer",
                    "email": "test@telecom.com",
                    "phone": "5555551234", 
                    "tier": "silver",
                    "account_status": "active",
                    "registration_date": "2023-03-10T00:00:00",
                    "lifetime_value": 1200.00,
                    "billing_address": {
                        "street": "789 Pine St",
                        "city": "Testville",
                        "state": "TX",
                        "zip": "54321"
                    },
                    "payment_method": "bank_transfer",
                    "preferences": {
                        "communication_channel": "email",
                        "language": "english", 
                        "notifications": False
                    },
                    "satisfaction_scores": [4.0, 3.8, 4.2, 4.1],
                    "account_notes": "Test account for system validation"
                }
            }
            
            profile_data = mock_profiles.get(customer_id)
            
            if profile_data:
                logger.info(f"Customer profile retrieved: {customer_id}")
                return {
                    "profile_found": True,
                    "customer_data": profile_data,
                    "lookup_timestamp": datetime.now().isoformat()
                }
            else:
                logger.info(f"Customer profile not found: {customer_id}")
                return {
                    "profile_found": False,
                    "lookup_timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting customer profile: {e}")
            return {
                "profile_found": False,
                "error": str(e)
            }
    
    @staticmethod
    async def update_customer_notes(
        customer_id: str,
        notes: str,
        note_type: str = "service_interaction"
    ) -> Dict[str, Any]:
        """Add notes to customer profile"""
        try:
            note_entry = {
                "note_id": f"NOTE_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "customer_id": customer_id,
                "note_type": note_type,
                "notes": notes,
                "created_at": datetime.now().isoformat(),
                "created_by": "TelecomServiceAgent"
            }
            
            # Simulate adding note to customer profile
            await asyncio.sleep(0.05)
            
            logger.info(f"Customer notes updated: {customer_id}")
            
            return {
                "notes_updated": True,
                "note_entry": note_entry
            }
            
        except Exception as e:
            logger.error(f"Error updating customer notes: {e}")
            return {
                "notes_updated": False,
                "error": str(e)
            }
    
    @staticmethod
    async def log_customer_interaction(
        customer_id: str,
        interaction_type: str,
        channel: str = "email",
        **kwargs
    ) -> Dict[str, Any]:
        """Log customer interaction for analytics and tracking"""
        try:
            interaction_data = {
                "interaction_id": f"INT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{customer_id}",
                "customer_id": customer_id,
                "interaction_type": interaction_type,
                "channel": channel,
                "timestamp": datetime.now().isoformat(),
                "agent_type": "TelecomServiceAgent",
                "outcome": "processed",
                "additional_data": kwargs
            }
            
            # Add specific tracking for phone service requests
            if interaction_type.startswith("phone_"):
                interaction_data["service_category"] = "phone_management"
                if "phone_number" in kwargs:
                    interaction_data["affected_number"] = kwargs["phone_number"]
            
            # Simulate logging to analytics system
            await asyncio.sleep(0.05)
            
            logger.info(f"Customer interaction logged: {customer_id} - {interaction_type}")
            
            return {
                "interaction_logged": True,
                "interaction_data": interaction_data
            }
            
        except Exception as e:
            logger.error(f"Error logging customer interaction: {e}")
            return {
                "interaction_logged": False,
                "error": str(e)
            }
    
    @staticmethod
    async def get_customer_interaction_history(
        customer_id: str,
        days: int = 30,
        interaction_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get customer interaction history"""
        try:
            # Simulate interaction history lookup
            mock_interactions = {
                "CUST001": [
                    {
                        "interaction_id": "INT_20240101_120000_CUST001",
                        "interaction_type": "phone_disconnect_request",
                        "channel": "email",
                        "timestamp": "2024-01-01T12:00:00",
                        "outcome": "processed",
                        "phone_number": "5551234568"
                    },
                    {
                        "interaction_id": "INT_20231215_140000_CUST001", 
                        "interaction_type": "billing_inquiry",
                        "channel": "phone",
                        "timestamp": "2023-12-15T14:00:00",
                        "outcome": "resolved"
                    }
                ],
                "CUST002": [
                    {
                        "interaction_id": "INT_20231220_100000_CUST002",
                        "interaction_type": "service_upgrade",
                        "channel": "online",
                        "timestamp": "2023-12-20T10:00:00", 
                        "outcome": "completed"
                    }
                ],
                "CUST003": [
                    {
                        "interaction_id": "INT_20240105_090000_CUST003",
                        "interaction_type": "phone_add_request",
                        "channel": "email",
                        "timestamp": "2024-01-05T09:00:00",
                        "outcome": "processed",
                        "phone_number": "5555551235"
                    }
                ]
            }
            
            interactions = mock_interactions.get(customer_id, [])
            
            # Filter by interaction type if specified
            if interaction_type:
                interactions = [i for i in interactions if i["interaction_type"] == interaction_type]
            
            # Filter by date range (simplified - would use actual date filtering in real implementation)
            # For demo, return all interactions
            
            logger.info(f"Interaction history retrieved: {customer_id}")
            
            return {
                "history_found": True,
                "customer_id": customer_id,
                "interactions": interactions,
                "total_interactions": len(interactions),
                "date_range_days": days,
                "lookup_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting customer interaction history: {e}")
            return {
                "history_found": False,
                "error": str(e)
            }