#!/usr/bin/env python3
"""
Mouse and Keyboard Macro Recorder with Flask Web Interface
A comprehensive application for recording and replaying mouse/keyboard actions
"""

import json
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import pynput
from pynput import mouse, keyboard
from flask import Flask, render_template_string, request, jsonify, send_file
import signal
import sys

class MacroRecorder:
    """Handles recording of mouse and keyboard events"""
    
    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        self.recording = False
        self.start_time = None
        self.mouse_listener = None
        self.keyboard_listener = None
    
    def start_recording(self):
        """Start recording mouse and keyboard events"""
        if self.recording:
            return False
        
        self.events.clear()
        self.recording = True
        self.start_time = time.time()
        
        # Start mouse listener
        self.mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click,
            on_move=self._on_mouse_move,
            on_scroll=self._on_mouse_scroll
        )
        
        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        
        self.mouse_listener.start()
        self.keyboard_listener.start()
        
        print("Recording started...")
        return True
    
    def stop_recording(self):
        """Stop recording events"""
        if not self.recording:
            return False
        
        self.recording = False
        
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        
        print(f"Recording stopped. Captured {len(self.events)} events.")
        return True
    
    def get_events(self):
        """Get current recorded events"""
        return self.events.copy()
    
    def _get_timestamp(self):
        """Get relative timestamp from start of recording"""
        return time.time() - self.start_time if self.start_time else 0
    
    def _on_mouse_click(self, x, y, button, pressed):
        """Handle mouse click events"""
        if self.recording:
            self.events.append({
                'type': 'mouse_click',
                'timestamp': self._get_timestamp(),
                'x': x,
                'y': y,
                'button': str(button),
                'pressed': pressed
            })
    
    def _on_mouse_move(self, x, y):
        """Handle mouse move events (throttled)"""
        if self.recording:
            # Only record significant movements to avoid too many events
            if not self.events or self.events[-1]['type'] != 'mouse_move' or \
               self._get_timestamp() - self.events[-1]['timestamp'] > 0.1:
                self.events.append({
                    'type': 'mouse_move',
                    'timestamp': self._get_timestamp(),
                    'x': x,
                    'y': y
                })
    
    def _on_mouse_scroll(self, x, y, dx, dy):
        """Handle mouse scroll events"""
        if self.recording:
            self.events.append({
                'type': 'mouse_scroll',
                'timestamp': self._get_timestamp(),
                'x': x,
                'y': y,
                'dx': dx,
                'dy': dy
            })
    
    def _on_key_press(self, key):
        """Handle key press events"""
        if self.recording:
            try:
                key_char = key.char
            except AttributeError:
                key_char = str(key)
            
            self.events.append({
                'type': 'key_press',
                'timestamp': self._get_timestamp(),
                'key': key_char
            })
    
    def _on_key_release(self, key):
        """Handle key release events"""
        if self.recording:
            try:
                key_char = key.char
            except AttributeError:
                key_char = str(key)
            
            self.events.append({
                'type': 'key_release',
                'timestamp': self._get_timestamp(),
                'key': key_char
            })

