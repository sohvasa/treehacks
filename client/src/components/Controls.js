import React, { useEffect, useRef, useState } from 'react';
import styled from 'styled-components';
import nipplejs from 'nipplejs';
import { Icon } from '@mdi/react';
import { mdiMicrophone, mdiMicrophoneOff } from '@mdi/js';

const ControlsContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 32px;
  touch-action: none;
  user-select: none;
  -webkit-user-select: none;
  -webkit-touch-callout: none;
`;

const JoystickContainer = styled.div`
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  touch-action: none;
`;

const JoystickZone = styled.div`
  width: 120px;
  height: 120px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 50%;
  position: relative;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
  touch-action: none;

  &:active {
    background: rgba(255, 255, 255, 0.08);
  }

  &::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 6px;
    height: 6px;
    background: rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    transform: translate(-50%, -50%);
  }
`;

  


const ControlButton = styled.button`
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: ${props => props.active ? '#3B82F6' : 'rgba(255, 255, 255, 0.05)'};
  border: 1px solid ${props => props.active ? '#60A5FA' : 'rgba(255, 255, 255, 0.1)'};
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s ease;
  touch-action: manipulation;
  
  &:hover {
    background: ${props => props.active ? '#4F8EF6' : 'rgba(255, 255, 255, 0.08)'};
    transform: translateY(-2px);
  }
  
  &:active {
    transform: translateY(0);
  }
  
  svg {
    color: ${props => props.active ? '#FFFFFF' : 'rgba(255, 255, 255, 0.9)'};
    transition: all 0.3s ease;
  }
`;

const Controls = ({ onJoystickMove, onMicToggle }) => {
  const joystickRef = useRef(null);
  const joystickInstanceRef = useRef(null);
  const [isMicActive, setIsMicActive] = useState(false);
  const [status, setStatus] = useState('');
  const mediaRecorder = useRef(null);
  const audioChunks = useRef([]);

  useEffect(() => {
    console.log(status)
  }, [status]);

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
      setIsMicActive(true);
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
      setIsMicActive(false);
      setStatus('Processing...');
    }
  };
  
  // Add function to send commands to Raspberry Pi
  const sendMoveCommand = async (direction, speed) => {
    console.log('sending move command')
    console.log(direction, speed)
    try {
      const response = await fetch('http://10.19.179.61:5000/move', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ direction, speed })
      });

      if (!response.ok) {
        throw new Error('Failed to send movement command');
      }
    } catch (error) {
      console.error('Movement command error:', error);
      setStatus('Error controlling robot');
    }
  };

  useEffect(() => {
    const preventScroll = (e) => {
      e.preventDefault();
    };

    console.log('joystickRef.current', joystickRef.current)

    if (joystickRef.current) {
      joystickRef.current.addEventListener('touchmove', preventScroll, { passive: false });
      
      const options = {
        zone: joystickRef.current,
        mode: 'static',
        position: { left: '50%', top: '50%' },
        color: 'rgba(255, 255, 255, 0.7)',
        size: 90,
        lockX: false,
        lockY: false,
      };

      joystickInstanceRef.current = nipplejs.create(options);

      let moveInterval = null;
      let currentVector = { x: 0, y: 0 };

      joystickInstanceRef.current.on('move', (evt, data) => {
        // Update current vector
        currentVector = {
          x: data.vector.x,
          y: data.vector.y
        };

        console.log('currentVector', currentVector)

        // Start interval if not already started
        if (!moveInterval) {
          moveInterval = setInterval(() => {
            // Calculate direction and speed based on vector
            const x = currentVector.x;
            const y = -currentVector.y; // Invert Y since joystick Y is inverted
            
            // Calculate speed (0-100) based on distance from center
            const speed = Math.min(Math.sqrt(x * x + y * y) * 100, 100);
            
            // Determine direction based on vector components and speed
            let direction;
            if (speed <= 10) {
              direction = 'center';
            } else if (Math.abs(x) > Math.abs(y)) {
              // Horizontal movement is stronger
              direction = x > 0 ? 'right' : 'left';
            } else {
              // Vertical movement is stronger
              direction = y > 0 ? 'forward' : 'backward';
            }

            // Send movement command
            sendMoveCommand(direction, Math.round(speed));
            console.log('sending move command:', direction, Math.round(speed));
          }, 100); // Send commands every 100ms
        }
      });

      joystickInstanceRef.current.on('end', () => {
        // Clear interval and stop movement
        if (moveInterval) {
          clearInterval(moveInterval);
          moveInterval = null;
        }
        currentVector = { x: 0, y: 0 };
        sendMoveCommand('stop', 0);
      });
    }

    return () => {
      if (joystickRef.current) {
        joystickRef.current.removeEventListener('touchmove', preventScroll);
      }
      if (joystickInstanceRef.current) {
        joystickInstanceRef.current.destroy();
      }
    };
  }, []);

  const handleMicToggle = () => {
    console.log('hi')
    setIsMicActive(!isMicActive);
    
    if (isMicActive) {
      stopRecording();
      onMicToggle(!isMicActive);
    } else {
      startRecording();
      onMicToggle(!isMicActive);
    }
  };

  return (
    <ControlsContainer>
      <JoystickContainer>
        <JoystickZone ref={joystickRef} />
      </JoystickContainer>
      <ControlButton 
        active={isMicActive} 
        onClick={handleMicToggle}
        aria-label="Toggle microphone"
      >
        <Icon 
          path={isMicActive ? mdiMicrophone : mdiMicrophoneOff} 
          size={1.2}
        />
      </ControlButton>
    </ControlsContainer>
  );
};

export default Controls;
