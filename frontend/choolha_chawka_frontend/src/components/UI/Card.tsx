import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: boolean;
}

const Card: React.FC<CardProps> = ({ children, className = '', padding = true }) => {
  return (
    <div className={`bg-gray-800 border border-yellow-400 rounded-lg shadow-lg ${padding ? 'p-6' : ''} ${className}`}>
      {children}
    </div>
  );
};

export default Card;