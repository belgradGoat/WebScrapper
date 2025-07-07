import React, { useState } from 'react';
import { motion } from 'framer-motion';

const DashboardPage: React.FC = () => {
  const [messages, setMessages] = useState<Array<{ id: string; role: 'user' | 'assistant'; content: string; timestamp: Date }>>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m your AI assistant. Upload some data or ask me a question to get started with your analysis.',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');

  const handleSendMessage = () => {
    if (!inputMessage.trim()) return;

    const newMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, newMessage]);
    setInputMessage('');

    // Simulate AI response
    setTimeout(() => {
      const aiResponse = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: 'I understand your question. To provide a more accurate analysis, please upload some relevant data or provide more context about what you\'d like to explore.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, aiResponse]);
    }, 1000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Chat Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((message) => (
          <motion.div
            key={message.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`max-w-3xl ${message.role === 'user' ? 'order-2' : 'order-1'}`}>
              {/* Message bubble */}
              <div
                className={`apple-card p-4 ${
                  message.role === 'user'
                    ? 'bg-apple-blue-500 text-white ml-12'
                    : 'bg-white mr-12'
                }`}
              >
                <div className="flex items-start space-x-3">
                  {message.role === 'assistant' && (
                    <div className="w-8 h-8 bg-gradient-to-r from-apple-blue-500 to-apple-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
                      <span className="text-white text-sm">🤖</span>
                    </div>
                  )}
                  
                  <div className="flex-1">
                    <p className={`text-body ${message.role === 'user' ? 'text-white' : 'text-apple-gray-900'}`}>
                      {message.content}
                    </p>
                    <p className={`text-caption1 mt-2 ${
                      message.role === 'user' ? 'text-apple-blue-100' : 'text-apple-gray-500'
                    }`}>
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                  
                  {message.role === 'user' && (
                    <div className="w-8 h-8 bg-apple-gray-200 rounded-full flex items-center justify-center flex-shrink-0">
                      <span className="text-apple-gray-600 text-sm">👤</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="px-6 py-4 border-t border-apple-gray-200">
        <div className="flex flex-wrap gap-2 mb-4">
          <button className="px-3 py-1 bg-apple-gray-100 text-apple-gray-700 rounded-full text-subhead hover:bg-apple-gray-200 transition-colors">
            Summarize my data
          </button>
          <button className="px-3 py-1 bg-apple-gray-100 text-apple-gray-700 rounded-full text-subhead hover:bg-apple-gray-200 transition-colors">
            Find key insights
          </button>
          <button className="px-3 py-1 bg-apple-gray-100 text-apple-gray-700 rounded-full text-subhead hover:bg-apple-gray-200 transition-colors">
            Create visualization
          </button>
          <button className="px-3 py-1 bg-apple-gray-100 text-apple-gray-700 rounded-full text-subhead hover:bg-apple-gray-200 transition-colors">
            Export report
          </button>
        </div>
      </div>

      {/* Message Input Area */}
      <div className="glass border-t border-apple-gray-200 p-6">
        <div className="flex items-end space-x-4">
          <div className="flex-1">
            <div className="relative">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me anything about your data..."
                className="apple-input w-full resize-none min-h-[44px] max-h-32 pr-12"
                rows={1}
                style={{
                  height: 'auto',
                  minHeight: '44px'
                }}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = 'auto';
                  target.style.height = `${Math.min(target.scrollHeight, 128)}px`;
                }}
              />
              
              {/* Attach button */}
              <button className="absolute right-3 bottom-3 p-1 text-apple-gray-500 hover:text-apple-gray-700 transition-colors">
                <span className="text-lg">📎</span>
              </button>
            </div>
          </div>
          
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim()}
            className={`apple-button flex-shrink-0 px-6 py-3 ${
              inputMessage.trim()
                ? 'apple-button-primary'
                : 'bg-apple-gray-200 text-apple-gray-500 cursor-not-allowed'
            }`}
          >
            Send
          </button>
        </div>
        
        <div className="flex items-center justify-between mt-3 text-caption1 text-apple-gray-500">
          <div className="flex items-center space-x-4">
            <span>Press ⏎ to send, ⇧⏎ for new line</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span>AI Ready</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;