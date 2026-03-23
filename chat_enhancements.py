"""
chat_enhancements.py
--------------------
Advanced features for the HEFI AI chatbot:
- Follow-up question suggestions
- Context awareness
- Response confidence scoring
- Query validation
- Multi-turn conversation support
"""

from typing import Optional, Dict, List, Tuple, Any

# Contextual follow-up questions by topic
FOLLOWUP_SUGGESTIONS = {
    "what_is_hefi": [
        "How is my personal HEFI score calculated?",
        "What are the different tariff tiers?",
        "How can HEFI help me save money?"
    ],
    "tariff_tiers": [
        "What's my current tariff tier?",
        "How can I move to a better tier?",
        "What subsidies come with my tier?"
    ],
    "income_vulnerability": [
        "How does household size affect my score?",
        "What other factors determine my HEFI?",
        "Can I improve my score?"
    ],
    "household_size": [
        "What about energy dependency?",
        "How does income affect my score?",
        "Do I qualify for subsidies?"
    ],
    "energy_dependency": [
        "I have a medical condition - how does this help?",
        "What consumption levels are normal?",
        "How are anomalies detected?"
    ],
    "consumption_anomaly": [
        "Why is my consumption so high?",
        "How can I reduce unusual usage?",
        "What usage patterns are normal?"
    ],
    "save_money": [
        "Will energy savings improve my HEFI?",
        "Are there government subsidies I can get?",
        "Should I install solar panels?"
    ],
    "subsidies": [
        "How much can I save with subsidies?",
        "What other help is available?",
        "How do I claim my subsidies?"
    ],
    "renewable_energy": [
        "How much does solar cost?",
        "Will solar improve my HEFI score?",
        "Are there solar subsidies?"
    ],
    "improve_score": [
        "What's the fastest way to improve my score?",
        "How long does recalculation take?",
        "Will my bill immediately change?"
    ],
    "score_breakdown": [
        "Which factor most affects my score?",
        "How can I improve specific components?",
        "What's a good HEFI score?"
    ]
}


def get_followup_suggestions(intent: str, max_suggestions: int = 3) -> List[str]:
    """
    Returns contextual follow-up questions based on the detected intent.
    
    Args:
        intent: The classified intent from the user query
        max_suggestions: Maximum number of suggestions to return
        
    Returns:
        List of relevant follow-up questions
    """
    suggestions = FOLLOWUP_SUGGESTIONS.get(intent, 
        [
            "Is there anything else about HEFI you'd like to know?",
            "Would you like tips on saving energy?",
            "Can I help with anything else?"
        ]
    )
    return suggestions[:max_suggestions]


def validate_query(query: str) -> Tuple[bool, str]:
    """
    Validates if a query is a legitimate HEFI-related question.
    
    Args:
        query: User's input query
        
    Returns:
        Tuple of (is_valid, validation_message)
    """
    if not query or not query.strip():
        return False, "Please enter a question."
    
    if len(query) < 3:
        return False, "Question is too short. Please provide more details."
    
    if len(query) > 500:
        return False, "Question is too long. Please ask a more concise question."
    
    # Check for HEFI-related keywords
    hefi_keywords = [
        "hefi", "score", "tariff", "tier", "energy", "electricity", "bill", 
        "save", "income", "household", "subsidy", "solar", "renewable", 
        "consumption", "dependency", "fair", "fair", "vulnerable", "efficient"
    ]
    
    query_lower = query.lower()
    has_hefi_content = any(keyword in query_lower for keyword in hefi_keywords)
    
    if not has_hefi_content:
        return True, ""  # Accept non-HEFI queries but note user might get generic response
    
    return True, ""


def score_response_confidence(intent: str, query: str, keywords_matched: int) -> float:
    """
    Scores the confidence of the response (0.0 to 1.0).
    
    Args:
        intent: The classified intent
        query: The original user query
        keywords_matched: Number of keywords matched
        
    Returns:
        Confidence score from 0.0 to 1.0
    """
    confidence = 0.5  # Base confidence
    
    # Boost for direct keyword matches
    if keywords_matched >= 3:
        confidence += 0.3
    elif keywords_matched == 2:
        confidence += 0.2
    elif keywords_matched == 1:
        confidence += 0.1
    
    # Boost for specific intents
    specific_intents = {
        "what_is_hefi": 0.9,
        "tariff_tiers": 0.92,
        "subsidies": 0.88,
        "save_money": 0.85
    }
    confidence = specific_intents.get(intent, min(confidence, 0.95))
    
    return min(confidence, 1.0)


