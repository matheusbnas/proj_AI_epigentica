import React, { useState, useRef, useEffect } from 'react';
import { X, Send, Bot, User } from 'lucide-react';

interface ChatbotPanelProps {
  slideContent: string;
  onClose: () => void;
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  timestamp: Date;
}

const ChatbotPanel: React.FC<ChatbotPanelProps> = ({ slideContent, onClose }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      sender: 'bot',
      text: 'Olá! Eu sou o assistente deste slide. Como posso ajudá-lo com o conteúdo apresentado?',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom whenever messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: input,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    // Simulate bot response
    setTimeout(() => {
      generateBotResponse(input, slideContent);
    }, 1000);
  };

  const generateBotResponse = (userInput: string, context: string) => {
    // In a real application, this would call an API to a language model
    // For now, we're implementing a simple response generator
    
    let response = '';
    const lowercaseInput = userInput.toLowerCase();
    
    if (lowercaseInput.includes('resumo') || lowercaseInput.includes('resumir')) {
      response = 'Este slide apresenta informações sobre ' + 
        (context.includes('metabolismo') ? 'metabolismo e funções corporais relacionadas.' :
         context.includes('cardio') ? 'saúde cardiovascular e fatores de risco.' :
         context.includes('vitamina') ? 'vitaminas e minerais importantes para o organismo.' :
         'diversos aspectos de saúde e genética.');
    } 
    else if (lowercaseInput.includes('explicar') || lowercaseInput.includes('explique')) {
      response = 'O conteúdo deste slide detalha informações genéticas e suas implicações para a saúde. ' +
        'Existem variações genéticas que podem influenciar diferentes aspectos do seu organismo.';
    }
    else if (lowercaseInput.includes('dna') || lowercaseInput.includes('genética')) {
      response = 'A genética estuda os genes, a variação genética e a hereditariedade em organismos. ' +
        'Variações nos genes podem influenciar diversos aspectos da saúde, como metabolismo, ' +
        'risco de doenças e respostas a tratamentos.';
    }
    else {
      response = 'Posso ajudar a explicar o conteúdo deste slide. Você gostaria de um resumo das informações apresentadas ou tem alguma dúvida específica sobre o tema?';
    }

    const botMessage: ChatMessage = {
      id: Date.now().toString(),
      sender: 'bot',
      text: response,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, botMessage]);
    setIsTyping(false);
  };

  return (
    <div className="absolute right-4 bottom-16 w-80 sm:w-96 h-96 bg-white rounded-lg shadow-lg flex flex-col overflow-hidden">
      {/* Header */}
      <div className="bg-blue-600 text-white px-4 py-3 flex justify-between items-center">
        <div className="flex items-center">
          <Bot className="h-5 w-5 mr-2" />
          <h3 className="font-medium">Assistente do Slide</h3>
        </div>
        <button 
          onClick={onClose}
          className="text-white hover:text-gray-200 transition-colors"
          aria-label="Fechar chatbot"
        >
          <X className="h-5 w-5" />
        </button>
      </div>
      
      {/* Messages container */}
      <div className="flex-1 p-4 overflow-y-auto">
        {messages.map(message => (
          <div 
            key={message.id} 
            className={`mb-4 ${message.sender === 'user' ? 'flex justify-end' : 'flex justify-start'}`}
          >
            <div 
              className={`max-w-3/4 px-4 py-2 rounded-lg ${
                message.sender === 'user' 
                  ? 'bg-blue-600 text-white rounded-br-none' 
                  : 'bg-gray-100 text-gray-800 rounded-bl-none'
              }`}
            >
              <p className="text-sm">{message.text}</p>
              <span className="text-xs mt-1 block opacity-70">
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div className="flex justify-start mb-4">
            <div className="bg-gray-100 text-gray-800 px-4 py-2 rounded-lg rounded-bl-none">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input form */}
      <form onSubmit={handleSubmit} className="border-t border-gray-200 p-3 flex">
        <input
          type="text"
          value={input}
          onChange={handleInputChange}
          placeholder="Digite sua mensagem..."
          className="flex-1 px-3 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          className="bg-blue-600 text-white px-4 py-2 rounded-r-md hover:bg-blue-700 transition-colors"
          disabled={!input.trim()}
        >
          <Send className="h-5 w-5" />
        </button>
      </form>
    </div>
  );
};

export default ChatbotPanel;