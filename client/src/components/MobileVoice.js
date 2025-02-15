import React, { useState, useRef } from 'react';
import styled from 'styled-components';
import { Icon } from '@mdi/react';
import { mdiMicrophone, mdiMicrophoneOff } from '@mdi/js';

const MicButton = styled.button`
  position: fixed;
  bottom: 100px;
  right: 20px;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: ${props => props.$isRecording ? '#ff4444' : '#3B82F6'};
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
  z-index: 1000;

  &:active {
    transform: scale(0.95);
  }

  svg {
    color: white;
  }
`;

const StatusText = styled.div`
  position: fixed;
  bottom: 170px;
  right: 20px;
  color: white;
  font-size: 14px;
  text-align: right;
  background: rgba(0, 0, 0, 0.5);
  padding: 8px 12px;
  border-radius: 8px;
  z-index: 1000;
`;

const MobileVoice = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [status, setStatus] = useState('');
  const mediaRecorder = useRef(null);
  const audioChunks = useRef([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder.current = new MediaRecorder(stream);
      audioChunks.current = [];

      mediaRecorder.current.ondataavailable = (event) => {
        audioChunks.current.push(event.data);
      };

      mediaRecorder.current.onstop = async () => {
        const audioBlob = new Blob(audioChunks.current, { type: 'audio/wav' });
        const reader = new FileReader();
        
        reader.onloadend = async () => {
          try {
            console.log('handle_voice called')
            setStatus('Sending to server...');
            const response = await fetch('http://localhost:5001/handle_voice', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
              },
              body: JSON.stringify({
                audio: reader.result
              })
            });

            if (!response.ok) {
              throw new Error('Server response was not ok');
            }

            const data = await response.json();
            if (data.success) {
              setStatus('Message sent to your phone!');
            } else {
              setStatus('Error: ' + (data.error || 'Failed to process'));
            }
          } catch (error) {
            setStatus('Error sending to server');
            console.error('Error:', error);
          }
        };

        reader.readAsDataURL(audioBlob);
      };

      mediaRecorder.current.start();
      setIsRecording(true);
      setStatus('Recording...');
    } catch (err) {
      console.error('Error accessing microphone:', err);
      setStatus('Error accessing microphone');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder.current && mediaRecorder.current.state !== 'inactive') {
      mediaRecorder.current.stop();
      mediaRecorder.current.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
      setStatus('Processing...');
    }
  };

  const handleMicClick = () => {
    if (!isRecording) {
      startRecording();
    } else {
      stopRecording();
    }
  };

  return (
    <>
      {status && <StatusText>{status}</StatusText>}
      <MicButton 
        onClick={handleMicClick}
        $isRecording={isRecording}
        aria-label={isRecording ? 'Stop recording' : 'Start recording'}
      >
        <Icon 
          path={isRecording ? mdiMicrophoneOff : mdiMicrophone}
          size={1.2}
        />
      </MicButton>
    </>
  );
};

export default MobileVoice;
