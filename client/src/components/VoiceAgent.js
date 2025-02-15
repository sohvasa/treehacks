import React, { useState, useRef } from 'react';
import styled from 'styled-components';
import { Icon } from '@mdi/react';
import { mdiMicrophone, mdiMicrophoneOff, mdiLoading } from '@mdi/js';
import io from 'socket.io-client';

const VoiceContainer = styled.div`
  position: fixed;
  bottom: 32px;
  right: 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
`;

const RecordButton = styled.button`
  width: 64px;
  height: 64px;
  border-radius: 32px;
  background: ${props => props.isRecording ? '#EF4444' : 'rgba(255, 255, 255, 0.1)'};
  border: none;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    transform: scale(1.05);
    background: ${props => props.isRecording ? '#DC2626' : 'rgba(255, 255, 255, 0.15)'};
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  svg {
    color: white;
    transition: all 0.3s ease;
  }
`;

const StatusText = styled.div`
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  text-align: center;
  max-width: 200px;
`;

const VoiceAgent = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [status, setStatus] = useState('');
  const mediaRecorder = useRef(null);
  const socket = useRef(null);
  const chunks = useRef([]);

  const initializeSocket = () => {
    if (!socket.current) {
      socket.current = io('http://localhost:5000');
      
      socket.current.on('connect', () => {
        console.log('Connected to server');
      });

      socket.current.on('voice_response', (response) => {
        if (response.error) {
          setStatus('Error: ' + response.error);
        } else {
          setStatus('Task recorded and notification sent!');
        }
        setIsProcessing(false);
      });
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder.current = new MediaRecorder(stream);
      chunks.current = [];

      mediaRecorder.current.ondataavailable = (e) => {
        chunks.current.push(e.data);
      };

      mediaRecorder.current.onstop = async () => {
        const audioBlob = new Blob(chunks.current, { type: 'audio/wav' });
        const reader = new FileReader();
        
        reader.onloadend = () => {
          setIsProcessing(true);
          setStatus('Processing audio...');
          socket.current.emit('voice_data', { audio: reader.result });
        };
        
        reader.readAsDataURL(audioBlob);
      };

      mediaRecorder.current.start();
      setIsRecording(true);
      setStatus('Recording... Speak about your completed task');
      initializeSocket();
    } catch (err) {
      console.error('Error accessing microphone:', err);
      setStatus('Error: Could not access microphone');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder.current && mediaRecorder.current.state !== 'inactive') {
      mediaRecorder.current.stop();
      mediaRecorder.current.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
      setStatus('Processing your recording...');
    }
  };

  const handleClick = () => {
    if (!isRecording) {
      startRecording();
    } else {
      stopRecording();
    }
  };

  return (
    <VoiceContainer>
      <StatusText>{status}</StatusText>
      <RecordButton
        onClick={handleClick}
        isRecording={isRecording}
        disabled={isProcessing}
        aria-label={isRecording ? 'Stop recording' : 'Start recording'}
      >
        <Icon
          path={isProcessing ? mdiLoading : (isRecording ? mdiMicrophoneOff : mdiMicrophone)}
          size={1.5}
          spin={isProcessing}
        />
      </RecordButton>
    </VoiceContainer>
  );
};

export default VoiceAgent;
