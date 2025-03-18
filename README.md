# YaarAI 🤖💙  
An **empathetic, multi-agent AI chatbot** designed to provide **human-like, emotionally intelligent conversations** by adapting to user emotions, sarcasm detection, and context awareness.

## 🌟 Overview  
YaarAI is a **multi-agentic conversational AI** that goes beyond traditional chatbots. It dynamically adjusts its responses based on:  
- **Emotion detection** 🧠 – Recognizing user sentiment through NLP models  
- **Context awareness** 📖 – Retaining conversation history for fluid engagement  
- **Sarcasm detection** 🎭 – Ensuring responses align with the user's actual intent  
- **Crisis handling** 🆘 – Responding with care in sensitive situations  

This project was developed as part of the **15th OSS4AI's AI Agent Hackathon at Microsoft Reactor** and is an ongoing effort to build AI that truly understands and engages with users.

---

## 🚀 Features  
✅ **Multi-Agent Architecture** – Separates responsibilities across different AI agents  
✅ **Sentiment & Emotion Analysis** – Uses NLP models to classify user emotions  
✅ **Memory-Based Conversations** – Context-aware responses with recall capability  
✅ **Adaptive Tone Matching** – Adjusts the chatbot's style based on the user's mood  
✅ **Sarcasm Interpretation** – Prevents misinterpretation of ironic or sarcastic messages  
✅ **Crisis Detection** – Recognizes distress signals and responds with empathy  

---

## 🔧 Installation  

### Clone the Repository**
```bash
git clone https://github.com/prathambusa/YaarAI.git
cd YaarAI
```

## Set Up a Virtual Environment
```bash
python -m venv env
source env/bin/activate  # Mac/Linux
env\Scripts\activate  # Windows
```
```bash
pip install -r requirements.txt
```

## Set Up OpenAI API Key
Get your OpenAI API key from OpenAI
Create a .env file in the root directory
Add the following line to the .env file:
```bash
OPENAI_API_KEY=your_api_key_here
```

## Now run it
```bash
streamlit run app.py
```

## Future Roadmap 🎯
- Migrate UI from Streamlit to React for a modern web experience
- Implement Text-to-Speech (TTS) models for more realistic AI conversations
- Enhance contextual memory for deeper, long-term interactions
- Improve sarcasm and sentiment detection with fine-tuned models

## Contact
For questions or collaboration, reach out to:
- 📧 Email: [busapratham@gmail.com]
- 🌐 LinkedIn: [linkedin.com/in/prathambusa15]

Let's build the future of empathetic AI conversations together! 🚀