class MacroPlayer:
    """Handles playback of recorded macros"""
    
    def __init__(self):
        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()
        self.playing = False
        self.loop_playing = False
        self.play_thread = None
        self.stop_listener = None
    
    def play_macro(self, events: List[Dict[str, Any]], speed: float = 1.0, repeat: int = 1):
        """Play back recorded events"""
        if self.playing:
            return False
        
        self.playing = True
        self.play_thread = threading.Thread(
            target=self._play_events,
            args=(events, speed, repeat)
        )
        self.play_thread.start()
        return True
    
    def play_macro_loop(self, events: List[Dict[str, Any]], speed: float = 1.0, delay_between_loops: float = 1.0):
        """Play back recorded events in an infinite loop until Ctrl+S is pressed"""
        if self.playing or self.loop_playing:
            return False
        
        self.loop_playing = True
        self.playing = True
        
        # Start keyboard listener for Ctrl+S
        self._start_stop_listener()
        
        self.play_thread = threading.Thread(
            target=self._play_events_loop,
            args=(events, speed, delay_between_loops)
        )
        self.play_thread.start()
        return True
    
    def _start_stop_listener(self):
        """Start listening for Ctrl+S to stop loop playback"""
        def on_hotkey():
            print("🛑 Stop hotkey detected!")
            self.stop_loop_playback()
        
        try:
            # Try to use GlobalHotKeys for better hotkey detection
            from pynput.keyboard import GlobalHotKeys
            self.stop_listener = GlobalHotKeys({
                '<ctrl>+s': on_hotkey,
                '<esc>': on_hotkey
            })
            self.stop_listener.start()
            print("🎹 Hotkey listener started: Ctrl+S or ESC to stop loop")
        except Exception as e:
            print(f"⚠️ Could not start hotkey listener: {e}")
            # Fallback: just use a simple keyboard listener
            def on_key_press(key):
                try:
                    if key == keyboard.Key.esc:
                        on_hotkey()
                except AttributeError:
                    pass
            
            self.stop_listener = keyboard.Listener(on_press=on_key_press)
            self.stop_listener.start()
            print("🎹 Basic keyboard listener started: ESC to stop loop")
    
    def stop_loop_playback(self):
        """Stop loop playback"""
        self.loop_playing = False
        self.playing = False
        if self.stop_listener:
            self.stop_listener.stop()
        if self.play_thread:
            self.play_thread.join()
        print("🛑 Loop playback stopped by user (Ctrl+S pressed)")
    
    def _play_events_loop(self, events: List[Dict[str, Any]], speed: float, delay_between_loops: float):
        """Internal method to play events in a loop"""
        loop_count = 0
        try:
            while self.loop_playing and self.playing:
                loop_count += 1
                print(f"🔄 Loop iteration #{loop_count}")
                
                last_timestamp = 0
                
                for event in events:
                    if not self.loop_playing or not self.playing:
                        break
                    
                    # Wait for the appropriate time
                    wait_time = (event['timestamp'] - last_timestamp) / speed
                    if wait_time > 0:
                        time.sleep(wait_time)
                    
                    self._execute_event(event)
                    last_timestamp = event['timestamp']
                
                # Wait between loop iterations
                if self.loop_playing and self.playing and delay_between_loops > 0:
                    time.sleep(delay_between_loops)
        
        except Exception as e:
            print(f"Loop playback error: {e}")
        finally:
            self.loop_playing = False
            self.playing = False
            if self.stop_listener:
                self.stop_listener.stop()
            print(f"✅ Loop playback finished after {loop_count} iterations")
    
    def stop_playback(self):
        """Stop current playback"""
        self.playing = False
        self.loop_playing = False
        if self.stop_listener:
            self.stop_listener.stop()
        if self.play_thread:
            self.play_thread.join()
    
    def _play_events(self, events: List[Dict[str, Any]], speed: float, repeat: int):
        """Internal method to play events"""
        try:
            for _ in range(repeat):
                if not self.playing:
                    break
                
                last_timestamp = 0
                
                for event in events:
                    if not self.playing:
                        break
                    
                    # Wait for the appropriate time
                    wait_time = (event['timestamp'] - last_timestamp) / speed
                    if wait_time > 0:
                        time.sleep(wait_time)
                    
                    self._execute_event(event)
                    last_timestamp = event['timestamp']
        
        except Exception as e:
            print(f"Playback error: {e}")
        finally:
            self.playing = False
    
    def _execute_event(self, event: Dict[str, Any]):
        """Execute a single event"""
        try:
            if event['type'] == 'mouse_click':
                self.mouse_controller.position = (event['x'], event['y'])
                button = getattr(mouse.Button, event['button'].split('.')[-1])
                if event['pressed']:
                    self.mouse_controller.press(button)
                else:
                    self.mouse_controller.release(button)
            
            elif event['type'] == 'mouse_move':
                self.mouse_controller.position = (event['x'], event['y'])
            
            elif event['type'] == 'mouse_scroll':
                self.mouse_controller.position = (event['x'], event['y'])
                self.mouse_controller.scroll(event['dx'], event['dy'])
            
            elif event['type'] == 'key_press':
                key = self._parse_key(event['key'])
                self.keyboard_controller.press(key)
            
            elif event['type'] == 'key_release':
                key = self._parse_key(event['key'])
                self.keyboard_controller.release(key)
        
        except Exception as e:
            print(f"Error executing event: {e}")
    
    def _parse_key(self, key_str: str):
        """Parse key string back to pynput key"""
        if len(key_str) == 1:
            return key_str
        
        # Handle special keys
        if key_str.startswith('Key.'):
            key_name = key_str.split('.')[-1]
            return getattr(keyboard.Key, key_name, key_str)
        
        return key_str

