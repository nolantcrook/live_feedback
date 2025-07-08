import os
import threading
import time
import json
from datetime import datetime
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import speech_recognition as sr
import pyaudio
from openai import OpenAI
from dotenv import load_dotenv
import queue
import sys

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Global variables
conversation_history = []
system_prompt = "You are a helpful assistant that provides live feedback and recommendations."
is_listening = False
recognizer = sr.Recognizer()
microphone = sr.Microphone()
audio_queue = queue.Queue()

class LiveFeedbackSystem:
    def __init__(self):
        self.is_running = False
        self.last_speech_time = time.time()
        self.silence_threshold = 3  # seconds of silence before processing
        self.speech_buffer = []  # Buffer to collect speech segments
        self.processing_timer = None
        self.min_speech_length = 0.5  # minimum seconds of speech before considering it valid
        
    def adjust_for_ambient_noise(self):
        """Adjust for ambient noise once at startup"""
        try:
            with microphone as source:
                socketio.emit('status', {'message': 'Adjusting for ambient noise...'})
                recognizer.adjust_for_ambient_noise(source, duration=1)
                socketio.emit('status', {'message': 'Ready to listen!'})
        except Exception as e:
            socketio.emit('error', {'message': f'Error adjusting for ambient noise: {str(e)}'})
    
    def listen_continuously(self):
        """Listen to microphone in a separate thread"""
        def callback(recognizer, audio):
            try:
                audio_queue.put(audio)
            except Exception as e:
                socketio.emit('error', {'message': f'Error in audio callback: {str(e)}'})
        
        try:
            self.adjust_for_ambient_noise()
            self.stop_listening = recognizer.listen_in_background(microphone, callback)
            
            while self.is_running:
                try:
                    # Get audio from queue with timeout
                    audio = audio_queue.get(timeout=1)
                    self.process_audio(audio)
                except queue.Empty:
                    continue
                except Exception as e:
                    socketio.emit('error', {'message': f'Error processing audio: {str(e)}'})
                    
        except Exception as e:
            socketio.emit('error', {'message': f'Error in continuous listening: {str(e)}'})
    
    def process_audio(self, audio):
        """Process audio and convert to text with intelligent pause detection"""
        try:
            # Use Google's speech recognition
            text = recognizer.recognize_google(audio)
            if text.strip():
                self.last_speech_time = time.time()
                
                print(f"Received speech: '{text}' - buffering...")
                
                # Add to speech buffer
                self.speech_buffer.append({
                    'text': text,
                    'timestamp': time.time()
                })
                
                # Emit the recognized text immediately for visual feedback
                timestamp = datetime.now().strftime("%H:%M:%S")
                socketio.emit('speech_partial', {
                    'text': text,
                    'timestamp': timestamp
                })
                
                # Cancel previous timer if exists
                if self.processing_timer:
                    self.processing_timer.cancel()
                    print(f"Cancelled previous timer, starting new {self.silence_threshold}s timer...")
                else:
                    print(f"Starting {self.silence_threshold}s timer...")
                
                # Start new timer to process after silence threshold
                self.processing_timer = threading.Timer(
                    self.silence_threshold, 
                    self.process_buffered_speech
                )
                self.processing_timer.start()
                
        except sr.UnknownValueError:
            # Speech was unintelligible
            pass
        except sr.RequestError as e:
            socketio.emit('error', {'message': f'Speech recognition error: {str(e)}'})
        except Exception as e:
            socketio.emit('error', {'message': f'Error processing speech: {str(e)}'})
    
    def process_buffered_speech(self):
        """Process the buffered speech segments as a complete thought"""
        try:
            if not self.speech_buffer:
                return
                
            # Check if we have enough speech duration
            total_duration = self.speech_buffer[-1]['timestamp'] - self.speech_buffer[0]['timestamp']
            if total_duration < self.min_speech_length and len(self.speech_buffer) == 1:
                # Too short, might be just a quick word
                print(f"Speech too short: {total_duration:.2f}s, skipping...")
                self.speech_buffer.clear()
                return
            
            # Combine all buffered speech segments
            combined_text = ' '.join([segment['text'] for segment in self.speech_buffer])
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            print(f"Processing complete speech: '{combined_text}' ({len(self.speech_buffer)} segments)")
            
            # Add to conversation history
            conversation_history.append({
                'type': 'user',
                'text': combined_text,
                'timestamp': timestamp
            })
            
            # Emit the final recognized text
            socketio.emit('speech_recognized', {
                'text': combined_text,
                'timestamp': timestamp
            })
            
            # Get AI recommendation
            self.get_ai_recommendation(combined_text)
            
            # Clear the buffer
            self.speech_buffer.clear()
            self.processing_timer = None
            
        except Exception as e:
            print(f"Error in process_buffered_speech: {e}")
            socketio.emit('error', {'message': f'Error processing speech: {str(e)}'})
    
    def get_ai_recommendation(self, latest_text):
        """Get recommendation from OpenAI API"""
        try:
            # Build context from conversation history
            context_messages = [{"role": "system", "content": system_prompt}]
            
            # Add recent conversation history (last 10 messages)
            recent_history = conversation_history[-10:]
            for msg in recent_history:
                role = "user" if msg['type'] == 'user' else "assistant"
                context_messages.append({
                    "role": role,
                    "content": msg['text']
                })
            
            # Get recommendation from OpenAI
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=context_messages,
                max_tokens=150,
                temperature=0.7
            )
            
            recommendation = response.choices[0].message.content.strip()
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Add to conversation history
            conversation_history.append({
                'type': 'assistant',
                'text': recommendation,
                'timestamp': timestamp
            })
            
            # Emit the recommendation
            socketio.emit('ai_recommendation', {
                'text': recommendation,
                'timestamp': timestamp
            })
            
        except Exception as e:
            socketio.emit('error', {'message': f'Error getting AI recommendation: {str(e)}'})
    
    def start(self):
        """Start the listening system"""
        if not self.is_running:
            self.is_running = True
            self.listening_thread = threading.Thread(target=self.listen_continuously)
            self.listening_thread.daemon = True
            self.listening_thread.start()
    
    def stop(self):
        """Stop the listening system"""
        self.is_running = False
        if hasattr(self, 'stop_listening'):
            self.stop_listening()
        
        # Cancel any pending processing timer
        if self.processing_timer:
            self.processing_timer.cancel()
            self.processing_timer = None
        
        # Process any remaining buffered speech before stopping
        if self.speech_buffer:
            self.process_buffered_speech()

