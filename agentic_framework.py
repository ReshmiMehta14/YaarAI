import json
from datetime import datetime
import uuid
# Add these imports at the top of your file
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
import openai

# Initialize the OpenAI client
client = openai.OpenAI(
    api_key="your_key"
)

# Initialize OpenTelemetry
def init_telemetry(endpoint="http://localhost:6006/v1/traces"):
    """Initialize OpenTelemetry with Phoenix"""
    trace_provider = TracerProvider()
    trace_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint)))
    trace.set_tracer_provider(trace_provider)
    return trace.get_tracer("emotional_support_chatbot")

# Define a class to store conversation history
class ConversationMemory:
    def __init__(self, max_history=20):
        self.messages = []
        self.max_history = max_history
        self.session_id = str(uuid.uuid4())
        self.session_start = datetime.now()
        self.user_profile = {
            "detected_emotions": [],
            "recurring_topics": [],
            "cultural_context": None,
            "communication_preferences": None
        }
    
    def add_message(self, role, content, emotion_data=None):
        """Add a message to the conversation history"""
        timestamp = datetime.now()
        message = {
            "role": role,
            "content": content,
            "timestamp": timestamp,
            "emotion_data": emotion_data
        }
        self.messages.append(message)
        # Trim history if it exceeds max length
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
    
    def get_recent_messages(self, count=5):
        """Get the most recent messages"""
        return self.messages[-count:] if len(self.messages) >= count else self.messages
    
    def get_formatted_history(self, count=5):
        """Get formatted conversation history for API calls"""
        recent = self.get_recent_messages(count)
        return [{"role": msg["role"], "content": msg["content"]} for msg in recent]
    
    def update_user_profile(self, emotion_data=None, topic=None):
        """Update user profile with new information"""
        if emotion_data and isinstance(emotion_data, dict):
            # Store last 5 emotions to track patterns
            if "emotion" in emotion_data:
                self.user_profile["detected_emotions"].append({
                    "emotion": emotion_data.get("emotion"),
                    "intensity": emotion_data.get("intensity_score"),
                    "timestamp": datetime.now()
                })
                if len(self.user_profile["detected_emotions"]) > 5:
                    self.user_profile["detected_emotions"] = self.user_profile["detected_emotions"][-5:]
        if topic and topic not in self.user_profile["recurring_topics"]:
            self.user_profile["recurring_topics"].append(topic)
            if len(self.user_profile["recurring_topics"]) > 10:
                self.user_profile["recurring_topics"] = self.user_profile["recurring_topics"][-10:]

# 1. User Input Processing Agent
def process_user_input(user_input, conversation_memory, user_input_prompt):
    """Process and sanitize user input"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": user_input_prompt},
                {"role": "user", "content": f"User message: {user_input}"}
            ],
            temperature=0.3
        )
        result_text = response.choices[0].message.content
        print("DEBUG: process_user_input raw response:", result_text)
        try:
            processed_input = json.loads(result_text)
        except json.JSONDecodeError:
            # Fall back to using raw text if JSON parsing fails
            processed_input = {"processed_text": result_text}
        # Add metadata
        processed_input["timestamp"] = datetime.now().isoformat()
        processed_input["raw_input"] = user_input
        # Update conversation memory with topic if provided
        if "main_topic" in processed_input:
            conversation_memory.update_user_profile(topic=processed_input["main_topic"])
        return processed_input
    except Exception as e:
        print("ERROR in process_user_input:", e)
        print(f"Full error details: {str(e)}")  # More detailed error
        return {
            "error": str(e),
            "raw_input": user_input,
            "timestamp": datetime.now().isoformat()
        }

# 2. Emotion Detection Agent
def detect_emotion(user_input, conversation_memory, emotion_detection_prompt):
    """Detects the user's emotional state from the input text using OpenAI API."""
    formatted_history = conversation_memory.get_formatted_history(5)
    conv_history_str = "None"
    if formatted_history:
        conv_history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in formatted_history])
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": emotion_detection_prompt},
                {"role": "user", "content": f"User message: {user_input}\n\nConversation history: {conv_history_str}"}
            ],
            temperature=0.7
        )
        result_text = response.choices[0].message.content
        print("DEBUG: detect_emotion raw response:", result_text)
        try:
            result_dict = json.loads(result_text)
        except json.JSONDecodeError:
            result_dict = {"detected_emotion": result_text}
        conversation_memory.update_user_profile(emotion_data=result_dict)
        return result_dict
    except Exception as e:
        print("ERROR in detect_emotion:", e)
        print(f"Full error details: {str(e)}")  # More detailed error
        return {"error": str(e)}

