"""
Intent Classification Agent for Contact Center Agentic Flow System
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import re

from src.agents.base_agent import BaseAgent
from src.models.state import AgentState, Sentiment
from src.core.logging import get_logger

logger = get_logger(__name__)


class IntentClassificationAgent(BaseAgent):
    """Agent specialized in intent classification and sentiment analysis"""
    
    def __init__(
        self,
        name: str,
        model: str,
        capabilities: List[str],
        tools: List[str],
        confidence_threshold: float = 0.85
    ):
        super().__init__(name, model, capabilities, tools, confidence_threshold)
        
        # Intent classification patterns
        self.intent_patterns = self._initialize_intent_patterns()
        
        # Sentiment analysis keywords
        self.sentiment_keywords = self._initialize_sentiment_keywords()
        
        # Language detection patterns
        self.language_patterns = self._initialize_language_patterns()
    
    async def handle_message(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Handle intent classification for incoming message"""
        try:
            logger.info(f"Classifying intent for message: {message[:50]}...")
            
            # Clean and preprocess message
            cleaned_message = self._preprocess_message(message)
            
            # Classify intent
            intent_result = await self._classify_intent(cleaned_message, state)
            
            # Analyze sentiment
            sentiment_result = await self._analyze_sentiment(cleaned_message, state)
            
            # Detect language
            language = await self._detect_language(cleaned_message)
            
            # Assess urgency
            urgency_level = await self._assess_urgency(cleaned_message, state)
            
            # Determine confidence
            overall_confidence = min(intent_result["confidence"], sentiment_result["confidence"])
            
            # Log classification metrics
            await self._log_classification_metrics(
                intent_result, sentiment_result, language, urgency_level
            )
            
            return {
                "intent": intent_result["intent"],
                "confidence": overall_confidence,
                "sentiment": sentiment_result["sentiment"],
                "sentiment_score": sentiment_result["score"],
                "language": language,
                "urgency_level": urgency_level,
                "classification_details": {
                    "intent_confidence": intent_result["confidence"],
                    "sentiment_confidence": sentiment_result["confidence"],
                    "intent_categories": intent_result.get("categories", []),
                    "keywords_detected": intent_result.get("keywords", [])
                },
                "message": f"Classified as {intent_result['intent']} with {overall_confidence:.2f} confidence",
                "success": True,
                "tools_used": ["intent_classifier", "sentiment_analyzer"],
                "actions_taken": ["intent_classification", "sentiment_analysis", "language_detection"]
            }
            
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "sentiment": Sentiment.NEUTRAL,
                "sentiment_score": 0.0,
                "language": "en",
                "urgency_level": "medium",
                "message": "Unable to classify intent due to processing error",
                "success": False,
                "error": str(e)
            }
    
    async def can_handle(self, state: AgentState) -> bool:
        """Determine if this agent can handle the current state"""
        # Intent classification agent can handle any message that needs classification
        return True
    
    def _get_agent_permissions(self) -> List[str]:
        """Get the permissions available to this agent"""
        return [
            "read_customer_data",
            "read_knowledge_base", 
            "write_analytics",
            "classify_intent",
            "analyze_sentiment"
        ]
    
    def _initialize_intent_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize intent classification patterns"""
        return {
            "account_access": {
                "keywords": [
                    "login", "log in", "sign in", "access", "password", "username",
                    "account", "locked", "forgot password", "reset password",
                    "can't access", "cannot login", "unable to login"
                ],
                "patterns": [
                    r"can[\'t\s]*log\s*in",
                    r"forgot\s+my\s+password",
                    r"account\s+locked",
                    r"reset\s+password",
                    r"can[\'t\s]*access\s+my\s+account"
                ],
                "confidence_boost": 0.2
            },
            "technical_support": {
                "keywords": [
                    "not working", "broken", "error", "issue", "problem", "bug",
                    "slow", "loading", "connection", "network", "down", "outage",
                    "technical", "help", "support", "fix", "repair"
                ],
                "patterns": [
                    r"not\s+working",
                    r"getting\s+an?\s+error",
                    r"technical\s+(issue|problem)",
                    r"something\s+is\s+(wrong|broken)",
                    r"need\s+help\s+with"
                ],
                "confidence_boost": 0.1
            },
            "billing_inquiry": {
                "keywords": [
                    "bill", "billing", "charge", "payment", "invoice", "cost",
                    "price", "fee", "refund", "money", "paid", "pay", "owe",
                    "balance", "account balance", "statement"
                ],
                "patterns": [
                    r"billing\s+(question|issue|problem)",
                    r"charged\s+(me|wrong)",
                    r"refund",
                    r"payment\s+(issue|problem)",
                    r"how\s+much.*cost"
                ],
                "confidence_boost": 0.15
            },
            "sales_inquiry": {
                "keywords": [
                    "buy", "purchase", "upgrade", "plan", "pricing", "features",
                    "product", "service", "subscription", "package", "offer",
                    "deal", "discount", "trial", "demo"
                ],
                "patterns": [
                    r"want\s+to\s+buy",
                    r"upgrade\s+my\s+plan",
                    r"what.*cost",
                    r"pricing\s+information",
                    r"interested\s+in"
                ],
                "confidence_boost": 0.1
            },
            "complaint": {
                "keywords": [
                    "complaint", "complain", "unhappy", "dissatisfied", "angry",
                    "frustrated", "terrible", "awful", "worst", "horrible",
                    "disappointed", "unacceptable", "poor service"
                ],
                "patterns": [
                    r"want\s+to\s+complain",
                    r"very\s+(unhappy|disappointed)",
                    r"terrible\s+service",
                    r"worst.*experience",
                    r"completely\s+unacceptable"
                ],
                "confidence_boost": 0.3
            },
            "cancellation": {
                "keywords": [
                    "cancel", "cancellation", "close account", "terminate",
                    "end service", "stop", "quit", "leave", "unsubscribe"
                ],
                "patterns": [
                    r"want\s+to\s+cancel",
                    r"close\s+my\s+account",
                    r"terminate\s+service",
                    r"stop\s+my\s+subscription",
                    r"no\s+longer\s+need"
                ],
                "confidence_boost": 0.25
            },
            "general_inquiry": {
                "keywords": [
                    "question", "help", "information", "how to", "how do",
                    "what is", "where", "when", "who", "why", "explain"
                ],
                "patterns": [
                    r"have\s+a\s+question",
                    r"need\s+help",
                    r"how\s+(do|to)",
                    r"what\s+is",
                    r"can\s+you\s+explain"
                ],
                "confidence_boost": 0.05
            }
        }
    
    def _initialize_sentiment_keywords(self) -> Dict[str, List[str]]:
        """Initialize sentiment analysis keywords"""
        return {
            "positive": [
                "great", "excellent", "amazing", "wonderful", "fantastic",
                "love", "perfect", "awesome", "brilliant", "outstanding",
                "satisfied", "happy", "pleased", "thank you", "thanks"
            ],
            "negative": [
                "terrible", "awful", "horrible", "worst", "hate", "angry",
                "frustrated", "disappointed", "unacceptable", "poor",
                "bad", "wrong", "broken", "useless", "annoying"
            ],
            "frustrated": [
                "frustrated", "annoyed", "irritated", "fed up", "sick of",
                "enough", "ridiculous", "absurd", "crazy", "stupid",
                "waste of time", "joke", "pathetic"
            ]
        }
    
    def _initialize_language_patterns(self) -> Dict[str, List[str]]:
        """Initialize language detection patterns"""
        return {
            "es": ["hola", "gracias", "por favor", "ayuda", "problema", "no funciona"],
            "fr": ["bonjour", "merci", "s'il vous plaît", "aide", "problème", "ne fonctionne pas"],
            "de": ["hallo", "danke", "bitte", "hilfe", "problem", "funktioniert nicht"],
            "it": ["ciao", "grazie", "per favore", "aiuto", "problema", "non funziona"],
            "pt": ["olá", "obrigado", "por favor", "ajuda", "problema", "não funciona"]
        }
    
    def _preprocess_message(self, message: str) -> str:
        """Clean and preprocess the message"""
        # Convert to lowercase
        cleaned = message.lower().strip()
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Remove special characters except basic punctuation
        cleaned = re.sub(r'[^\w\s\.\!\?\,\-\']', '', cleaned)
        
        return cleaned
    
    async def _classify_intent(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Classify the intent of the message"""
        intent_scores = {}
        detected_keywords = []
        
        # Score each intent category
        for intent, config in self.intent_patterns.items():
            score = 0.0
            intent_keywords = []
            
            # Check keywords
            for keyword in config["keywords"]:
                if keyword in message:
                    score += 1.0
                    intent_keywords.append(keyword)
            
            # Check patterns
            for pattern in config["patterns"]:
                if re.search(pattern, message, re.IGNORECASE):
                    score += config["confidence_boost"]
                    intent_keywords.append(f"pattern:{pattern}")
            
            # Normalize score
            max_possible_score = len(config["keywords"]) + len(config["patterns"]) * config["confidence_boost"]
            if max_possible_score > 0:
                normalized_score = min(score / max_possible_score, 1.0)
            else:
                normalized_score = 0.0
            
            intent_scores[intent] = normalized_score
            if intent_keywords:
                detected_keywords.extend(intent_keywords)
        
        # Get best intent
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[best_intent]
        else:
            best_intent = "general_inquiry"
            confidence = 0.5
        
        # Apply context-based adjustments
        confidence = await self._apply_context_adjustments(
            best_intent, confidence, message, state
        )
        
        return {
            "intent": best_intent,
            "confidence": confidence,
            "categories": intent_scores,
            "keywords": detected_keywords
        }
    
    async def _analyze_sentiment(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Analyze sentiment of the message"""
        sentiment_scores = {
            "positive": 0.0,
            "negative": 0.0,
            "frustrated": 0.0,
            "neutral": 1.0  # Base neutral score
        }
        
        # Count sentiment keywords
        for sentiment_type, keywords in self.sentiment_keywords.items():
            for keyword in keywords:
                if keyword in message:
                    sentiment_scores[sentiment_type] += 1.0
        
        # Apply sentiment patterns
        negative_patterns = [
            r"not\s+working",
            r"doesn[\'t]\s+work",
            r"this\s+is\s+(ridiculous|absurd)",
            r"waste\s+of\s+time"
        ]
        
        for pattern in negative_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                sentiment_scores["negative"] += 0.5
        
        # Determine dominant sentiment
        max_sentiment = max(sentiment_scores, key=sentiment_scores.get)
        max_score = sentiment_scores[max_sentiment]
        
        # Convert to sentiment enum and score
        if max_sentiment == "positive" and max_score > 0:
            sentiment = Sentiment.POSITIVE
            score = min(max_score / 3.0, 1.0)  # Normalize
        elif max_sentiment == "frustrated" and max_score > 0:
            sentiment = Sentiment.FRUSTRATED
            score = max(0.0, 1.0 - min(max_score / 2.0, 1.0))  # Inverted score
        elif max_sentiment == "negative" and max_score > 0:
            sentiment = Sentiment.NEGATIVE
            score = max(0.0, 1.0 - min(max_score / 2.0, 1.0))  # Inverted score
        else:
            sentiment = Sentiment.NEUTRAL
            score = 0.5
        
        confidence = min(max_score / 2.0, 1.0) if max_score > 0 else 0.7
        
        return {
            "sentiment": sentiment,
            "score": score,
            "confidence": confidence,
            "sentiment_scores": sentiment_scores
        }
    
    async def _detect_language(self, message: str) -> str:
        """Detect the language of the message"""
        language_scores = {"en": 1.0}  # Default to English
        
        # Check for non-English patterns
        for lang, keywords in self.language_patterns.items():
            score = sum(1 for keyword in keywords if keyword in message)
            if score > 0:
                language_scores[lang] = score
        
        # Return language with highest score
        detected_language = max(language_scores, key=language_scores.get)
        return detected_language
    
    async def _assess_urgency(self, message: str, state: AgentState) -> str:
        """Assess the urgency level of the message"""
        urgency_keywords = {
            "high": [
                "urgent", "emergency", "critical", "immediately", "asap",
                "right now", "can't work", "business down", "losing money"
            ],
            "medium": [
                "soon", "important", "need help", "issue", "problem"
            ],
            "low": [
                "question", "wondering", "curious", "when you have time"
            ]
        }
        
        urgency_scores = {"low": 0, "medium": 0, "high": 0}
        
        for level, keywords in urgency_keywords.items():
            for keyword in keywords:
                if keyword in message:
                    urgency_scores[level] += 1
        
        # Customer tier adjustment
        if state.customer and state.customer.tier.value == "platinum":
            urgency_scores["high"] += 1
        
        # Return highest scoring urgency level
        max_urgency = max(urgency_scores, key=urgency_scores.get)
        return max_urgency if urgency_scores[max_urgency] > 0 else "medium"
    
    async def _apply_context_adjustments(
        self, 
        intent: str, 
        confidence: float, 
        message: str, 
        state: AgentState
    ) -> float:
        """Apply context-based confidence adjustments"""
        adjusted_confidence = confidence
        
        # History-based adjustments
        if state.conversation_history:
            recent_intents = [
                turn.get("intent") for turn in state.conversation_history[-3:]
                if turn.get("intent") and turn.get("speaker") == "customer"
            ]
            
            # If recent intents match, boost confidence
            if intent in recent_intents:
                adjusted_confidence = min(adjusted_confidence + 0.1, 1.0)
        
        # Customer profile adjustments
        if state.customer:
            # VIP customers get slight confidence boost
            if state.customer.tier.value in ["gold", "platinum"]:
                adjusted_confidence = min(adjusted_confidence + 0.05, 1.0)
        
        # Message length adjustments
        word_count = len(message.split())
        if word_count < 3:
            adjusted_confidence *= 0.8  # Reduce confidence for very short messages
        elif word_count > 20:
            adjusted_confidence = min(adjusted_confidence + 0.1, 1.0)  # Boost for detailed messages
        
        return max(0.0, min(1.0, adjusted_confidence))
    
    async def _log_classification_metrics(
        self,
        intent_result: Dict[str, Any],
        sentiment_result: Dict[str, Any],
        language: str,
        urgency_level: str
    ):
        """Log classification metrics for monitoring"""
        try:
            if self.tool_registry:
                await self.tool_registry.execute_tool(
                    "log_interaction_metrics",
                    {
                        "metric_type": "intent_classification",
                        "intent": intent_result["intent"],
                        "intent_confidence": intent_result["confidence"],
                        "sentiment": sentiment_result["sentiment"].value,
                        "sentiment_confidence": sentiment_result["confidence"],
                        "language": language,
                        "urgency_level": urgency_level,
                        "timestamp": datetime.now().isoformat()
                    },
                    self.get_agent_context(AgentState(session_id="", conversation_id=""))
                )
        except Exception as e:
            logger.warning(f"Failed to log classification metrics: {e}")