class MacroManager:
    """Manages saving and loading of macros"""
    
    def __init__(self, macros_dir: str = "macros"):
        self.macros_dir = Path(macros_dir)
        self.macros_dir.mkdir(exist_ok=True)
    
    def save_macro(self, name: str, events: List[Dict[str, Any]], description: str = ""):
        """Save macro to file"""
        macro_data = {
            'name': name,
            'description': description,
            'created': datetime.now().isoformat(),
            'events': events
        }
        
        filename = f"{name}.json"
        filepath = self.macros_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(macro_data, f, indent=2)
        
        return str(filepath)
    
    def auto_save_macro(self, events: List[Dict[str, Any]]) -> str:
        """Automatically save macro with timestamp-based name"""
        if not events:
            return ""
        
        # Generate automatic name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"macro_{timestamp}"
        
        # Add some context based on events
        mouse_clicks = sum(1 for e in events if e['type'] == 'mouse_click' and e['pressed'])
        key_presses = sum(1 for e in events if e['type'] == 'key_press')
        duration = events[-1]['timestamp'] - events[0]['timestamp'] if len(events) > 1 else 0
        
        description = f"Auto-saved macro: {mouse_clicks} clicks, {key_presses} key presses, {duration:.1f}s duration"
        
        return self.save_macro(name, events, description)
    
    def load_macro(self, name: str) -> Optional[Dict[str, Any]]:
        """Load macro from file"""
        filename = f"{name}.json"
        filepath = self.macros_dir / filename
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def list_macros(self) -> List[Dict[str, str]]:
        """List all available macros"""
        macros = []
        for filepath in self.macros_dir.glob("*.json"):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    macros.append({
                        'name': data.get('name', filepath.stem),
                        'description': data.get('description', ''),
                        'created': data.get('created', 'Unknown'),
                        'events_count': len(data.get('events', []))
                    })
            except Exception as e:
                print(f"Error reading macro {filepath}: {e}")
        
        return macros
    
    def delete_macro(self, name: str) -> bool:
        """Delete a macro file"""
        filename = f"{name}.json"
        filepath = self.macros_dir / filename
        
        if filepath.exists():
            filepath.unlink()
            return True
        return False

# Flask Web Application
app = Flask(__name__)

