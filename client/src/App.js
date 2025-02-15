import React, { useState } from 'react';
import styled from 'styled-components';
import VideoSection from './components/VideoSection';
import RobotCamera from './components/RobotCamera';
import Controls from './components/Controls';
import Login from './components/Login';
import MobileVoice from './components/MobileVoice';

const AppContainer = styled.div`
  height: 100vh;
  height: -webkit-fill-available;
  width: 100vw;
  position: fixed;
  background: #0A0A0B;
  overflow: hidden;
  padding-bottom: env(safe-area-inset-bottom, 0px);
`;

const MainCameraSection = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: calc(200px + env(safe-area-inset-bottom, 0px));
  overflow: hidden;
`;

const ZoomBubble = styled.div`
  position: absolute;
  top: 24px;
  right: 24px;
  width: 180px;
  height: 180px;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.1);
  z-index: 10;
`;

const SafeArea = styled.div`
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: calc(200px + env(safe-area-inset-bottom, 0px));
  padding-bottom: calc(env(safe-area-inset-bottom, 0px) + 40px);
  background: linear-gradient(
    to bottom,
    transparent,
    rgba(0, 0, 0, 0.8) 30%
  );
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 24px;
`;

const ControlsOverlay = styled.div`
  background: rgba(18, 18, 20, 0.8);
  backdrop-filter: blur(12px);
  padding: 20px 32px;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
`;

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  
  const handleJoystickMove = (data) => {
    console.log('Joystick moved:', data);
  };

  const handleMicToggle = (isActive) => {
    console.log('Microphone:', isActive ? 'on' : 'off');
  };

  // Add viewport height fix for iOS
  React.useEffect(() => {
    const setViewportHeight = () => {
      document.documentElement.style.setProperty(
        '--vh', 
        `${window.innerHeight * 0.01}px`
      );
      // Reset scroll position
      window.scrollTo(0, 0);
    };

    setViewportHeight();
    window.addEventListener('resize', setViewportHeight);
    return () => window.removeEventListener('resize', setViewportHeight);
  }, []);

  // Reset scroll position after login
  React.useEffect(() => {
    if (isLoggedIn) {
      window.scrollTo(0, 0);
    }
  }, [isLoggedIn]);

  return (
    <AppContainer>
      {!isLoggedIn ? (
        <Login onLogin={() => setIsLoggedIn(true)} />
      ) : (
        <>
          <MainCameraSection>
            <RobotCamera />
            <ZoomBubble>
              <VideoSection />
            </ZoomBubble>
          </MainCameraSection>
          <SafeArea>
            <ControlsOverlay>
              <Controls 
                onJoystickMove={handleJoystickMove}
                onMicToggle={handleMicToggle}
              />
            </ControlsOverlay>
          </SafeArea>
        </>
      )}
    </AppContainer>
  );
}

export default App;
