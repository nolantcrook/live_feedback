# Live Feedback System

A real-time AI-powered conversation assistance application that listens to your microphone and provides live feedback from ChatGPT's API.

## Features

- **Real-time Speech Recognition**: Converts your speech to text using Google's speech recognition API
- **AI-Powered Recommendations**: Gets intelligent feedback and recommendations from OpenAI's GPT models
- **Custom System Prompts**: Configure the AI's role and behavior (e.g., sales coach, presentation assistant)
- **Modern Web Interface**: Clean, responsive web UI with real-time updates
- **Conversation History**: Keep track of your conversation and AI recommendations

## Setup

### Prerequisites

- Python 3.13+ 
- macOS with Homebrew
- Microphone access permissions
- OpenAI API key

### Installation

1. **Install system dependencies:**
   ```bash
   brew install portaudio
   ```

2. **Activate your virtual environment:**
   ```bash
   source ~/venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   cd live_feedback
   pip install -r requirements.txt
   ```

4. **Set up your OpenAI API key:**
   - Make sure your `.env` file contains: `OPENAI_API_KEY=your_api_key_here`

### Running the Application

1. **Start the server:**
   ```bash
   source ~/venv/bin/activate
   python app.py
   ```

2. **Open your browser:**
   - Navigate to `http://localhost:5000`
   - Grant microphone permissions when prompted

## Usage

1. **Set your system prompt**: 
   - Use the textarea in the control panel to configure how the AI should behave
   - Example: "You are a live sales-call agent that listens to a person and gives them recommendations on what to say or does research and returns results. Your human companion is trying to address the needs and create value by creating AI-centric products for businesses."

2. **Start listening**:
   - Click "Start Listening" 
   - The app will adjust for ambient noise and then begin listening
   - Speak naturally - your speech will be converted to text and sent to the AI

3. **Get recommendations**:
   - The AI will analyze your speech and conversation context
   - Real-time recommendations will appear in the conversation panel
   - Each message is timestamped for reference

4. **Manage conversation**:
   - Use "Stop Listening" to pause audio input
   - Use "Clear Conversation" to reset the chat history
   - Update the system prompt anytime to change the AI's behavior

## Example Use Cases

- **Sales Call Coaching**: Get real-time suggestions during sales conversations
- **Presentation Practice**: Receive feedback on your speaking and content
- **Interview Preparation**: Practice with AI-powered interview coaching
- **Language Learning**: Get pronunciation and conversation guidance
- **Meeting Assistant**: Receive talking points and research during discussions

## Technical Details

- **Frontend**: HTML5, CSS3, JavaScript with Socket.IO for real-time communication
- **Backend**: Flask with Socket.IO for WebSocket support
- **Speech Recognition**: Google Speech Recognition API
- **AI Integration**: OpenAI GPT models
- **Audio Processing**: PyAudio for microphone input

## Troubleshooting

### Common Issues

1. **Microphone not working**: Make sure to grant microphone permissions in your browser
2. **No audio input detected**: Check your system's default microphone settings
3. **OpenAI API errors**: Verify your API key is correct and has sufficient credits
4. **Connection issues**: Ensure the Flask server is running on port 5000

### Error Messages

- **"Error adjusting for ambient noise"**: Check microphone permissions and hardware
- **"Speech recognition error"**: Internet connection required for Google's API
- **"Error getting AI recommendation"**: Check OpenAI API key and quota

## License

MIT License 