# Global instances
recorder = MacroRecorder()
player = MacroPlayer()
manager = MacroManager()

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Macro Recorder</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .section {
            margin-bottom: 30px;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 8px;
        }
        .section h2 {
            margin-top: 0;
            color: #555;
        }
        .controls {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        button {
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s;
        }
        .btn-primary {
            background-color: #007bff;
            color: white;
        }
        .btn-primary:hover {
            background-color: #0056b3;
        }
        .btn-danger {
            background-color: #dc3545;
            color: white;
        }
        .btn-danger:hover {
            background-color: #c82333;
        }
        .btn-success {
            background-color: #28a745;
            color: white;
        }
        .btn-success:hover {
            background-color: #218838;
        }
        .btn-warning {
            background-color: #ffc107;
            color: black;
        }
        .btn-warning:hover {
            background-color: #e0a800;
        }
        .status {
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            font-weight: bold;
        }
        .status.recording {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .status.stopped {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .status.playing {
            background-color: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        input, select {
            padding: 8px;
            margin: 5px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .macro-list {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .macro-item {
            padding: 15px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: between;
            align-items: center;
        }
        .macro-item:last-child {
            border-bottom: none;
        }
        .macro-info {
            flex-grow: 1;
        }
        .macro-name {
            font-weight: bold;
            color: #333;
        }
        .macro-details {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        .macro-actions {
            display: flex;
            gap: 5px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        .hidden {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🖱️ Macro Recorder & Player</h1>
        
        <!-- Recording Section -->
        <div class="section">
            <h2>📹 Recording</h2>
            <div id="status" class="status stopped">Ready to record</div>
            <div class="controls">
                <button id="startBtn" class="btn-success" onclick="startRecording()">▶️ Start Recording</button>
                <button id="stopBtn" class="btn-danger" onclick="stopRecording()" disabled>⏹️ Stop Recording</button>
                <button id="clearBtn" class="btn-warning" onclick="clearRecording()">🗑️ Clear</button>
            </div>
            <div id="eventCount">Events recorded: 0</div>
            <div id="autoSaveStatus" class="hidden" style="margin-top: 10px; padding: 8px; background-color: #d1ecf1; color: #0c5460; border-radius: 4px;">
                ✅ Macro automatically saved!
            </div>
        </div>
        
        <!-- Manual Save Section (Optional) -->
        <div class="section" id="saveSection" style="display: none;">
            <h2>💾 Manual Save (Optional)</h2>
            <p style="color: #666; font-size: 14px;">Macros are auto-saved, but you can rename them here if needed:</p>
            <div class="form-group">
                <label for="macroName">Custom Name:</label>
                <input type="text" id="macroName" placeholder="Enter custom name (optional)">
            </div>
            <div class="form-group">
                <label for="macroDescription">Description:</label>
                <input type="text" id="macroDescription" placeholder="Enter description (optional)">
            </div>
            <button class="btn-primary" onclick="saveMacro()">💾 Save with Custom Name</button>
        </div>
        
        <!-- Playback Section -->
        <div class="section">
            <h2>▶️ Playback</h2>
            <div class="controls">
                <label for="speedSelect">Speed:</label>
                <select id="speedSelect">
                    <option value="0.5">0.5x (Slow)</option>
                    <option value="1.0" selected>1.0x (Normal)</option>
                    <option value="1.5">1.5x (Fast)</option>
                    <option value="2.0">2.0x (Very Fast)</option>
                </select>
                
                <label for="repeatCount">Repeat:</label>
                <input type="number" id="repeatCount" value="1" min="1" max="100" style="width: 60px;">
                
                <label for="loopDelay">Loop Delay (s):</label>
                <input type="number" id="loopDelay" value="1" min="0" max="10" step="0.5" style="width: 70px;">
                
                <button class="btn-primary" onclick="playCurrentMacro()">▶️ Play Current</button>
                <button class="btn-success" onclick="playCurrentMacroLoop()">🔄 Loop Current</button>
                <button class="btn-danger" onclick="stopPlayback()">⏹️ Stop Playback</button>
            </div>
            <div id="loopStatus" class="hidden" style="margin-top: 10px; padding: 8px; background-color: #fff3cd; color: #856404; border-radius: 4px;">
                🔄 Loop playing... Press <strong>Ctrl+S</strong> or <strong>ESC</strong> to stop
            </div>
        </div>
        
        <!-- Macro Library -->
        <div class="section">
            <h2>📚 Macro Library</h2>
            <button class="btn-primary" onclick="refreshMacros()">🔄 Refresh</button>
            <div id="macroList" class="macro-list">
                <!-- Macros will be loaded here -->
            </div>
        </div>
    </div>

    <script>
        let currentEvents = [];
        let recordingInterval;
        
        // Start recording
        async function startRecording() {
            const response = await fetch('/start_recording', { method: 'POST' });
            const result = await response.json();
            
            if (result.success) {
                document.getElementById('status').textContent = 'Recording... Click Stop when done';
                document.getElementById('status').className = 'status recording';
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                
                // Start polling for event count
                recordingInterval = setInterval(updateEventCount, 500);
            }
        }
        
        // Stop recording
        async function stopRecording() {
            const response = await fetch('/stop_recording', { method: 'POST' });
            const result = await response.json();
            
            if (result.success) {
                currentEvents = result.events;
                const eventCount = result.events.length;
                
                if (result.auto_saved && eventCount > 0) {
                    document.getElementById('status').textContent = `✅ Recording stopped & auto-saved! ${eventCount} events captured`;
                    document.getElementById('status').className = 'status recording';
                    
                    // Show auto-save confirmation
                    const autoSaveStatus = document.getElementById('autoSaveStatus');
                    autoSaveStatus.classList.remove('hidden');
                    setTimeout(() => {
                        autoSaveStatus.classList.add('hidden');
                    }, 5000);
                    
                    // Refresh macro list to show the new auto-saved macro
                    refreshMacros();
                } else {
                    document.getElementById('status').textContent = `Recording stopped. ${eventCount} events captured`;
                    document.getElementById('status').className = 'status stopped';
                }
                
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
                
                // Show optional manual save section only if there are events
                if (eventCount > 0) {
                    document.getElementById('saveSection').style.display = 'block';
                }
                
                clearInterval(recordingInterval);
                updateEventCount();
            }
        }
        
        // Clear current recording
        function clearRecording() {
            currentEvents = [];
            document.getElementById('eventCount').textContent = 'Events recorded: 0';
            document.getElementById('saveSection').style.display = 'none';
            document.getElementById('autoSaveStatus').classList.add('hidden');
            document.getElementById('macroName').value = '';
            document.getElementById('macroDescription').value = '';
        }
        
        // Update event count
        async function updateEventCount() {
            try {
                const response = await fetch('/get_event_count');
                const result = await response.json();
                document.getElementById('eventCount').textContent = `Events recorded: ${result.count}`;
            } catch (error) {
                console.error('Error updating event count:', error);
            }
        }
        
        // Save macro with custom name (optional)
        async function saveMacro() {
            const name = document.getElementById('macroName').value.trim();
            const description = document.getElementById('macroDescription').value.trim();
            
            if (!name) {
                alert('Please enter a custom macro name');
                return;
            }
            
            const response = await fetch('/save_macro', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name,
                    description: description,
                    events: currentEvents
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                alert('Custom macro saved successfully!');
                document.getElementById('macroName').value = '';
                document.getElementById('macroDescription').value = '';
                refreshMacros();
            } else {
                alert('Error saving macro: ' + result.error);
            }
        }
        
        // Play current macro
        async function playCurrentMacro() {
            if (currentEvents.length === 0) {
                alert('No events to play. Record a macro first.');
                return;
            }
            
            const speed = parseFloat(document.getElementById('speedSelect').value);
            const repeat = parseInt(document.getElementById('repeatCount').value);
            
            const response = await fetch('/play_macro', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    events: currentEvents,
                    speed: speed,
                    repeat: repeat
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                document.getElementById('status').textContent = 'Playing macro...';
                document.getElementById('status').className = 'status playing';
            } else {
                alert('Error playing macro: ' + result.error);
            }
        }
        
        // Play current macro in loop
        async function playCurrentMacroLoop() {
            if (currentEvents.length === 0) {
                alert('No events to play. Record a macro first.');
                return;
            }
            
            const speed = parseFloat(document.getElementById('speedSelect').value);
            const delay = parseFloat(document.getElementById('loopDelay').value);
            
            const response = await fetch('/play_macro_loop', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    events: currentEvents,
                    speed: speed,
                    delay: delay
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                document.getElementById('status').textContent = 'Playing macro in loop... Press Ctrl+S to stop';
                document.getElementById('status').className = 'status playing';
                document.getElementById('loopStatus').classList.remove('hidden');
            } else {
                alert('Error playing macro loop: ' + result.error);
            }
        }
        
        // Stop playback
        async function stopPlayback() {
            const response = await fetch('/stop_playback', { method: 'POST' });
            const result = await response.json();
            
            if (result.success) {
                document.getElementById('status').textContent = 'Playback stopped';
                document.getElementById('status').className = 'status stopped';
                document.getElementById('loopStatus').classList.add('hidden');
            }
        }
        
        // Play saved macro
        async function playSavedMacro(name) {
            const speed = parseFloat(document.getElementById('speedSelect').value);
            const repeat = parseInt(document.getElementById('repeatCount').value);
            
            const response = await fetch('/play_saved_macro', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name,
                    speed: speed,
                    repeat: repeat
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                document.getElementById('status').textContent = `Playing macro: ${name}`;
                document.getElementById('status').className = 'status playing';
            } else {
                alert('Error playing macro: ' + result.error);
            }
        }
        
        // Delete macro
        async function deleteMacro(name) {
            if (!confirm(`Are you sure you want to delete the macro "${name}"?`)) {
                return;
            }
            
            const response = await fetch('/delete_macro', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name })
            });
            
            const result = await response.json();
            
            if (result.success) {
                refreshMacros();
            } else {
                alert('Error deleting macro: ' + result.error);
            }
        }
        
        // Refresh macro list
        async function refreshMacros() {
            const response = await fetch('/list_macros');
            const result = await response.json();
            
            const macroList = document.getElementById('macroList');
            macroList.innerHTML = '';
            
            if (result.macros.length === 0) {
                macroList.innerHTML = '<div class="macro-item">No saved macros found.</div>';
                return;
            }
            
            result.macros.forEach(macro => {
                const item = document.createElement('div');
                item.className = 'macro-item';
                item.innerHTML = `
                    <div class="macro-info">
                        <div class="macro-name">${macro.name}</div>
                        <div class="macro-details">
                            ${macro.description ? macro.description + ' • ' : ''}
                            ${macro.events_count} events • Created: ${new Date(macro.created).toLocaleDateString()}
                        </div>
                    </div>
                    <div class="macro-actions">
                        <button class="btn-primary" onclick="playSavedMacro('${macro.name}')">▶️ Play</button>
                        <button class="btn-success" onclick="loopPlaySavedMacro('${macro.name}')">🔄 Loop</button>
                        <button class="btn-danger" onclick="deleteMacro('${macro.name}')">🗑️</button>
                    </div>
                `;
                macroList.appendChild(item);
            });
        }
        
        // Load macros on page load
        window.onload = function() {
            refreshMacros();
        };
    </script>
</body>
</html>
"""

# Flask Routes
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/start_recording', methods=['POST'])
def start_recording():
    success = recorder.start_recording()
    return jsonify({'success': success})

@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    success = recorder.stop_recording()
    
    if success and recorder.events:
        # Auto-save the macro
        try:
            filepath = manager.auto_save_macro(recorder.events)
            print(f"✅ Macro auto-saved to: {filepath}")
        except Exception as e:
            print(f"❌ Auto-save failed: {e}")
    
    return jsonify({
        'success': success,
        'events': recorder.events if success else [],
        'auto_saved': success and len(recorder.events) > 0
    })

@app.route('/get_event_count')
def get_event_count():
    return jsonify({'count': len(recorder.events)})

@app.route('/save_macro', methods=['POST'])
def save_macro():
    try:
        data = request.json
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        events = data.get('events', [])
        
        if not name:
            return jsonify({'success': False, 'error': 'Name is required'})
        
        filepath = manager.save_macro(name, events, description)
        return jsonify({'success': True, 'filepath': filepath})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/play_macro', methods=['POST'])
def play_macro():
    try:
        data = request.json
        events = data.get('events', [])
        speed = data.get('speed', 1.0)
        repeat = data.get('repeat', 1)
        
        success = player.play_macro(events, speed, repeat)
        return jsonify({'success': success})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/play_saved_macro', methods=['POST'])
def play_saved_macro():
    try:
        data = request.json
        name = data.get('name', '')
        speed = data.get('speed', 1.0)
        repeat = data.get('repeat', 1)
        
        macro_data = manager.load_macro(name)
        if not macro_data:
            return jsonify({'success': False, 'error': 'Macro not found'})
        
        success = player.play_macro(macro_data['events'], speed, repeat)
        return jsonify({'success': success})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/play_macro_loop', methods=['POST'])
def play_macro_loop():
    try:
        data = request.json
        events = data.get('events', [])
        speed = data.get('speed', 1.0)
        delay = data.get('delay', 1.0)
        
        success = player.play_macro_loop(events, speed, delay)
        return jsonify({'success': success})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/stop_playback', methods=['POST'])
def stop_playback():
    player.stop_playback()
    return jsonify({'success': True})

@app.route('/list_macros')
def list_macros():
    macros = manager.list_macros()
    return jsonify({'macros': macros})

@app.route('/delete_macro', methods=['POST'])
def delete_macro():
    try:
        data = request.json
        name = data.get('name', '')
        
        success = manager.delete_macro(name)
        return jsonify({'success': success})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\nShutting down gracefully...")
    recorder.stop_recording()
    player.stop_playback()
    sys.exit(0)

if __name__ == '__main__':
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🚀 Starting Macro Recorder Application")
    print("📝 Make sure to install required packages:")
    print("   pip install flask pynput")
    print()
    print("🌐 Open your browser and go to: http://localhost:5000")
    print("⚠️  Note: This app requires appropriate permissions to record mouse/keyboard")
    print("✨ NEW: Macros are now AUTO-SAVED automatically when you stop recording!")
    print("📁 Auto-saved macros use timestamp names like: macro_20250702_143045")
    print("🔄 NEW: Loop Play feature - continuously repeat macros until Ctrl+S is pressed!")
    print("⌨️  Use Ctrl+S or ESC to stop loop playback")
    print()
    
    # Run Flask app
    app.run(debug=False, host='0.0.0.0', port=5000)