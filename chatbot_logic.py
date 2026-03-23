"""
chatbot_logic.py
----------------
Advanced AI Support Chatbot for HEFI System.
Provides comprehensive, real-time responses to HEFI-related questions with
personalized recommendations based on user data.
"""

import re
from typing import Optional, Dict, Any, Tuple

# Import enhancements with fallback
try:
    from chat_enhancements import (
        get_followup_suggestions, 
        validate_query,
        score_response_confidence,
        format_response_with_metadata,
        detect_user_intent_context,
        HEFI_DECISION_TREE
    )
    ENHANCEMENTS_AVAILABLE = True
except ImportError:
    # Fallback if enhancements module not found
    ENHANCEMENTS_AVAILABLE = False
    def get_followup_suggestions(intent, max_suggestions=3):
        return []
    def validate_query(query):
        return True, ""
    def score_response_confidence(intent, query, keywords_matched):
        return 0.7
    def format_response_with_metadata(response, intent, query, user_data=None):
        return {"response": response, "intent": intent}

# ─── Knowledge Base ────────────────────────────────────────────────────────────
HEFI_KNOWLEDGE = {
    "what_is_hefi": {
        "keywords": ["what", "hefi", "define", "fairness", "index", "meaning"],
        "response": """🏠 **HEFI (Household Energy Fairness Index)** is an AI-powered scoring system (0-100) that determines fair electricity tariffs.

**Why HEFI Exists:**
- Traditional tariffs only consider consumption, ignoring those who truly need support
- HEFI ensures vulnerable households receive maximum subsidies
- It balances equity with efficiency across the entire grid

**What HEFI Considers:**
- 💰 **Income**: Lower income = Higher priority for subsidies
- 👥 **Household Size**: Larger families get more support
- ⚡ **Energy Dependency**: Critical reliance on electricity (medical, cooking)
- 📊 **Consumption Patterns**: Unusual usage flags are analyzed

Your unique combination of these factors determines your score."""
    },
    
    "tariff_tiers": {
        "keywords": ["tier", "tariff", "subsidized", "standard", "premium", "classification"],
        "response": """📊 **HEFI Tariff Tiers Explained:**

🟢 **SUBSIDIZED (Score: 70-100)**
- Maximum financial support for vulnerable households
- Lower electricity rates
- Access to additional welfare schemes
- Eligible if: Low income, large family, high energy dependency

🟡 **STANDARD (Score: 40-69)**
- Regular market-based pricing
- Stable, predictable monthly bills
- No subsidies, no surcharge
- Suitable for average households

🔴 **PREMIUM (Score: 0-39)**
- Higher rates for high-income, high-consumption users
- Encourages conservation
- Supports subsidy fund for vulnerable groups
- Applies to luxury consumption patterns"""
    },
    
    "income_vulnerability": {
        "keywords": ["income", "vulnerable", "poverty", "afford", "subsidy"],
        "response": """💰 **Income Vulnerability in HEFI:**

Your household's monthly income is a major factor in your HEFI score.

**How It Affects Your Score:**
- **Low Income** (₹0-15,000/month): Very high vulnerability score (+25-30 points)
- **Lower-Middle** (₹15,000-35,000): High vulnerability (+15-20 points)
- **Middle** (₹35,000-75,000): Moderate vulnerability (+5-10 points)
- **High** (₹75,000+): Lower vulnerability (+0-5 points)

**Example:**
- A family earning ₹10,000/month gets 25+ points for income vulnerability
- The same family earning ₹100,000/month gets 2-3 points

**Pro Tip:** If your household income has decreased (job loss, retirement), update your profile immediately for recalculation."""
    },
    
    "household_size": {
        "keywords": ["household", "size", "members", "family", "people", "dependents"],
        "response": """👥 **Household Size Factor:**

HEFI recognizes that larger families have more electricity needs and are often poorer.

**Scoring Impact:**
- **1 member**: Base factor (1.0)
- **2-3 members**: +5-8 points to HEFI
- **4-5 members**: +10-15 points to HEFI
- **6+ members**: +18-25 points to HEFI

**Real Example:**
- Same income household with 2 people: HEFI = 45 (Standard tier)
- Same income household with 5 people: HEFI = 62 (Subsidized tier)

**Action:** Pregnant? Adopted a child? Update your household size immediately—it directly improves your HEFI score!"""
    },
    
    "energy_dependency": {
        "keywords": ["dependency", "dependent", "critical", "medical", "reliance", "essential"],
        "response": """⚡ **Energy Dependency Score:**

This measures how critical electricity is to your household's survival and wellbeing.

**High Dependency Examples:**
- ❤️ Medical equipment (oxygen concentrators, ventilators, refrigerated medicines)
- 👶 Infant care (sterilizers, refrigeration for formula)
- 🧑‍🦽 Mobility aids (wheelchairs, lifts)
- 🍳 No alternative cooking (electric-only kitchen)
- ❄️ Climate control needed for health (severe asthma, heart conditions)

**How It Affects HEFI:**
- High dependency (8-10): +15-20 points
- Medium dependency (5-7): +8-12 points
- Low dependency (0-4): +0-5 points

**Update Your Dependency:** If you have health conditions requiring electricity, inform your utility—your HEFI will improve."""
    },
    
    "consumption_anomaly": {
        "keywords": ["anomaly", "consumption", "unusual", "pattern", "usage", "high", "low", "spike"],
        "response": """📈 **Consumption Anomaly Detection:**

HEFI flags unusual electricity usage patterns to prevent fraud and identify struggling households.

**Why Anomalies Matter:**
- **Extremely High Usage**: May indicate theft, waste, or lifestyle inflation (reduces HEFI)
- **Extremely Low Usage**: May indicate disconnection, poverty, or inability to pay (increases HEFI)
- **Erratic Patterns**: Possible meter issues or seasonal needs

**Example Anomalies:**
- Family of 4 consuming 500+ kWh/month with high AC = Not vulnerable (lower HEFI)
- Family of 4 consuming 20 kWh/month = May indicate energy poverty (higher HEFI)
- Sudden spikes = Could indicate medical equipment new installation

**Your Anomaly Score:** If flagged, it usually indicates you need special attention or support."""
    },
    
    "save_money": {
        "keywords": ["save", "lower", "reduce", "bill", "cost", "money", "cheaper"],
        "response": """💡 **How to Save on Your Electricity Bill:**

**Immediate Actions (0-1 month impact):**
1. **Turn off idle devices**: Screen a TV off when not watching, unplug chargers
2. **Use LED bulbs**: Replace old incandescent with LEDs (saves 80%)
3. **Close vents**: Keep cool air in one room during AC usage
4. **Shift peak usage**: Use heavy appliances (washing, cooking) during off-peak hours (avoid 6-10 PM)

**Short-term (1-3 months):**
1. **Open windows at night**: Let natural ventilation replace AC
2. **Use ceiling fans**: More efficient than air conditioning
3. **Service your AC**: A clean filter saves 10-15%
4. **Cook efficiently**: Use lids on pots, cook multiple dishes together

**Long-term (3-12 months):**
1. **Install solar panels**: Reduces grid dependence by 40-60%
2. **Buy energy-efficient appliances**: STAR-rated refrigerators, fans
3. **Insulate your home**: Reduces cooling/heating needs
4. **Install solar water heater**: Eliminates 30-40% of consumption

**For Your HEFI Score:**
✅ **Reduces bill** → May lower your consumption anomaly score
✅ **Solar installation** → Adds "green bonus" to your index  
⚠️ **But remember:** Better to be honest about consumption—don't lie to improve your score!"""
    },
    
    "subsidies": {
        "keywords": ["subsidy", "subsidized", "help", "support", "scheme", "welfare", "grant", "discount"],
        "response": """🟢 **Understanding HEFI Subsidies:**

**Who Gets Subsidies?**
If your HEFI score is **70-100**, you're in the **SUBSIDIZED tier** and eligible for:

**Monthly Benefits:**
- ✅ 30-50% discount on electricity rates
- ✅ Guaranteed minimum free units (e.g., first 50 kWh free)
- ✅ Lower disconnection risk even if payment is late
- ✅ Priority reconnection if disconnected

**Additional Schemes (if eligible):**
- 🏠 Home weatherization programs
- ☀️ Subsidized solar installation grants
- 💡 Free energy-efficient lighting
- 📱 Mobile app for bill management with alerts
- 💬 Free calls to support helpline

**How Subsidies Work:**
$$ Government pays utility ⟶ Utility charges you less ⟶ You save money

**Important:** Your subsidy is based on your honest household data. If you update your details (new baby, job loss, health condition), your subsidy adjusts automatically."""
    },
    
    "renewable_energy": {
        "keywords": ["renewable", "solar", "green", "panel", "photovoltaic", "eco", "sustainable"],
        "response": """☀️ **Renewable Energy & HEFI:**

**Installing Solar?**
- Adds a **'Green Bonus'** to your HEFI score (+5-10 points)
- Reduces your consumption anomaly score
- May shift you to a better tier

**For Low-Income Households:**
- Some utilities have **subsidized solar programs** for HEFI-eligible families
- You may qualify for 50% subsidy on solar installation
- Payback period could be 3-5 years

**Why Government Promotes Solar:**
- Reduces strain on grid during peak hours
- Improves your household's energy independence
- Cuts emissions (environmental benefit)

**What HEFI Considers:**
- Your renewable energy access (Yes/No) affects your score
- Grid-tied solar + your HEFI score = Best combination

**Next Steps:**
1. Check if your state has a renewable subsidy program
2. Get quotes from certified installers
3. Update your HEFI status once installed—your score may improve!"""
    },
    
    "improve_score": {
        "keywords": ["improve", "increase", "boost", "better", "higher", "upgrade"],
        "response": """📈 **How to Improve Your HEFI Score:**

**Quick Actions (Honest Updates):**
✅ **Update household size**: New baby? Grandparent moved in? Update immediately (+5-15 points)
✅ **Report income decrease**: Lost a job? Pension reduced? HEFI recalculates instantly (+10-25 points)
✅ **Add health conditions**: Medical equipment? Declare energy dependency (+5-20 points)
✅ **Install renewable energy**: Solar installation adds green bonus (+5-10 points)

**Real Example:**
- Household with ₹50k income + 4 people = 55 (Standard)
- After baby birth → 65 (Approaching Subsidized!)
- Installation of solar → 72 (Now Subsidized!)

**DO NOT:**
❌ Lie about income
❌ Hide appliances or household members
❌ Fake energy dependency claims
→ These are verified and fraud results in penalty

**Honest Way Forward:**
- Your situation may genuinely improve your score
- Update details when your life changes
- Be transparent = System works for you
- HEFI rewards truth!"""
    },
    
    "score_breakdown": {
        "keywords": ["breakdown", "components", "factor", "weight", "calculate", "formula"],
        "response": """📊 **How Your HEFI Score is Calculated:**

Your HEFI combines **4 weighted factors**:

**1. Income Vulnerability (30% weight)**
   - How much your income limits energy access
   - Formula: Adjusted based on local poverty line

**2. Household Size (20% weight)**
   - More people = Higher basic electricity needs
   - Scales non-linearly (advantage for large families)

**3. Energy Dependency (30% weight)**
   - Critical reliance on electricity for health/survival
   - Medical, cooking, climate needs

**4. Consumption Anomaly (20% weight)**
   - Is your actual usage unusual?
   - Low usage in poor household = Higher score
   - High usage in wealthy household = Lower score

**Example Calculation:**
```
Income Vulnerability:  35/100 × 0.30 = 10.5 points
Household Size:        25/100 × 0.20 = 5.0 points
Energy Dependency:     80/100 × 0.30 = 24.0 points
Consumption Anomaly:   30/100 × 0.20 = 6.0 points
═══════════════════════════════════════════
FINAL HEFI SCORE:                    45.5 (Standard tier)
```

**Key Insight:** All factors matter equally in combination. One high factor alone doesn't guarantee a high score."""
    },
    
    "frequently_asked": {
        "keywords": ["faq", "common", "question", "problem", "issue", "help", "support"],
        "response": """❓ **Frequently Asked HEFI Questions:**

**Q: Will updating my details change my bill?**
A: No immediately. Your next billing cycle applies the new rate. One update takes 1-2 days to process.

**Q: Can I appeal my HEFI score?**
A: Yes! Contact your utility's HEFI office with evidence (income documents, medical reports). Appeals are free.

**Q: What if my bill still seems unfair?**
A: Your tier is recalculated monthly. If your score crossed into a new tier, wait for the next billing cycle.

**Q: Is HEFI data private?**
A: Yes. Your data is encrypted and only used for tariff calculation. Not shared without consent.

**Q: Can I request a manual audit?**
A: Absolutely. Request via the mobile app or call the helpline. Typically takes 5-7 business days.

**Q: What if I have multiple incomes?**
A: Report your total household income. Include salaries, pensions, business income, everything.

**Q: Does HEFI check meter data?**
A: Yes, we analyze consumption patterns. Unusual usage is flagged and investigated.

**Q: Can I game the system?**
A: No. The HEFI algorithm is sophisticated. Fraud is detected and penalized."""
    }
}