def format_response_with_metadata(response: str, intent: str, query: str, 
                                  user_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Packages response with metadata including follow-up suggestions.
    
    Args:
        response: The generated response text
        intent: The classified intent
        query: The original query
        user_data: Optional user household data
        
    Returns:
        Dictionary with response and metadata
    """
    followups = get_followup_suggestions(intent)
    
    return {
        "response": response,
        "intent": intent,
        "followup_questions": followups,
        "personalized": user_data is not None,
        "metadata": {
            "type": "HEFI Assistant Response",
            "can_provide_followups": len(followups) > 0
        }
    }


def detect_user_intent_context(new_query: str, chat_history: List[Dict[str, str]]) -> str:
    """
    Analyzes chat history to understand context for follow-up questions.
    
    Args:
        new_query: The current user query
        chat_history: List of previous messages
        
    Returns:
        Context string (e.g., "clarification", "followup", "new_topic")
    """
    if not chat_history or len(chat_history) < 2:
        return "new_topic"
    
    last_user_msg = None
    for msg in reversed(chat_history):
        if msg['role'] == 'user':
            last_user_msg = msg['text']
            break
    
    if not last_user_msg:
        return "new_topic"
    
    # Simple heuristics for context
    clarifying_words = ["what", "why", "how", "which", "tell me", "explain", "example"]
    if any(word in new_query.lower() for word in clarifying_words):
        if "score" in last_user_msg.lower() and "score" in new_query.lower():
            return "clarification"
        return "followup"
    
    return "new_topic"


def generate_contextual_prompt(intent: str, context: str, user_data: Optional[Dict] = None) -> str:
    """
    Generates a contextual system prompt for the response based on intent.
    
    Args:
        intent: The classified intent
        context: The conversation context
        user_data: Optional user data
        
    Returns:
        A contextual prompt for better responses
    """
    base_prompt = f"Provide a helpful response about {intent.replace('_', ' ')}. "
    
    if context == "clarification":
        base_prompt += "The user is asking for clarification. Be concise and specific. "
    elif context == "followup":
        base_prompt += "This is a follow-up question. Build on previous context. "
    else:
        base_prompt += "This is a new topic. Provide comprehensive information. "
    
    if user_data:
        base_prompt += f"The user's household size is {user_data.get('household_size', '?')} "
        base_prompt += f"with monthly income ₹{user_data.get('household_income', '?')}. "
    
    return base_prompt


class ConversationMemory:
    """
    Maintains conversation context for multi-turn interactions.
    """
    
    def __init__(self, max_history: int = 10):
        self.history = []
        self.max_history = max_history
        self.current_intent = None
        self.topics_discussed = set()
    
    def add_exchange(self, user_msg: str, bot_response: str, intent: str):
        """Adds a user-bot exchange to memory."""
        self.history.append({
            "user": user_msg,
            "bot": bot_response,
            "intent": intent,
            "topic": intent.replace('_', ' ')
        })
        self.topics_discussed.add(intent)
        self.current_intent = intent
        
        # Keep only recent history
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def get_recent_context(self) -> str:
        """Returns a summary of recent conversation."""
        if not self.history:
            return "No previous context."
        
        topics = ", ".join(list(self.topics_discussed)[:3])
        return f"Previously discussed: {topics}"
    
    def should_provide_followup(self) -> bool:
        """Determines if follow-up questions should be suggested."""
        return len(self.history) > 0 and len(self.topics_discussed) < 5


# Quick reference for decision-making
HEFI_DECISION_TREE = {
    "improve_score": {
        "prerequisite": "Does your situation match the qualifying criteria?",
        "actions": [
            "Update household size (add new members)",
            "Report income changes (job loss, salary cut)",
            "Declare health conditions (energy dependency)",
            "Install renewable energy"
        ]
    },
    "reduce_bill": {
        "prerequisite": "What's your current consumption level?",
        "high_consumption": [
            "Shift usage to off-peak hours",
            "Service your AC unit",
            "Reduce AC temperature by 1-2°C",
            "Cook efficiently"
        ],
        "normal_consumption": [
            "Use LED bulbs",
            "Unplug idle devices",
            "Use ceiling fans over AC"
        ]
    },
    "understand_score": {
        "ask_about": [
            "Your household size (vs. income ratio)",
            "Your energy dependency status",
            "Your recent consumption anomalies",
            "Changes in household composition"
        ]
    }
}
