import React from 'react';
import { Link } from 'react-router-dom';
import { useUser } from '../context/UserContext';

const Home = () => {
  const { user, logout } = useUser();


  return (
    <div className="relative min-h-screen w-full overflow-hidden text-white">
      {/* 🔹 Background Video */}
      <video
        autoPlay
        loop
        muted
        playsInline
        className="absolute top-0 left-0 w-full h-full object-cover z-0"
      >
        <source src="/video/homePageBackground.mp4" type="video/mp4" />
        Your browser does not support the video tag.
      </video>

      {/* 🔹 Content Overlay */}
      <div className="relative z-10 flex flex-col justify-between min-h-screen bg-black bg-opacity-60 p-6">
        {/* 🔸 Top Text */}
        <div className="text-center mt-6">
          <h2 className="text-4xl font-bold mb-2">🏈 Welcome to TripleStreak!</h2>
          <p className="text-lg">Make your weekly picks, compete with friends, and go for the streak!</p>
        </div>

        {/* 🔸 Bottom Section */}

      </div>
    </div>
  );
};

export default Home;