# 3. Context Management Agent
def analyze_context(user_input, processed_input, emotion_data, conversation_memory, context_management_prompt):
    """Analyzes conversation context to provide deeper understanding."""
    user_profile = conversation_memory.user_profile
    recent_emotions = user_profile["detected_emotions"]
    recurring_topics = user_profile["recurring_topics"]
    emotion_history = "None"
    if recent_emotions:
        emotion_history = ", ".join([f"{e['emotion']} (intensity: {e['intensity']})" for e in recent_emotions])
    formatted_history = conversation_memory.get_formatted_history(5)
    conv_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in formatted_history])
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": context_management_prompt},
                {"role": "user", "content": f"""
User message: {user_input}

Current emotion: {emotion_data.get('emotion', 'Unknown')} (Intensity: {emotion_data.get('intensity_score', 'Unknown')})
Sarcasm detected: {emotion_data.get('sarcasm_detected', 'Unknown')}

Recent emotion history: {emotion_history}

Recurring topics: {', '.join(recurring_topics) if recurring_topics else 'None detected yet'}

Conversation history:
{conv_history}
"""}
            ],
            temperature=0.5
        )
        result_text = response.choices[0].message.content
        print("DEBUG: analyze_context raw response:", result_text)
        try:
            context_analysis = json.loads(result_text)
        except json.JSONDecodeError:
            context_analysis = {"context_summary": result_text}
        if context_analysis.get("cultural_context", {}).get("cultural_elements_detected"):
            conversation_memory.user_profile["cultural_context"] = context_analysis["cultural_context"]["cultural_elements_detected"]
        return context_analysis
    except Exception as e:
        print("ERROR in analyze_context:", e)
        print(f"Full error details: {str(e)}")  # More detailed error
        return {"error": str(e)}

# 4. Response Generation Agent
def generate_response(user_input, emotion_data, context_analysis, conversation_memory, response_generation_prompt):
    """Generates an empathetic, friend-like response based on user input, emotional state, and context."""
    emotion = emotion_data.get("emotion", "Unknown") if isinstance(emotion_data, dict) else "Unknown"
    intensity = emotion_data.get("intensity_level", "Moderate") if isinstance(emotion_data, dict) else "Moderate"
    sarcasm = emotion_data.get("sarcasm_detected", "No") if isinstance(emotion_data, dict) else "No"
    focus_areas = context_analysis.get("response_guidance", {}).get("focus_areas", []) if isinstance(context_analysis, dict) else []
    approach = context_analysis.get("response_guidance", {}).get("approach_suggestion", "Supportive") if isinstance(context_analysis, dict) else "Supportive"
    avoid_topics = context_analysis.get("response_guidance", {}).get("avoid_topics", []) if isinstance(context_analysis, dict) else []
    cultural_context = conversation_memory.user_profile.get("cultural_context")
    communication_preferences = conversation_memory.user_profile.get("communication_preferences")
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": response_generation_prompt},
                {"role": "user", "content": f"""
Respond as a supportive friend to this message:

User message: "{user_input}"

IMPORTANT CONTEXT (use this to inform your response but don't reference it directly):
- User's detected emotion: {emotion} (Intensity: {intensity})
- Sarcasm detected: {sarcasm}
- Suggested focus areas: {', '.join(focus_areas) if focus_areas else 'None specified'}
- Suggested approach: {approach}
- Topics to avoid: {', '.join(avoid_topics) if avoid_topics else 'None specified'}
- Cultural context to consider: {cultural_context if cultural_context else 'None detected'}
- Communication preferences: {communication_preferences if communication_preferences else 'None specified'}

Remember to respond as a supportive friend would, not as a therapist or AI assistant.
"""}
            ],
            temperature=0.7,
            max_tokens=300
        )
        response_text = response.choices[0].message.content
        print("DEBUG: generate_response raw response:", response_text)
        try:
            response_json = json.loads(response_text)
            if "final_response" in response_json:
                return response_json["final_response"]
            else:
                return response_json.get("processed_text", response_text)
        except json.JSONDecodeError:
            return response_text
    except Exception as e:
        print("ERROR in generate_response:", e)
        print(f"Full error details: {str(e)}")  # More detailed error
        return "I'm here to listen. Would you like to tell me more about how you're feeling?"

