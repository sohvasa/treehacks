import React, { useEffect, useRef, useState } from 'react';
import styled from 'styled-components';

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

const FallbackImage = styled.img`
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
  background: ${props => props.isActive ? '#10B981' : '#EF4444'};
  box-shadow: 0 0 8px ${props => props.isActive ? 'rgba(16, 185, 129, 0.6)' : 'rgba(239, 68, 68, 0.6)'};
`;

const StatusText = styled.span`
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
`;

const VideoSection = () => {
  const videoRef = useRef(null);
  const [isVideoActive, setIsVideoActive] = useState(false);
  const [currentVideoUrl, setCurrentVideoUrl] = useState(null);

  // Function to update video source
  const updateVideo = (mp4Path) => {
    if (videoRef.current && mp4Path) {
      videoRef.current.src = mp4Path;
      console.log('playing video:', mp4Path);
      videoRef.current.play().catch(e => console.error('Error playing video:', e));
      setIsVideoActive(true);
      setCurrentVideoUrl(mp4Path);
    }
  };

  // Listen for new video events from the server
  useEffect(() => {
    const eventSource = new EventSource('http://localhost:5001/video-stream');
    
    console.log('eventSource:', eventSource);
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.videoUrl) {
        console.log('received videoUrl:', data.videoUrl);
        updateVideo(data.videoUrl);
      }
    };

    eventSource.onerror = (error) => {
      console.error('EventSource failed:', error);
      setIsVideoActive(false);
    };

    return () => {
      eventSource.close();
    };
  }, []);

  // Handle video end
  const handleVideoEnd = () => {
    setIsVideoActive(false);
  };

  return (
    <VideoContainer>
      {currentVideoUrl ? (
        <Video 
          ref={videoRef}
          autoPlay 
          playsInline
          onEnded={handleVideoEnd}
        />
      ) : (
        <FallbackImage src="/avatar.png" alt="AI Avatar" />
      )}
      <StatusBadge>
        <StatusDot isActive={isVideoActive} />
        <StatusText>{isVideoActive ? 'Speaking' : 'Ready'}</StatusText>
      </StatusBadge>
    </VideoContainer>
  );
};

export default VideoSection;
