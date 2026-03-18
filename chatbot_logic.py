"""
chatbot_logic.py
----------------
Rule-based logic for the HEFI Support Bot.
Provides immediate feedback on energy fairness, scoring, and saving tips.
"""

import random

def get_chatbot_response(user_query, user_data=None):
    """
    Analyzes intent and returns a contextual response.
    """
    query = user_query.lower()
    
    # Intent 1: Explaining HEFI
    if any(word in query for word in ["what is hefi", "define hefi", "fairness index"]):
        return ("**HEFI (Household Energy Fairness Index)** is a score from 0 to 100 used to determine equitable electricity tariffs. "
                "Unlike traditional models that only look at consumption, HEFI considers your income, household size, and energy dependency to "
                "ensure those who need subsidies most actually receive them.")

    # Intent 2: Specific Score Components
    if "score" in query or "low" in query or "high" in query:
        if user_data:
            hefi = user_data.get('hefi_score', 'N/A')
            tier = user_data.get('tariff_tier', 'N/A')
            response = f"Your current HEFI score is **{hefi}**, placing you in the **{tier}** tier. "
            
            if user_data.get('income_vulnerability', 0) > 0.7:
                response += "\n\nYour score is primarily driven by high *Income Vulnerability*. You are prioritised for social subsidies."
            elif user_data.get('energy_dependency', 0) > 0.7:
                response += "\n\nYour *Energy Dependency* is high. This can happen if you rely on electricity for critical medical or cooking needs."
            
            return response
        return "To explain your score, please log in so I can see your household parameters."

    # Intent 3: How to improve/reduce bill
    if any(word in query for word in ["lower", "reduce", "bill", "save", "subsidy"]):
        return ("To lower your bill or improve your fairness index status:\n"
                "1. **Report updates**: If your household size has increased, update your details to increase your HEFI score.\n"
                "2. **Renewable Energy**: Installing solar solar panels can provide a 'Green Bonus' to your index.\n"
                "3. **Efficiency**: Reducing waste during peak hours helps the grid and your regional anomaly score.")

    # Intent 4: Meaning of tiers
    if "tier" in query or "subsidized" in query or "premium" in query:
        return ("- **Subsidized (70-100)**: Maximum support for vulnerable households.\n"
                "- **Standard (40-69)**: Regular billing for average households.\n"
                "- **Premium (0-39)**: Higher rates for high-income, high-consumption luxury users.")

    # Fallback
    responses = [
        "I'm here to help with your Energy Fairness questions. Could you specify if you're asking about your score, the tariff tiers, or how to save energy?",
        "Interesting question! As an AI assistant, I can explain how your HEFI score is calculated. What would you like to know?",
        "I can help you understand your electricity classification. Are you looking for information on your current tariff tier?"
    ]
    return random.choice(responses)
