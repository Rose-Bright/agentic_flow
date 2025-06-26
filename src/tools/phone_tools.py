"""
Phone number management tools for telecom service operations
"""

import re
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.core.logging import get_logger

logger = get_logger(__name__)


class PhoneTools:
    """Phone number management and validation tools"""
    
    @staticmethod
    async def validate_phone_number(phone_number: str) -> Dict[str, Any]:
        """Validate phone number format and structure"""
        try:
            # Clean the phone number
            clean_number = re.sub(r'[^\d+]', '', phone_number)
            
            # Remove country code if present
            if clean_number.startswith('+1'):
                clean_number = clean_number[2:]
            elif len(clean_number) == 11 and clean_number.startswith('1'):
                clean_number = clean_number[1:]
            
            # Validate US phone number (10 digits)
            is_valid = len(clean_number) == 10 and clean_number.isdigit()
            
            # Additional validation rules
            validation_errors = []
            if is_valid:
                area_code = clean_number[:3]
                exchange = clean_number[3:6]
                
                # Area code cannot start with 0 or 1
                if area_code[0] in ['0', '1']:
                    is_valid = False
                    validation_errors.append("Invalid area code")
                
                # Exchange cannot start with 0 or 1
                if exchange[0] in ['0', '1']:
                    is_valid = False
                    validation_errors.append("Invalid exchange code")
                
                # Check for reserved numbers (e.g., 911, 411)
                if clean_number in ['9110000000', '4110000000']:
                    is_valid = False
                    validation_errors.append("Reserved number")
            
            result = {
                "is_valid": is_valid,
                "original_number": phone_number,
                "cleaned_number": clean_number,
                "formatted_number": f"({clean_number[:3]}) {clean_number[3:6]}-{clean_number[6:]}" if is_valid else None,
                "validation_timestamp": datetime.now().isoformat()
            }
            
            if validation_errors:
                result["validation_errors"] = validation_errors
            
            logger.info(f"Phone number validation: {phone_number} -> {is_valid}")
            return result
            
        except Exception as e:
            logger.error(f"Error validating phone number: {e}")
            return {
                "is_valid": False,
                "error": str(e)
            }
    
    @staticmethod
    async def get_customer_phone_services(customer_id: str) -> Dict[str, Any]:
        """Get all phone services for a customer"""
        try:
            # Simulate database lookup
            # In real implementation, this would query the telecom services database
            
            mock_customer_services = {
                "CUST001": {
                    "customer_id": "CUST001",
                    "phone_numbers": ["5551234567", "5551234568"],
                    "services": [
                        {
                            "phone_number": "5551234567",
                            "service_type": "voice",
                            "status": "active",
                            "plan": "unlimited",
                            "activation_date": "2023-01-15",
                            "features": ["voicemail", "call_waiting", "caller_id"]
                        },
                        {
                            "phone_number": "5551234568", 
                            "service_type": "voice",
                            "status": "active",
                            "plan": "basic",
                            "activation_date": "2023-06-01",
                            "features": ["voicemail"]
                        }
                    ]
                },
                "CUST002": {
                    "customer_id": "CUST002",
                    "phone_numbers": ["5559876543"],
                    "services": [
                        {
                            "phone_number": "5559876543",
                            "service_type": "voice", 
                            "status": "active",
                            "plan": "premium",
                            "activation_date": "2022-11-20",
                            "features": ["voicemail", "call_waiting", "caller_id", "international"]
                        }
                    ]
                },
                "CUST003": {
                    "customer_id": "CUST003",
                    "phone_numbers": ["5555551234", "5555551235"],
                    "services": [
                        {
                            "phone_number": "5555551234",
                            "service_type": "voice",
                            "status": "active", 
                            "plan": "basic",
                            "activation_date": "2023-03-10",
                            "features": ["voicemail"]
                        },
                        {
                            "phone_number": "5555551235",
                            "service_type": "voice",
                            "status": "suspended",
                            "plan": "basic", 
                            "activation_date": "2023-08-15",
                            "features": ["voicemail"]
                        }
                    ]
                }
            }
            
            services_data = mock_customer_services.get(customer_id)
            
            if services_data:
                logger.info(f"Phone services found for customer: {customer_id}")
                return {
                    "services_found": True,
                    "phone_numbers": services_data["phone_numbers"],
                    "services": services_data["services"],
                    "total_lines": len(services_data["services"]),
                    "active_lines": len([s for s in services_data["services"] if s["status"] == "active"]),
                    "lookup_timestamp": datetime.now().isoformat()
                }
            else:
                logger.info(f"No phone services found for customer: {customer_id}")
                return {
                    "services_found": False,
                    "phone_numbers": [],
                    "services": [],
                    "total_lines": 0,
                    "active_lines": 0,
                    "lookup_timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting customer phone services: {e}")
            return {
                "services_found": False,
                "error": str(e)
            }
    
    @staticmethod
    async def check_disconnect_eligibility(customer_id: str, phone_number: str) -> Dict[str, Any]:
        """Check if a phone number is eligible for disconnection"""
        try:
            # Get customer services first
            services_result = await PhoneTools.get_customer_phone_services(customer_id)
            
            if not services_result.get("services_found", False):
                return {
                    "eligible": False,
                    "reason": "Customer services not found"
                }
            
            # Find the specific service
            target_service = None
            for service in services_result["services"]:
                if service["phone_number"] == phone_number:
                    target_service = service
                    break
            
            if not target_service:
                return {
                    "eligible": False,
                    "reason": "Phone number not found on customer account"
                }
            
            # Check eligibility rules
            eligibility_issues = []
            
            # Check if already inactive
            if target_service["status"] != "active":
                eligibility_issues.append(f"Service is already {target_service['status']}")
            
            # Check if it's the last active line (business rule)
            active_services = [s for s in services_result["services"] if s["status"] == "active"]
            if len(active_services) == 1 and target_service["status"] == "active":
                eligibility_issues.append("Cannot disconnect the last active line on account")
            
            # Check for pending billing issues (simulated)
            # In real implementation, this would check billing system
            if phone_number.endswith("68"):  # Mock condition
                eligibility_issues.append("Outstanding billing issues must be resolved first")
            
            is_eligible = len(eligibility_issues) == 0
            
            result = {
                "eligible": is_eligible,
                "phone_number": phone_number,
                "service_status": target_service["status"],
                "service_plan": target_service["plan"],
                "eligibility_timestamp": datetime.now().isoformat()
            }
            
            if eligibility_issues:
                result["reason"] = "; ".join(eligibility_issues)
            
            logger.info(f"Disconnect eligibility check: {phone_number} -> {is_eligible}")
            return result
            
        except Exception as e:
            logger.error(f"Error checking disconnect eligibility: {e}")
            return {
                "eligible": False,
                "error": str(e)
            }
    
    @staticmethod
    async def check_add_line_capacity(customer_id: str) -> Dict[str, Any]:
        """Check if customer can add additional phone lines"""
        try:
            # Get current services
            services_result = await PhoneTools.get_customer_phone_services(customer_id)
            
            if not services_result.get("services_found", False):
                return {
                    "can_add_line": False,
                    "reason": "Customer services not found"
                }
            
            current_lines = services_result["total_lines"]
            active_lines = services_result["active_lines"]
            
            # Business rules for adding lines
            capacity_issues = []
            
            # Maximum lines per customer (business rule)
            max_lines = 10
            if current_lines >= max_lines:
                capacity_issues.append(f"Maximum line limit reached ({max_lines})")
            
            # Check customer tier limits (mock implementation)
            # In real implementation, this would check customer tier rules
            customer_tier_limits = {
                "bronze": 3,
                "silver": 5, 
                "gold": 8,
                "platinum": 10
            }
            
            # For demo, assume gold tier
            tier_limit = customer_tier_limits.get("gold", 5)
            if current_lines >= tier_limit:
                capacity_issues.append(f"Customer tier limit reached ({tier_limit})")
            
            # Check account standing (simulated)
            if customer_id.endswith("003"):  # Mock condition
                capacity_issues.append("Account has outstanding issues")
            
            can_add = len(capacity_issues) == 0
            
            result = {
                "can_add_line": can_add,
                "current_lines": current_lines,
                "active_lines": active_lines,
                "max_allowed_lines": tier_limit,
                "capacity_check_timestamp": datetime.now().isoformat()
            }
            
            if capacity_issues:
                result["reason"] = "; ".join(capacity_issues)
            
            logger.info(f"Add line capacity check: customer {customer_id} -> {can_add}")
            return result
            
        except Exception as e:
            logger.error(f"Error checking add line capacity: {e}")
            return {
                "can_add_line": False,
                "error": str(e)
            }