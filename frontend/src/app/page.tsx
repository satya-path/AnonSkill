"use client"

import { useState } from "react";

export default function Home() {
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant', content: string }>>([]);
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    setMessages([...messages, { role: 'user', content: input }]);
    setInput('');
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-b from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <h1 className="text-xl font-semibold text-gray-800 dark:text-white">AnonSkill Chat</h1>
        </div>
      </div>

      {/* Chat Container */}
      <div className="flex-1 overflow-y-auto px-4 py-6 max-w-4xl mx-auto w-full">
        <div className="space-y-6">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-gray-500 dark:text-gray-400">
                <p className="text-lg">Welcome to AnonSkill Chat!</p>
                <p className="text-sm mt-2">Start a conversation by sending a message below.</p>
              </div>
            </div>
          ) : (
            messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-6 py-3 shadow-sm ${
                    message.role === 'user'
                      ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white'
                      : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-white border border-gray-100 dark:border-gray-700'
                  }`}
                >
                  <p className="text-[15px] leading-relaxed">{message.content}</p>
                  <span className="text-xs mt-1 block opacity-70">
                    {message.role === 'user' ? 'You' : 'Assistant'}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Input Form */}
      <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <form onSubmit={handleSubmit}>
            <div className="flex gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your message..."
                className="flex-1 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 px-5 py-3 text-[15px] focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
              <button
                type="submit"
                className="bg-gradient-to-r from-blue-500 to-blue-600 text-white px-8 py-3 rounded-xl hover:from-blue-600 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all font-medium shadow-sm"
              >
                Send
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