# Initialize the feedback system
feedback_system = LiveFeedbackSystem()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('status', {'message': 'Connected to Live Feedback System'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('start_listening')
def handle_start_listening():
    global is_listening
    if not is_listening:
        is_listening = True
        feedback_system.start()
        emit('status', {'message': 'Started listening...'})
    else:
        emit('status', {'message': 'Already listening...'})

@socketio.on('stop_listening')
def handle_stop_listening():
    global is_listening
    if is_listening:
        is_listening = False
        feedback_system.stop()
        emit('status', {'message': 'Stopped listening'})
    else:
        emit('status', {'message': 'Not currently listening'})

@socketio.on('set_system_prompt')
def handle_set_system_prompt(data):
    global system_prompt
    system_prompt = data.get('prompt', system_prompt)
    emit('status', {'message': 'System prompt updated'})

@socketio.on('set_silence_threshold')
def handle_set_silence_threshold(data):
    threshold = data.get('threshold', 3.0)
    feedback_system.silence_threshold = threshold
    emit('status', {'message': f'Pause detection set to {threshold:.1f} seconds'})

@socketio.on('clear_conversation')
def handle_clear_conversation():
    global conversation_history
    conversation_history = []
    emit('status', {'message': 'Conversation history cleared'})

@socketio.on('get_conversation_history')
def handle_get_conversation_history():
    emit('conversation_history', {'history': conversation_history})

@socketio.on('force_process_speech')
def handle_force_process_speech():
    if feedback_system.speech_buffer:
        print("Manual processing triggered")
        feedback_system.process_buffered_speech()
        emit('status', {'message': 'Processed buffered speech'})
    else:
        emit('status', {'message': 'No speech to process'})

if __name__ == '__main__':
    # Check if OpenAI API key is available
    if not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY not found in environment variables")
        print("Please add your OpenAI API key to a .env file")
        sys.exit(1)
    
    print("Starting Live Feedback System...")
    print("Make sure you have a microphone connected and permissions are granted")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 