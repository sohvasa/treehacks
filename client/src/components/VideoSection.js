import React, { useEffect, useRef } from 'react';
import styled from 'styled-components';
import { ZoomVideo } from '@zoom/videosdk';

const VideoContainer = styled.div`
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
  background: #1a1a1a;
`;

const Video = styled.video`
  width: 100%;
  height: 100%;
  object-fit: cover;
`;

const StatusBadge = styled.div`
  position: absolute;
  top: 12px;
  left: 12px;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  padding: 6px 10px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
`;

const StatusDot = styled.div`
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10B981;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
`;

const StatusText = styled.span`
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
`;

const VideoSection = () => {
  const videoRef = useRef(null);

  useEffect(() => {
    // Initialize Zoom client here when you have the SDK credentials
    // This is a placeholder for the Zoom implementation
    const initializeZoom = async () => {
      // Implement Zoom initialization here
    };

    initializeZoom();
  }, []);

  return (
    <VideoContainer>
      <Video ref={videoRef} autoPlay playsInline />
      <StatusBadge>
        <StatusDot />
        <StatusText>Live</StatusText>
      </StatusBadge>
    </VideoContainer>
  );
};

export default VideoSection;