def classify_intent(query: str) -> str:
    """
    Classifies user query into one of the HEFI knowledge categories.
    Returns the matching intent key.
    """
    query_lower = query.lower()
    
    # Score each knowledge base category
    scores = {}
    for intent_key, intent_data in HEFI_KNOWLEDGE.items():
        keyword_matches = sum(1 for keyword in intent_data["keywords"] if keyword in query_lower)
        scores[intent_key] = keyword_matches
    
    # Return the intent with highest match score
    best_intent = max(scores.items(), key=lambda x: x[1])
    return best_intent[0] if best_intent[1] > 0 else "frequently_asked"


def personalize_response(base_response: str, user_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Personalizes the base response with user-specific data.
    """
    if not user_data:
        return base_response
    
    personalization = "\n\n---\n**📌 Your Personal Situation:**\n"
    
    hefi_score = user_data.get('hefi_score', 0)
    tier = user_data.get('tariff_tier', 'Unknown')
    income = user_data.get('household_income', 0)
    household_size = user_data.get('household_size', 0)
    consumption = user_data.get('monthly_electricity_consumption_kwh', 0)
    income_vuln = user_data.get('income_vulnerability', 0)
    
    personalization += f"- **Your Score:** {hefi_score:.1f} (**{tier}** Tier)\n"
    personalization += f"- **Household Income:** ₹{income:,}/month\n"
    personalization += f"- **Family Size:** {household_size} members\n"
    personalization += f"- **Monthly Usage:** {consumption:.0f} kWh\n"
    
    # Add smart tips based on their situation
    if income < 20000:
        personalization += "\n💡 **Tip:** You likely qualify for maximum subsidies. Make sure all welfare schemes are applied to your account."
    
    if household_size > 5:
        personalization += f"\n💡 **Tip:** Your family size ({household_size}) significantly improves your HEFI score. You're correctly classified as vulnerable."
    
    if consumption > 300:
        personalization += "\n💡 **Tip:** Your consumption is high. Consider the energy-saving strategies above—you could reduce bills by 20-30%."
    
    if hefi_score >= 70:
        personalization += f"\n✅ **Good News:** You're in the **SUBSIDIZED tier** (≥70 points). Verify all subsidies are applied to your account!"
    elif hefi_score >= 40:
        personalization += f"\n📊 **Status:** You're in the **STANDARD tier**. Monitor for life changes that might improve your score."
    else:
        personalization += f"\n🔔 **Note:** You're in the **PREMIUM tier**. Consider updating if there have been changes in your household situation."
    
    return base_response + personalization


def get_chatbot_response(user_query: str, user_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Advanced chatbot that recognizes intent and provides real-time, contextualized responses.
    
    Args:
        user_query: The user's question about HEFI
        user_data: Dictionary containing user's household information
        
    Returns:
        A comprehensive, personalized response string
    """
    if not user_query or not user_query.strip():
        return "👋 Hi! Ask me anything about HEFI, your score, tariffs, energy saving, or subsidies. I'm here to help!"
    
    # Validate query
    is_valid, validation_msg = validate_query(user_query)
    if not is_valid:
        return f"⚠️ {validation_msg} Try asking something like: 'What is HEFI?' or 'How can I save energy?'"
    
    # Classify the user's intent
    intent = classify_intent(user_query)
    
    # Get the base response from knowledge base
    base_response = HEFI_KNOWLEDGE[intent]["response"]
    
    # Personalize with user data
    personalized_response = personalize_response(base_response, user_data)
    
    # Score confidence
    keywords_matched = sum(1 for kw in HEFI_KNOWLEDGE[intent]["keywords"] if kw in user_query.lower())
    confidence = score_response_confidence(intent, user_query, keywords_matched)
    
    # Add follow-up suggestions if confidence is high enough
    if confidence > 0.6:
        followups = get_followup_suggestions(intent, max_suggestions=2)
        personalized_response += "\n\n---\n**💡 Follow-up Questions You Might Ask:**\n"
        for i, followup in enumerate(followups, 1):
            personalized_response += f"{i}. {followup}\n"
    
    return personalized_response


def get_chatbot_response_with_metadata(user_query: str, user_data: Optional[Dict[str, Any]] = None,
                                      chat_history: Optional[list] = None) -> Dict[str, Any]:
    """
    Enhanced chatbot response with metadata, confidence, and follow-up suggestions.
    
    Args:
        user_query: The user's question about HEFI
        user_data: Dictionary containing user's household information
        chat_history: Previous conversation history for context
        
    Returns:
        Dictionary containing response and metadata
    """
    response_text = get_chatbot_response(user_query, user_data)
    intent = classify_intent(user_query)
    
    # Detect conversation context if enhancements available
    context = "new_topic"
    if ENHANCEMENTS_AVAILABLE and chat_history and len(chat_history) >= 2:
        try:
            context = detect_user_intent_context(user_query, chat_history)
        except:
            context = "new_topic"
    
    return format_response_with_metadata(response_text, intent, user_query, user_data)


def get_quick_answer(user_query: str) -> Optional[str]:
    """
    Returns a quick, concise answer for simple HEFI questions.
    Best for FAQ-style questions.
    
    Args:
        user_query: The user's question
        
    Returns:
        Quick answer string or None if answer not found
    """
    query_lower = user_query.lower()
    
    # Quick answer patterns
    quick_answers = {
        "am i eligible for subsidies": "Yes! If your HEFI score is 70 or above, you qualify for the Subsidized tier with 30-50% discounts.",
        "what tier am i": "To see your exact tier, log in and check the 'My HEFI Status' dashboard.",
        "how long until my score updates": "Usually 1-2 days after you submit changes. Billing cycles apply changes in the next month.",
        "can my score go down": "Yes, if your household composition decreases or income significantly increases.",
        "is my data private": "100% yes. Your HEFI data is encrypted and only used for tariff calculation.",
        "how do i appeal": "Contact your utility's HEFI office with evidence (income docs, medical reports). Appeals are free.",
    }
    
    for pattern, answer in quick_answers.items():
        if pattern in query_lower:
            return answer
    
    return None


def get_detailed_breakdown(user_data: Dict[str, Any]) -> str:
    """
    Provides a detailed breakdown of the user's HEFI components.
    
    Args:
        user_data: User's household data
        
    Returns:
        Detailed explanation of HEFI breakdown
    """
    if not user_data:
        return "Please log in to see your detailed HEFI breakdown."
    
    hefi = user_data.get('hefi_score', 0)
    income_vuln = user_data.get('income_vulnerability', 0)
    household_factor = user_data.get('household_size_factor', 0)
    energy_dep = user_data.get('energy_dependency', 0)
    anomaly = user_data.get('consumption_anomaly', 0)
    
    # Normalize to 0-100 scale (these are typically 0-1)
    income_vuln_score = income_vuln * 100 if income_vuln <= 1 else income_vuln
    household_score = household_factor * 100 if household_factor <= 1 else household_factor
    energy_score = energy_dep * 100 if energy_dep <= 1 else energy_dep
    anomaly_score = anomaly * 100 if anomaly <= 1 else anomaly
    
    breakdown = f"""📊 **Your HEFI Score Breakdown (Total: {hefi:.1f}/100)**

1. **Income Vulnerability (30% weight)**: {income_vuln_score:.1f}/100
   - Your income level relative to poverty line
   - Lower income = Higher score (more support)

2. **Household Size Factor (20% weight)**: {household_score:.1f}/100
   - Number of family members
   - Larger family = Higher score

3. **Energy Dependency (30% weight)**: {energy_score:.1f}/100
   - Critical reliance on electricity
   - Medical, cooking, climate needs

4. **Consumption Anomaly (20% weight)**: {anomaly_score:.1f}/100
   - How unusual your usage pattern is
   - Unusually low = Higher score
   - Unusually high = Lower score

**What This Means:**
- Score 70-100: **SUBSIDIZED** (Maximum support)
- Score 40-69: **STANDARD** (Regular pricing)
- Score 0-39: **PREMIUM** (Higher rates)

Your current tier: **{user_data.get('tariff_tier', 'Unknown')}**
"""
    return breakdown


def suggest_improvements(user_data: Dict[str, Any]) -> str:
    """
    Suggests specific improvements based on user's current HEFI profile.
    
    Args:
        user_data: User's household data
        
    Returns:
        Personalized improvement suggestions
    """
    if not user_data:
        return "Log in to get personalized improvement suggestions."
    
    hefi = user_data.get('hefi_score', 0)
    income = user_data.get('household_income', 0)
    size = user_data.get('household_size', 1)
    consumption = user_data.get('monthly_electricity_consumption_kwh', 0)
    renewable = user_data.get('renewable_energy_access', 'No')
    
    suggestions = "🎯 **Personalized Suggestions to Improve Your HEFI:**\n\n"
    
    # Income-based suggestions
    if income < 20000:
        suggestions += "💰 **Income Very Low**\n"
        suggestions += "- Document your income (bank statements, employment letters)\n"
        suggestions += "- Check if you qualify for additional welfare schemes\n"
        suggestions += "- Your HEFI score reflects your true vulnerability\n\n"
    
    # Size-based suggestions
    if size <= 2:
        suggestions += "👥 **Small Household**\n"
        suggestions += "- If you have new dependents, update family size immediately\n"
        suggestions += "- Each additional member can increase HEFI by 5-10 points\n\n"
    
    # Consumption-based suggestions
    if consumption > 250:
        suggestions += "⚡ **High Consumption**\n"
        suggestions += "- Review energy usage; high consumption reduces relative vulnerability\n"
        suggestions += f"- Save 20-30% by reducing peak-hour usage (currently {consumption:.0f} kWh/month)\n\n"
    elif consumption < 50:
        suggestions += "⚡ **Very Low Consumption**\n"
        suggestions += "- This often indicates energy poverty\n"
        suggestions += "- Ensure meter readings are accurate\n"
        suggestions += "- HEFI recognizes you may need essential appliances\n\n"
    
    # Renewable energy
    if renewable == 'No':
        suggestions += "☀️ **No Renewable Energy Yet**\n"
        suggestions += "- Installing solar adds 5-10 points to your HEFI\n"
        suggestions += "- Check if subsidies are available\n"
        suggestions += "- Renewable energy + your profile = Stronger case for subsidies\n\n"
    
    # Tier-based suggestions
    if hefi >= 70:
        suggestions += "✅ **You're in SUBSIDIZED Tier**\n"
        suggestions += "- Verify all subsidies are applied to your account\n"
        suggestions += "- Check if you qualify for additional schemes\n"
        suggestions += "- Maintain your profile accuracy\n"
    elif hefi >= 40:
        suggestions += "📊 **You're in STANDARD Tier**\n"
        suggestions += "- Monitor for life changes (new baby, job loss, health issues)\n"
        suggestions += "- These could improve your HEFI by 10-20 points\n"
        suggestions += "- Consider renewable energy installation\n"
    else:
        suggestions += "💼 **You're in PREMIUM Tier**\n"
        suggestions += "- This reflects your household's relative stability\n"
        suggestions += "- Your higher rates support subsidies for vulnerable families\n"
    
    return suggestions
