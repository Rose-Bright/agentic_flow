"""
Sales Agent for Contact Center Agentic Flow System
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re

from src.agents.base_agent import BaseAgent
from src.models.state import AgentState, TicketStatus, CustomerTier, Priority
from src.core.logging import get_logger

logger = get_logger(__name__)


class SalesAgent(BaseAgent):
    """Agent specialized in product inquiries, quotes, and sales opportunities"""
    
    def __init__(
        self,
        name: str,
        model: str,
        capabilities: List[str],
        tools: List[str],
        confidence_threshold: float = 0.8
    ):
        super().__init__(name, model, capabilities, tools, confidence_threshold)
        
        # Product knowledge and catalog
        self.product_catalog = self._initialize_product_catalog()
        
        # Pricing tiers and strategies
        self.pricing_strategies = self._initialize_pricing_strategies()
        
        # Sales conversation flows
        self.sales_flows = self._initialize_sales_flows()
        
        # Upselling and cross-selling rules
        self.upsell_rules = self._initialize_upsell_rules()
        
        # Contract and negotiation guidelines
        self.contract_guidelines = self._initialize_contract_guidelines()
    
    async def handle_message(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Handle sales-related interactions"""
        try:
            logger.info(f"Sales agent handling inquiry for conversation {state.conversation_id}")
            
            # Analyze sales intent and opportunity
            sales_analysis = await self._analyze_sales_opportunity(message, state)
            
            # Determine sales approach
            sales_approach = await self._determine_sales_approach(message, state, sales_analysis)
            
            # Execute sales interaction
            response = await self._execute_sales_interaction(sales_approach, message, state)
            
            # Check for upselling opportunities
            upsell_opportunities = await self._identify_upsell_opportunities(state, response)
            
            # Update opportunity tracking
            await self._update_opportunity_tracking(sales_analysis, response, state)
            
            return {
                "message": response["message"],
                "confidence": response["confidence"],
                "success": response["success"],
                "resolution_attempt": True,
                "actions_taken": response["actions_taken"],
                "tools_used": response["tools_used"],
                "outcome": response["outcome"],
                "new_status": TicketStatus.RESOLVED if response["success"] else TicketStatus.IN_PROGRESS,
                "sales_approach": sales_approach,
                "opportunity_score": sales_analysis.get("opportunity_score", 0.0),
                "products_discussed": response.get("products_discussed", []),
                "quote_generated": response.get("quote_generated", False),
                "next_steps": response.get("next_steps", []),
                "follow_up_required": response.get("follow_up_required", False),
                "estimated_close_date": response.get("estimated_close_date"),
                "deal_value": response.get("deal_value", 0.0),
                "upsell_opportunities": upsell_opportunities
            }
            
        except Exception as e:
            logger.error(f"Sales agent error: {e}")
            return {
                "message": "I apologize for the technical difficulty. Let me connect you with one of our senior sales specialists who can provide you with detailed product information and pricing.",
                "confidence": 0.0,
                "success": False,
                "resolution_attempt": True,
                "actions_taken": ["error_handling"],
                "tools_used": [],
                "outcome": "agent_error",
                "requires_escalation": True,
                "error": str(e)
            }
    
    async def can_handle(self, state: AgentState) -> bool:
        """Determine if this agent can handle the current state"""
        # Sales-related intents
        sales_intents = [
            "sales_inquiry", "product_inquiry", "pricing_inquiry", "upgrade_request",
            "purchase_intent", "quote_request", "demo_request", "trial_request"
        ]
        
        # Check if intent is sales-related
        can_handle_intent = (
            state.current_intent in sales_intents or
            any(keyword in state.current_intent.lower() 
                for keyword in ["sales", "buy", "purchase", "upgrade", "pricing"])
        )
        
        # Check for sales keywords in recent conversation
        sales_keywords_present = False
        if state.conversation_history:
            recent_messages = [turn.message.lower() for turn in state.conversation_history[-3:]]
            sales_keywords = ["buy", "purchase", "price", "cost", "upgrade", "plan", "subscription"]
            sales_keywords_present = any(
                keyword in message for message in recent_messages for keyword in sales_keywords
            )
        
        # Check if customer is in exploration phase
        exploration_phase = (
            len(state.conversation_history) > 2 and
            not any(turn.intent in ["complaint", "technical_support"] 
                   for turn in state.conversation_history[-3:] if hasattr(turn, 'intent'))
        )
        
        return can_handle_intent or sales_keywords_present or exploration_phase
    
    def _get_agent_permissions(self) -> List[str]:
        """Get the permissions available to this agent"""
        return [
            "read_customer_data",
            "access_product_catalog",
            "generate_quotes",
            "process_orders",
            "check_inventory",
            "access_pricing_engine",
            "create_sales_opportunities",
            "schedule_demos",
            "apply_discounts",
            "access_contract_templates"
        ]
    
    def _initialize_product_catalog(self) -> Dict[str, Dict[str, Any]]:
        """Initialize product catalog with features and benefits"""
        return {
            "starter_plan": {
                "name": "Starter Plan",
                "category": "basic",
                "monthly_price": 29.99,
                "annual_price": 299.99,
                "features": [
                    "Up to 5 users",
                    "10GB storage",
                    "Basic support",
                    "Standard features",
                    "Email integration"
                ],
                "benefits": [
                    "Cost-effective entry point",
                    "Easy setup and migration",
                    "Scalable foundation"
                ],
                "target_customers": ["small_business", "startups", "individual"],
                "upgrade_path": "professional_plan"
            },
            "professional_plan": {
                "name": "Professional Plan",
                "category": "standard",
                "monthly_price": 79.99,
                "annual_price": 799.99,
                "features": [
                    "Up to 25 users",
                    "100GB storage",
                    "Priority support",
                    "Advanced features",
                    "API access",
                    "Custom integrations",
                    "Advanced analytics"
                ],
                "benefits": [
                    "Enhanced productivity",
                    "Better collaboration",
                    "Advanced insights",
                    "Priority assistance"
                ],
                "target_customers": ["growing_business", "professional_teams"],
                "upgrade_path": "enterprise_plan"
            },
            "enterprise_plan": {
                "name": "Enterprise Plan",
                "category": "premium",
                "monthly_price": 199.99,
                "annual_price": 1999.99,
                "features": [
                    "Unlimited users",
                    "1TB storage",
                    "24/7 dedicated support",
                    "All premium features",
                    "White-label options",
                    "Advanced security",
                    "Custom development",
                    "SLA guarantee"
                ],
                "benefits": [
                    "Maximum scalability",
                    "Enterprise-grade security",
                    "Dedicated support team",
                    "Custom solutions"
                ],
                "target_customers": ["large_enterprise", "corporations"],
                "upgrade_path": "custom_enterprise"
            },
            "add_ons": {
                "premium_support": {
                    "name": "Premium Support",
                    "monthly_price": 49.99,
                    "features": ["24/7 phone support", "1-hour response time", "Dedicated account manager"]
                },
                "additional_storage": {
                    "name": "Additional Storage",
                    "price_per_gb": 0.10,
                    "minimum": 50,
                    "features": ["Secure cloud storage", "Automatic backups", "99.9% uptime"]
                },
                "advanced_analytics": {
                    "name": "Advanced Analytics",
                    "monthly_price": 29.99,
                    "features": ["Custom dashboards", "Real-time reporting", "Data export"]
                }
            }
        }
    
    def _initialize_pricing_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize pricing strategies and discount rules"""
        return {
            "new_customer": {
                "discount_percentage": 20,
                "duration": "first_3_months",
                "conditions": ["first_time_customer", "annual_payment"],
                "promo_code": "WELCOME20"
            },
            "annual_discount": {
                "discount_percentage": 15,
                "duration": "annual_contract",
                "conditions": ["annual_payment"],
                "promo_code": "ANNUAL15"
            },
            "upgrade_incentive": {
                "discount_percentage": 25,
                "duration": "first_6_months",
                "conditions": ["existing_customer", "plan_upgrade"],
                "promo_code": "UPGRADE25"
            },
            "volume_discount": {
                "discount_tiers": [
                    {"users": 50, "discount": 10},
                    {"users": 100, "discount": 15},
                    {"users": 250, "discount": 20},
                    {"users": 500, "discount": 25}
                ],
                "conditions": ["enterprise_plan"],
                "promo_code": "VOLUME"
            },
            "competitive_match": {
                "discount_percentage": 30,
                "duration": "first_year",
                "conditions": ["competitor_reference", "manager_approval"],
                "promo_code": "MATCH30"
            }
        }
    
    def _initialize_sales_flows(self) -> Dict[str, List[str]]:
        """Initialize sales conversation flows"""
        return {
            "discovery": [
                "Understand current situation and pain points",
                "Identify business requirements and goals",
                "Assess technical requirements and constraints",
                "Determine budget range and timeline",
                "Identify decision makers and approval process"
            ],
            "presentation": [
                "Present relevant product features and benefits",
                "Demonstrate how solution addresses specific needs",
                "Share success stories and case studies",
                "Address questions and concerns",
                "Provide pricing information"
            ],
            "proposal": [
                "Generate customized quote based on requirements",
                "Include recommended configuration and add-ons",
                "Present implementation timeline",
                "Outline support and training options",
                "Schedule follow-up discussion"
            ],
            "negotiation": [
                "Review and address pricing concerns",
                "Explore alternative configurations",
                "Discuss contract terms and conditions",
                "Present available discounts and incentives",
                "Finalize agreement details"
            ],
            "closing": [
                "Confirm final requirements and pricing",
                "Process order and payment information",
                "Schedule implementation and onboarding",
                "Introduce customer success team",
                "Set expectations for next steps"
            ]
        }
    
    def _initialize_upsell_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize upselling and cross-selling rules"""
        return {
            "usage_based": {
                "conditions": [
                    "approaching_user_limit",
                    "high_storage_usage",
                    "frequent_api_calls"
                ],
                "recommendations": [
                    "upgrade_to_higher_tier",
                    "add_storage_package",
                    "increase_api_quota"
                ],
                "timing": "proactive_notification"
            },
            "feature_based": {
                "conditions": [
                    "requesting_premium_feature",
                    "asking_about_integrations",
                    "need_advanced_analytics"
                ],
                "recommendations": [
                    "upgrade_to_professional",
                    "add_integration_package",
                    "add_analytics_module"
                ],
                "timing": "during_conversation"
            },
            "success_based": {
                "conditions": [
                    "high_engagement_metrics",
                    "positive_feedback",
                    "expanding_team"
                ],
                "recommendations": [
                    "premium_support_package",
                    "additional_licenses",
                    "training_services"
                ],
                "timing": "quarterly_review"
            }
        }
    
    def _initialize_contract_guidelines(self) -> Dict[str, Dict[str, Any]]:
        """Initialize contract and negotiation guidelines"""
        return {
            "standard_terms": {
                "payment_terms": "Net 30",
                "contract_length": "12 months",
                "auto_renewal": True,
                "cancellation_notice": "30 days",
                "price_protection": "12 months"
            },
            "negotiable_terms": {
                "payment_terms": ["Net 15", "Net 45", "Net 60"],
                "contract_length": ["6 months", "24 months", "36 months"],
                "volume_discounts": "available",
                "custom_terms": "enterprise_only"
            },
            "approval_limits": {
                "sales_agent": {"discount": 10, "contract_value": 50000},
                "sales_manager": {"discount": 25, "contract_value": 250000},
                "director": {"discount": 40, "contract_value": 1000000}
            }
        }
    
    async def _analyze_sales_opportunity(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Analyze the sales opportunity and customer intent"""
        message_lower = message.lower()
        
        # Intent indicators
        intent_indicators = {
            "high_intent": [
                "want to buy", "ready to purchase", "need to upgrade", "looking to switch",
                "when can we start", "how much does it cost", "send me a quote"
            ],
            "medium_intent": [
                "interested in", "tell me more", "what are the benefits", "how does it work",
                "what plans do you have", "pricing information"
            ],
            "low_intent": [
                "just looking", "exploring options", "doing research", "comparing solutions",
                "maybe in the future", "not ready yet"
            ]
        }
        
        # Score intent level
        intent_scores = {"low": 0, "medium": 0, "high": 0}
        for level, indicators in intent_indicators.items():
            for indicator in indicators:
                if indicator in message_lower:
                    intent_scores[level] += 1
        
        # Determine intent level
        max_intent = max(intent_scores, key=intent_scores.get) if any(intent_scores.values()) else "medium"
        intent_confidence = min(intent_scores[max_intent] / 2.0, 1.0) if intent_scores[max_intent] > 0 else 0.5
        
        # Calculate opportunity score
        opportunity_score = self._calculate_opportunity_score(intent_scores, state)
        
        # Identify product interest
        product_interest = self._identify_product_interest(message_lower)
        
        return {
            "intent_level": max_intent,
            "intent_confidence": intent_confidence,
            "opportunity_score": opportunity_score,
            "product_interest": product_interest,
            "intent_indicators": intent_scores
        }
    
    def _calculate_opportunity_score(self, intent_scores: Dict[str, int], state: AgentState) -> float:
        """Calculate overall opportunity score"""
        base_score = 0.0
        
        # Intent-based scoring
        if intent_scores["high"] > 0:
            base_score += 0.4
        elif intent_scores["medium"] > 0:
            base_score += 0.2
        else:
            base_score += 0.1
        
        # Customer tier bonus
        if state.customer:
            tier_bonus = {
                CustomerTier.BRONZE: 0.1,
                CustomerTier.SILVER: 0.15,
                CustomerTier.GOLD: 0.2,
                CustomerTier.PLATINUM: 0.25
            }
            base_score += tier_bonus.get(state.customer.tier, 0.1)
        
        # Conversation engagement bonus
        if len(state.conversation_history) > 5:
            base_score += 0.1
        
        # Urgency indicators
        if any(word in str(state.conversation_history).lower() 
               for word in ["urgent", "asap", "quickly", "soon"]):
            base_score += 0.15
        
        return min(base_score, 1.0)
    
    def _identify_product_interest(self, message_lower: str) -> List[str]:
        """Identify which products the customer is interested in"""
        product_keywords = {
            "starter_plan": ["basic", "starter", "small", "simple", "entry"],
            "professional_plan": ["professional", "standard", "business", "team"],
            "enterprise_plan": ["enterprise", "advanced", "premium", "large", "corporate"],
            "add_ons": ["support", "storage", "analytics", "integration", "add-on"]
        }
        
        interested_products = []
        for product, keywords in product_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                interested_products.append(product)
        
        return interested_products if interested_products else ["professional_plan"]  # Default
    
    async def _determine_sales_approach(
        self, 
        message: str, 
        state: AgentState, 
        sales_analysis: Dict[str, Any]
    ) -> str:
        """Determine the sales approach based on analysis"""
        intent_level = sales_analysis["intent_level"]
        opportunity_score = sales_analysis["opportunity_score"]
        
        # High intent customers - move to proposal
        if intent_level == "high" or opportunity_score > 0.7:
            return "proposal"
        
        # Medium intent - discovery and presentation
        elif intent_level == "medium" or opportunity_score > 0.4:
            if len(state.conversation_history) < 3:
                return "discovery"
            else:
                return "presentation"
        
        # Low intent - discovery and education
        else:
            return "discovery"
    
    async def _execute_sales_interaction(
        self, 
        approach: str, 
        message: str, 
        state: AgentState
    ) -> Dict[str, Any]:
        """Execute the sales interaction based on approach"""
        
        if approach == "discovery":
            return await self._execute_discovery(message, state)
        elif approach == "presentation":
            return await self._execute_presentation(message, state)
        elif approach == "proposal":
            return await self._execute_proposal(message, state)
        elif approach == "negotiation":
            return await self._execute_negotiation(message, state)
        elif approach == "closing":
            return await self._execute_closing(message, state)
        else:
            return await self._execute_general_sales_support(message, state)
    
    async def _execute_discovery(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Execute discovery phase conversation"""
        tools_used = []
        
        try:
            # Get customer information to understand their context
            customer_context = {}
            if state.customer:
                try:
                    customer_data = await self.use_tool(
                        "get_customer_profile",
                        {"customer_id": state.customer.customer_id},
                        self.get_agent_context(state)
                    )
                    customer_context = customer_data
                    tools_used.append("get_customer_profile")
                except Exception as e:
                    logger.warning(f"Failed to get customer profile: {e}")
            
            # Discovery questions based on message content
            discovery_response = self._generate_discovery_response(message, customer_context)
            
            return {
                "message": discovery_response["message"],
                "confidence": 0.8,
                "success": True,
                "actions_taken": ["discovery_conversation"],
                "tools_used": tools_used,
                "outcome": "discovery_in_progress",
                "next_steps": discovery_response["next_steps"],
                "follow_up_required": True
            }
            
        except Exception as e:
            logger.error(f"Discovery execution failed: {e}")
            return {
                "message": "I'd love to learn more about your needs to recommend the best solution. Could you tell me a bit about your current situation and what you're looking to achieve?",
                "confidence": 0.6,
                "success": True,
                "actions_taken": ["discovery_fallback"],
                "tools_used": tools_used,
                "outcome": "discovery_fallback"
            }
    
    def _generate_discovery_response(self, message: str, customer_context: Dict) -> Dict[str, Any]:
        """Generate discovery phase response"""
        message_lower = message.lower()
        
        # Identify what aspect they're interested in
        if any(word in message_lower for word in ["price", "cost", "pricing"]):
            response = "I'd be happy to discuss pricing with you! To provide you with the most accurate quote, "
            response += "could you tell me a bit about your team size and main requirements? "
            response += "This will help me recommend the best plan and any potential discounts you might qualify for."
            
            next_steps = ["gather_requirements", "prepare_pricing_options"]
            
        elif any(word in message_lower for word in ["features", "capabilities", "what does"]):
            response = "Great question! Our platform offers a comprehensive set of features. "
            response += "To highlight the most relevant ones for you, could you share what specific challenges "
            response += "you're looking to solve or what your main use cases would be?"
            
            next_steps = ["identify_use_cases", "feature_demonstration"]
            
        elif any(word in message_lower for word in ["team", "users", "people"]):
            response = "Understanding your team structure is really helpful! "
            response += "How many people would be using the system, and what are their primary roles? "
            response += "This will help me recommend the right plan and features for your organization."
            
            next_steps = ["determine_user_requirements", "plan_recommendation"]
            
        else:
            # General discovery
            response = "I'm excited to help you find the perfect solution! "
            response += "To get started, could you tell me:\n"
            response += "• What's your current situation or challenge?\n"
            response += "• How many people would be using the system?\n"
            response += "• What's your timeline for making a decision?\n\n"
            response += "This will help me provide you with the most relevant information and recommendations."
            
            next_steps = ["comprehensive_discovery", "needs_analysis"]
        
        return {
            "message": response,
            "next_steps": next_steps
        }
    
    async def _execute_presentation(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Execute presentation phase conversation"""
        tools_used = []
        
        try:
            # Get product information
            product_info = await self.use_tool(
                "get_product_information",
                {
                    "products": ["professional_plan", "enterprise_plan"],
                    "include_features": True,
                    "include_benefits": True
                },
                self.get_agent_context(state)
            )
            tools_used.append("get_product_information")
            
            # Generate presentation based on customer interest
            presentation_response = self._generate_presentation_response(message, product_info, state)
            
            return {
                "message": presentation_response["message"],
                "confidence": 0.85,
                "success": True,
                "actions_taken": ["product_presentation"],
                "tools_used": tools_used,
                "outcome": "presentation_delivered",
                "products_discussed": presentation_response["products_discussed"],
                "next_steps": presentation_response["next_steps"],
                "follow_up_required": True
            }
            
        except Exception as e:
            logger.error(f"Presentation execution failed: {e}")
            return {
                "message": "Based on what you've shared, I believe our Professional Plan would be an excellent fit. It includes advanced features, priority support, and can scale with your growing needs. Would you like me to walk you through the specific features and benefits?",
                "confidence": 0.7,
                "success": True,
                "actions_taken": ["presentation_fallback"],
                "tools_used": tools_used,
                "outcome": "presentation_fallback",
                "products_discussed": ["professional_plan"]
            }
    
    def _generate_presentation_response(self, message: str, product_info: Dict, state: AgentState) -> Dict[str, Any]:
        """Generate presentation phase response"""
        message_lower = message.lower()
        
        # Determine which product to focus on based on customer tier and requirements
        if state.customer and state.customer.tier in [CustomerTier.GOLD, CustomerTier.PLATINUM]:
            recommended_product = "enterprise_plan"
        else:
            recommended_product = "professional_plan"
        
        product_details = self.product_catalog.get(recommended_product, {})
        
        response = f"Based on your requirements, I'd recommend our {product_details.get('name', 'Professional Plan')}. "
        response += "Here's why it's perfect for your needs:\n\n"
        
        # Highlight key features
        features = product_details.get("features", [])[:5]  # Top 5 features
        response += "Key Features:\n"
        for feature in features:
            response += f"• {feature}\n"
        
        response += f"\nThis plan is designed for {', '.join(product_details.get('target_customers', ['growing businesses']))} "
        response += f"and starts at ${product_details.get('monthly_price', 79.99)}/month.\n\n"
        
        # Add benefits
        benefits = product_details.get("benefits", [])
        if benefits:
            response += "Key Benefits:\n"
            for benefit in benefits[:3]:  # Top 3 benefits
                response += f"• {benefit}\n"
        
        response += "\nWould you like me to show you how this addresses your specific requirements, "
        response += "or would you prefer to see a detailed quote with pricing options?"
        
        return {
            "message": response,
            "products_discussed": [recommended_product],
            "next_steps": ["detailed_demo", "quote_generation", "address_questions"]
        }
    
    async def _execute_proposal(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Execute proposal phase conversation"""
        tools_used = []
        quote_generated = False
        deal_value = 0.0
        
        try:
            # Generate quote based on requirements
            quote_params = self._extract_quote_parameters(message, state)
            
            quote_result = await self.use_tool(
                "generate_quote",
                quote_params,
                self.get_agent_context(state)
            )
            tools_used.append("generate_quote")
            quote_generated = True
            
            if quote_result.get("success"):
                deal_value = quote_result.get("total_value", 0.0)
                
                # Check inventory availability
                inventory_check = await self.use_tool(
                    "check_inventory_availability",
                    {
                        "products": quote_params.get("products", []),
                        "quantities": quote_params.get("quantities", [])
                    },
                    self.get_agent_context(state)
                )
                tools_used.append("check_inventory_availability")
                
                # Generate proposal response
                proposal_response = self._generate_proposal_response(quote_result, inventory_check)
                
                return {
                    "message": proposal_response["message"],
                    "confidence": 0.9,
                    "success": True,
                    "actions_taken": ["quote_generated", "proposal_presented"],
                    "tools_used": tools_used,
                    "outcome": "proposal_delivered",
                    "products_discussed": quote_params.get("products", []),
                    "quote_generated": quote_generated,
                    "deal_value": deal_value,
                    "estimated_close_date": (datetime.now() + timedelta(days=14)).isoformat(),
                    "next_steps": proposal_response["next_steps"],
                    "follow_up_required": True
                }
            else:
                raise Exception("Quote generation failed")
                
        except Exception as e:
            logger.error(f"Proposal execution failed: {e}")
            return {
                "message": "I'd be happy to prepare a detailed proposal for you! Based on our conversation, I can see you're interested in a comprehensive solution. Let me prepare a customized quote that includes everything you need, along with any applicable discounts. I'll have this ready for you within 24 hours. In the meantime, do you have any specific questions about implementation or support?",
                "confidence": 0.7,
                "success": True,
                "actions_taken": ["proposal_fallback"],
                "tools_used": tools_used,
                "outcome": "proposal_promised",
                "follow_up_required": True,
                "estimated_close_date": (datetime.now() + timedelta(days=21)).isoformat()
            }
    
    def _extract_quote_parameters(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Extract parameters needed for quote generation"""
        message_lower = message.lower()
        
        # Extract user count
        user_count = 10  # Default
        user_match = re.search(r'(\d+)\s*(?:users?|people|employees)', message_lower)
        if user_match:
            user_count = int(user_match.group(1))
        elif state.customer and hasattr(state.customer, 'team_size'):
            user_count = getattr(state.customer, 'team_size', 10)
        
        # Determine plan based on user count and customer tier
        if user_count >= 100 or (state.customer and state.customer.tier == CustomerTier.PLATINUM):
            primary_product = "enterprise_plan"
        elif user_count >= 25 or (state.customer and state.customer.tier == CustomerTier.GOLD):
            primary_product = "professional_plan"
        else:
            primary_product = "starter_plan"
        
        # Check for add-ons mentioned
        add_ons = []
        if any(word in message_lower for word in ["support", "help", "assistance"]):
            add_ons.append("premium_support")
        if any(word in message_lower for word in ["storage", "space", "files"]):
            add_ons.append("additional_storage")
        if any(word in message_lower for word in ["analytics", "reports", "insights"]):
            add_ons.append("advanced_analytics")
        
        # Determine contract length
        contract_length = 12  # Default annual
        if any(word in message_lower for word in ["monthly", "month-to-month"]):
            contract_length = 1
        elif any(word in message_lower for word in ["two years", "24 months"]):
            contract_length = 24
        
        return {
            "customer_id": state.customer.customer_id if state.customer else None,
            "products": [primary_product] + add_ons,
            "quantities": [user_count] + [1] * len(add_ons),
            "contract_length": contract_length,
            "discount_eligibility": self._check_discount_eligibility(state),
            "special_requirements": self._extract_special_requirements(message_lower)
        }
    
    def _check_discount_eligibility(self, state: AgentState) -> List[str]:
        """Check which discounts the customer is eligible for"""
        eligible_discounts = []
        
        # New customer discount
        if not state.customer or not hasattr(state.customer, 'previous_purchases'):
            eligible_discounts.append("new_customer")
        
        # Existing customer upgrade discount
        elif state.customer and hasattr(state.customer, 'current_plan'):
            eligible_discounts.append("upgrade_incentive")
        
        # Annual payment discount
        eligible_discounts.append("annual_discount")
        
        # VIP customer discounts
        if state.customer and state.customer.tier in [CustomerTier.GOLD, CustomerTier.PLATINUM]:
            eligible_discounts.append("vip_customer")
        
        return eligible_discounts
    
    def _extract_special_requirements(self, message_lower: str) -> List[str]:
        """Extract any special requirements mentioned"""
        requirements = []
        
        if any(word in message_lower for word in ["integration", "api", "connect"]):
            requirements.append("custom_integrations")
        if any(word in message_lower for word in ["training", "onboarding", "setup"]):
            requirements.append("training_services")
        if any(word in message_lower for word in ["migration", "import", "transfer"]):
            requirements.append("data_migration")
        if any(word in message_lower for word in ["sla", "guarantee", "uptime"]):
            requirements.append("sla_guarantee")
        
        return requirements
    
    def _generate_proposal_response(self, quote_result: Dict, inventory_check: Dict) -> Dict[str, Any]:
        """Generate proposal response based on quote and inventory"""
        response = "I've prepared a customized proposal for you! Here's what I recommend:\n\n"
        
        # Quote summary
        if quote_result.get("line_items"):
            response += "Your Solution:\n"
            for item in quote_result["line_items"]:
                response += f"• {item.get('name', 'Product')}: ${item.get('price', 0):.2f}\n"
        
        total_value = quote_result.get("total_value", 0)
        monthly_value = quote_result.get("monthly_value", 0)
        
        response += f"\nTotal Investment: ${total_value:.2f}"
        if monthly_value > 0:
            response += f" (${monthly_value:.2f}/month)"
        
        # Discounts applied
        if quote_result.get("discounts_applied"):
            response += f"\nGreat news! I've applied the following discounts:\n"
            for discount in quote_result["discounts_applied"]:
                response += f"• {discount.get('name', 'Discount')}: {discount.get('percentage', 0)}% off\n"
            response += f"You're saving ${quote_result.get('total_savings', 0):.2f}!"
        
        # Availability
        if inventory_check.get("available", True):
            response += "\n\n✅ All items are in stock and ready for immediate deployment!"
            response += "\nWe can have you up and running within 48 hours of order confirmation."
        else:
            response += "\n\n⏳ Most items are available immediately. I'll confirm exact delivery times once we proceed."
        
        # Next steps
        response += "\n\nNext Steps:\n"
        response += "1. Review this proposal and let me know if you have any questions\n"
        response += "2. I can schedule a brief call to walk through the implementation process\n"
        response += "3. Once you're ready, we can process the order and get started!\n\n"
        response += "This proposal is valid for 30 days. Would you like to move forward, or do you have any questions?"
        
        return {
            "message": response,
            "next_steps": ["proposal_review", "implementation_planning", "order_processing"]
        }
    
    async def _execute_negotiation(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Execute negotiation phase conversation"""
        tools_used = []
        
        try:
            message_lower = message.lower()
            
            # Identify negotiation points
            negotiation_points = self._identify_negotiation_points(message_lower)
            
            # Check approval limits
            approval_needed = self._check_approval_needed(negotiation_points, state)
            
            negotiation_response = await self._generate_negotiation_response(
                negotiation_points, approval_needed, state
            )
            
            return {
                "message": negotiation_response["message"],
                "confidence": 0.8,
                "success": True,
                "actions_taken": ["negotiation_handling"],
                "tools_used": tools_used,
                "outcome": "negotiation_in_progress",
                "approval_required": approval_needed,
                "next_steps": negotiation_response["next_steps"],
                "follow_up_required": True
            }
            
        except Exception as e:
            logger.error(f"Negotiation execution failed: {e}")
            return {
                "message": "I understand you'd like to discuss the terms. Let me connect you with my sales manager who has more flexibility with pricing and contract terms. They'll be able to work with you to find a solution that fits your budget and requirements.",
                "confidence": 0.6,
                "success": True,
                "actions_taken": ["negotiation_escalation"],
                "tools_used": tools_used,
                "outcome": "escalation_required",
                "requires_escalation": True
            }
    
    def _identify_negotiation_points(self, message_lower: str) -> List[str]:
        """Identify what aspects the customer wants to negotiate"""
        negotiation_points = []
        
        if any(word in message_lower for word in ["price", "cost", "expensive", "budget", "cheaper"]):
            negotiation_points.append("pricing")
        if any(word in message_lower for word in ["contract", "term", "length", "commitment"]):
            negotiation_points.append("contract_terms")
        if any(word in message_lower for word in ["payment", "billing", "invoice", "net"]):
            negotiation_points.append("payment_terms")
        if any(word in message_lower for word in ["features", "include", "add", "remove"]):
            negotiation_points.append("feature_customization")
        if any(word in message_lower for word in ["support", "service", "sla", "guarantee"]):
            negotiation_points.append("service_terms")
        
        return negotiation_points if negotiation_points else ["general_terms"]
    
    def _check_approval_needed(self, negotiation_points: List[str], state: AgentState) -> bool:
        """Check if manager approval is needed for negotiation"""
        approval_triggers = [
            "pricing" in negotiation_points,
            "contract_terms" in negotiation_points,
            state.customer and state.customer.tier == CustomerTier.PLATINUM,
            len(negotiation_points) > 2
        ]
        
        return any(approval_triggers)
    
    async def _generate_negotiation_response(
        self, 
        negotiation_points: List[str], 
        approval_needed: bool, 
        state: AgentState
    ) -> Dict[str, Any]:
        """Generate appropriate negotiation response"""
        
        if "pricing" in negotiation_points:
            if approval_needed:
                message = "I understand pricing is important to you. Let me connect you with my sales manager "
                message += "who can discuss additional discount options and flexible pricing structures that might work better for your budget."
                next_steps = ["manager_consultation", "custom_pricing_review"]
            else:
                message = "I'd be happy to work with you on pricing! I can offer our annual payment discount "
                message += "which saves 15%, or we could look at a customized package that better fits your specific needs. "
                message += "What would work best for your budget?"
                next_steps = ["discount_application", "package_customization"]
        
        elif "contract_terms" in negotiation_points:
            message = "I understand you'd like to discuss the contract terms. We have several options available:\n"
            message += "• Shorter 6-month terms with quarterly reviews\n"
            message += "• Longer 24-month terms with additional discounts\n"
            message += "• Month-to-month with slightly higher rates\n\n"
            message += "What type of commitment works best for your planning cycle?"
            next_steps = ["contract_customization", "terms_finalization"]
        
        elif "payment_terms" in negotiation_points:
            message = "We can definitely work with you on payment terms. Our standard is Net 30, but we can offer:\n"
            message += "• Net 45 or Net 60 for larger contracts\n"
            message += "• Quarterly or annual payment schedules\n"
            message += "• Split payments for large implementations\n\n"
            message += "What payment schedule would work best for your organization?"
            next_steps = ["payment_terms_agreement", "billing_setup"]
        
        else:
            message = "I'm here to work with you to find terms that make sense for your organization. "
            message += "What specific aspects would you like to adjust? I have flexibility in several areas "
            message += "and want to make sure this works well for you."
            next_steps = ["requirements_clarification", "custom_solution_design"]
        
        return {
            "message": message,
            "next_steps": next_steps
        }
    
    async def _execute_closing(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Execute closing phase conversation"""
        tools_used = []
        
        try:
            # Process the order
            order_result = await self.use_tool(
                "process_order",
                {
                    "customer_id": state.customer.customer_id if state.customer else None,
                    "quote_id": getattr(state, 'current_quote_id', None),  
                    "payment_method": "invoice",  # Default for B2B
                    "implementation_date": (datetime.now() + timedelta(days=7)).isoformat()
                },
                self.get_agent_context(state)
            )
            tools_used.append("process_order")
            
            if order_result.get("success"):
                # Calculate customer satisfaction score
                satisfaction_result = await self.use_tool(
                    "calculate_customer_satisfaction",
                    {
                        "customer_id": state.customer.customer_id if state.customer else None,
                        "interaction_type": "sales_completion",
                        "outcome": "successful_purchase"
                    },
                    self.get_agent_context(state)
                )
                tools_used.append("calculate_customer_satisfaction")
                
                response = "Congratulations! 🎉 Your order has been successfully processed.\n\n"
                response += f"Order Details:\n"
                response += f"• Order ID: {order_result.get('order_id', 'ORD-' + str(datetime.now().timestamp())[:10])}\n"
                response += f"• Implementation Date: {order_result.get('implementation_date', 'Within 7 days')}\n"
                response += f"• Total Value: ${order_result.get('total_value', 0):.2f}\n\n"
                
                response += "What happens next:\n"
                response += "1. You'll receive a confirmation email with all order details\n"
                response += "2. Our implementation team will contact you within 24 hours\n"
                response += "3. We'll schedule your onboarding and training sessions\n"
                response += "4. Your dedicated customer success manager will be assigned\n\n"
                
                response += "Thank you for choosing us! I'm excited to see the positive impact this will have on your business. "
                response += "If you have any questions during implementation, don't hesitate to reach out."
                
                return {
                    "message": response,
                    "confidence": 1.0,
                    "success": True,
                    "actions_taken": ["order_processed", "implementation_scheduled"],
                    "tools_used": tools_used,
                    "outcome": "sale_completed",
                    "deal_value": order_result.get("total_value", 0),
                    "order_id": order_result.get("order_id"),
                    "next_steps": ["implementation_kickoff", "customer_success_handoff"],
                    "follow_up_required": False
                }
            else:
                raise Exception("Order processing failed")
                
        except Exception as e:
            logger.error(f"Closing execution failed: {e}")
            return {
                "message": "I'm having a technical issue processing your order right now. Let me get this resolved immediately - I'll connect you with our sales operations team who can complete the order processing and ensure everything is set up correctly for you.",
                "confidence": 0.5,
                "success": False,
                "actions_taken": ["order_processing_failed"],
                "tools_used": tools_used,
                "outcome": "processing_error",
                "requires_escalation": True
            }
    
    async def _execute_general_sales_support(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Execute general sales support"""
        tools_used = []
        
        try:
            # Get product information for general inquiry
            product_info = await self.use_tool(
                "get_product_information",
                {
                    "products": ["all"],
                    "include_pricing": True,
                    "include_comparisons": True
                },
                self.get_agent_context(state)
            )
            tools_used.append("get_product_information")
            
            response = "I'm here to help you find the perfect solution for your needs! "
            response += "We offer several plans designed for different business sizes and requirements:\n\n"
            
            # Brief overview of main plans
            for plan_key, plan_info in self.product_catalog.items():
                if plan_key != "add_ons":
                    response += f"• {plan_info.get('name', plan_key)}: Starting at ${plan_info.get('monthly_price', 0):.2f}/month\n"
                    response += f"  Perfect for {', '.join(plan_info.get('target_customers', ['businesses']))}\n\n"
            
            response += "I'd love to learn more about your specific needs so I can recommend the best option. "
            response += "Could you tell me:\n"
            response += "• What size is your team?\n"
            response += "• What are your main requirements?\n"
            response += "• What's your timeline for getting started?\n\n"
            response += "This will help me provide you with personalized recommendations and pricing!"
            
            return {
                "message": response,
                "confidence": 0.8,
                "success": True,
                "actions_taken": ["general_sales_inquiry"],
                "tools_used": tools_used,
                "outcome": "information_provided",
                "products_discussed": ["starter_plan", "professional_plan", "enterprise_plan"],
                "next_steps": ["requirements_gathering", "solution_recommendation"],
                "follow_up_required": True
            }
            
        except Exception as e:
            logger.error(f"General sales support failed: {e}")
            return {
                "message": "I'd love to help you explore our solutions! We have plans designed for businesses of all sizes, from startups to large enterprises. Could you tell me a bit about your team size and main requirements? This will help me recommend the perfect solution for your needs.",
                "confidence": 0.7,
                "success": True,
                "actions_taken": ["sales_support_fallback"],
                "tools_used": tools_used,
                "outcome": "general_inquiry_response"
            }
    
    async def _identify_upsell_opportunities(self, state: AgentState, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify potential upselling opportunities"""
        opportunities = []
        
        # Current product-based upsells
        current_products = response.get("products_discussed", [])
        
        for product in current_products:
            if product == "starter_plan":
                opportunities.append({
                    "type": "upgrade",
                    "recommendation": "professional_plan",
                    "reason": "Enhanced features and priority support",
                    "timing": "after_trial_period"
                })
            elif product == "professional_plan":
                opportunities.append({
                    "type": "add_on",
                    "recommendation": "premium_support",
                    "reason": "24/7 dedicated support for business-critical operations",
                    "timing": "immediate"
                })
        
        # Usage-based opportunities
        if state.customer:
            # High-value customer opportunities
            if state.customer.tier in [CustomerTier.GOLD, CustomerTier.PLATINUM]:
                opportunities.append({
                    "type": "premium_service",
                    "recommendation": "dedicated_account_manager",
                    "reason": "Personalized service for strategic accounts",
                    "timing": "immediate"
                })
            
            # Long-term customer opportunities
            if hasattr(state.customer, 'account_age') and state.customer.account_age > 365:
                opportunities.append({
                    "type": "loyalty_upgrade",
                    "recommendation": "enterprise_features",
                    "reason": "Exclusive features for loyal customers",
                    "timing": "renewal_period"
                })
        
        return opportunities
    
    async def _update_opportunity_tracking(
        self, 
        sales_analysis: Dict[str, Any], 
        response: Dict[str, Any], 
        state: AgentState
    ):
        """Update opportunity tracking in CRM"""
        try:
            opportunity_data = {
                "conversation_id": state.conversation_id,
                "customer_id": state.customer.customer_id if state.customer else None,
                "opportunity_score": sales_analysis.get("opportunity_score", 0.0),
                "intent_level": sales_analysis.get("intent_level", "low"),
                "products_discussed": response.get("products_discussed", []),
                "deal_value": response.get("deal_value", 0.0),
                "stage": response.get("outcome", "discovery"),
                "next_follow_up": (datetime.now() + timedelta(days=3)).isoformat() if response.get("follow_up_required") else None,
                "confidence": response.get("confidence", 0.0)
            }
            
            # This would typically update a CRM system
            logger.info(f"Opportunity tracking updated: {opportunity_data}")
            
        except Exception as e:
            logger.warning(f"Failed to update opportunity tracking: {e}")