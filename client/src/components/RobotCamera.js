import React, { useEffect, useRef, useState } from 'react';
import styled from 'styled-components';

const CameraContainer = styled.div`
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
  background: #000000;
`;

const CameraFeed = styled.video`
  width: 100%;
  height: 100%;
  object-fit: cover;
`;

const CameraOverlay = styled.div`
  position: absolute;
  top: 24px;
  left: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
`;

const StatusBadge = styled.div`
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  padding: 8px 12px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const StatusDot = styled.div`
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: ${props => props.active ? '#10B981' : '#F43F5E'};
  box-shadow: 0 0 8px ${props => props.active ? 'rgba(16, 185, 129, 0.6)' : 'rgba(244, 63, 94, 0.6)'};
`;

const StatusText = styled.span`
  color: rgba(255, 255, 255, 0.9);
  font-size: 13px;
  font-weight: 500;
`;

// Subtle grid overlay for a more technical feel
const GridOverlay = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
`;

// Corner accents for a more technical look
const CornerAccent = styled.div`
  position: absolute;
  width: 40px;
  height: 40px;
  border-style: solid;
  border-color: rgba(255, 255, 255, 0.1);
  border-width: ${props => props.position};
  ${props => props.corner};
`;

const RobotCamera = () => {
  const videoRef = useRef(null);
  const [isActive, setIsActive] = useState(false);

  useEffect(() => {
    const initializeCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          setIsActive(true);
        }
      } catch (error) {
        console.error('Error accessing camera:', error);
        setIsActive(false);
      }
    };

    initializeCamera();
    return () => {
      if (videoRef.current?.srcObject) {
        videoRef.current.srcObject.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  return (
    <CameraContainer>
      <CameraFeed ref={videoRef} autoPlay playsInline />
      <GridOverlay />
      <CameraOverlay>
        <StatusBadge>
          <StatusDot active={isActive} />
          <StatusText>{isActive ? 'Connected' : 'Disconnected'}</StatusText>
        </StatusBadge>
      </CameraOverlay>
      <CornerAccent position="2px 0 0 2px" corner="top: 24px; left: 24px;" />
      <CornerAccent position="2px 2px 0 0" corner="top: 24px; right: 24px;" />
      <CornerAccent position="0 0 2px 2px" corner="bottom: 24px; left: 24px;" />
      <CornerAccent position="0 2px 2px 0" corner="bottom: 24px; right: 24px;" />
    </CameraContainer>
  );
};

export default RobotCamera;