# 5. Feedback Loop Agent
def process_feedback(user_input, previous_response, conversation_memory, feedback_loop_prompt):
    """Analyzes user feedback to previous response and suggests improvements."""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": feedback_loop_prompt},
                {"role": "user", "content": f"""
Previous system response: "{previous_response}"

User's latest message (potential feedback): "{user_input}"
"""}
            ],
            temperature=0.5
        )
        result_text = response.choices[0].message.content
        print("DEBUG: process_feedback raw response:", result_text)
        try:
            feedback_analysis = json.loads(result_text)
        except json.JSONDecodeError:
            feedback_analysis = {"feedback": result_text}
        return feedback_analysis
    except Exception as e:
        print("ERROR in process_feedback:", e)
        print(f"Full error details: {str(e)}")  # More detailed error
        return {"error": str(e)}

# Main Chatbot Class
class EmotionalSupportChatbot:
    def __init__(self, prompts):
        """Initialize the chatbot with the provided prompts."""
        self.prompts = prompts
        self.conversation_memory = ConversationMemory()
        self.previous_response = None
        self.debug_mode = False
    
    def set_debug_mode(self, enabled=True):
        """Enable or disable debug mode to see agent outputs"""
        self.debug_mode = enabled
    
    def process_message(self, user_input):
        """Process a user message through all agents and generate a response."""
        print("DEBUG: Available prompts keys:", self.prompts.keys())  # ✅ Check the dictionary keys
    
        tracer = trace.get_tracer("emotional_support_chatbot")
        with tracer.start_as_current_span("conversation_turn") as conversation_span:
            conversation_span.set_attribute("user_input", user_input)
            self.conversation_memory.add_message("user", user_input)
            with tracer.start_as_current_span("user_input_processing") as span:
                processed_input = process_user_input(
                    user_input, 
                    self.conversation_memory,
                    self.prompts["user_input_prompt"]
                )
                span.set_attribute("processed_input", str(processed_input))
                if self.debug_mode:
                    print("\n--- USER INPUT PROCESSING RESULT ---")
                    print(json.dumps(processed_input, indent=2))
            with tracer.start_as_current_span("emotion_detection") as span:
                emotion_data = detect_emotion(
                    user_input, 
                    self.conversation_memory,
                    self.prompts["emotion_detection_prompt"]
                )
                span.set_attribute("emotion", emotion_data.get("emotion", "Unknown"))
                span.set_attribute("intensity", emotion_data.get("intensity_level", "Unknown"))
                if self.debug_mode:
                    print("\n--- EMOTION DETECTION RESULT ---")
                    print(json.dumps(emotion_data, indent=2))
            with tracer.start_as_current_span("context_analysis") as span:
                context_analysis = analyze_context(
                    user_input,
                    processed_input,
                    emotion_data,
                    self.conversation_memory,
                    self.prompts["context_management_prompt"]
                )
                span.set_attribute("context_analysis", str(context_analysis))
                if self.debug_mode:
                    print("\n--- CONTEXT ANALYSIS RESULT ---")
                    print(json.dumps(context_analysis, indent=2))
            with tracer.start_as_current_span("response_generation") as span:
                response = generate_response(
                    user_input,
                    emotion_data,
                    context_analysis,
                    self.conversation_memory,
                    self.prompts["response_generation_prompt"]
                )
                span.set_attribute("response", response)
            self.conversation_memory.add_message("assistant", response, emotion_data)
            if self.previous_response:
                with tracer.start_as_current_span("feedback_processing") as span:
                    feedback_analysis = process_feedback(
                        user_input,
                        self.previous_response,
                        self.conversation_memory,
                        self.prompts["feedback_loop_prompt"]
                    )
                    span.set_attribute("feedback_analysis", str(feedback_analysis))
                    if self.debug_mode:
                        print("\n--- FEEDBACK ANALYSIS RESULT ---")
                        print(json.dumps(feedback_analysis, indent=2))
            self.previous_response = response
            conversation_span.set_attribute("final_response", response)
            return response

