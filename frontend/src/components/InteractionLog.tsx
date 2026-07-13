import { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import type { RootState } from '../store';
import { updateField, updateFromAI, addFollowUp } from '../features/interactionSlice';
import { Mic, Search, Calendar, Clock, Sparkles } from 'lucide-react';

export default function InteractionLog() {
  const dispatch = useDispatch();
  const formState = useSelector((state: RootState) => state.interaction);
  const [chatInput, setChatInput] = useState('');
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [loading, setLoading] = useState(false);

  const handleInputChange = (field: keyof typeof formState, value: string) => {
    dispatch(updateField({ field, value }));
  };

  const handleSendChat = async () => {
    if (!chatInput.trim()) return;

    const userMessage = { role: 'user', content: chatInput };
    setMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setLoading(true);

    try {
      // Use VITE_API_URL if defined, otherwise fallback to relative or localhost
      const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
      const response = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage.content, current_form_state: formState })
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.updated_form_state) {
          dispatch(updateFromAI(data.updated_form_state));
        }
        setMessages(prev => [...prev, { role: 'ai', content: 'Extracted details from your input and updated the form.' }]);
      } else {
        setTimeout(() => {
          setMessages(prev => [...prev, { role: 'ai', content: 'Dummy response: Form updated.' }]);
          setLoading(false);
        }, 1000);
      }
    } catch (error) {
      console.error("API error", error);
      setTimeout(() => {
        setMessages(prev => [...prev, { role: 'ai', content: 'Failed to connect to backend. Please ensure it is running on port 8000.' }]);
        setLoading(false);
      }, 500);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex gap-4 h-[calc(100vh-80px)] text-sm">
      {/* Left Column: Form (65%) */}
      <div className="w-[65%] h-full bg-white rounded-md shadow-sm border border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-800">Interaction Details</h2>
        </div>
        
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-gray-700 mb-1.5">HCP Name</label>
              <input 
                type="text" 
                value={formState.hcp_name}
                onChange={(e) => handleInputChange('hcp_name', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
                placeholder="Search or select HCP..."
              />
            </div>
            <div>
              <label className="block text-gray-700 mb-1.5">Interaction Type</label>
              <select 
                value={formState.interaction_type}
                onChange={(e) => handleInputChange('interaction_type', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
              >
                <option value="Meeting">Meeting</option>
                <option value="Virtual">Virtual</option>
                <option value="Phone">Phone</option>
                <option value="Email">Email</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-gray-700 mb-1.5">Date</label>
              <div className="relative">
                <input 
                  type="date" 
                  value={formState.date}
                  onChange={(e) => handleInputChange('date', e.target.value)}
                  className="w-full pl-3 pr-10 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
                />
                <Calendar className="absolute right-3 top-2.5 h-4 w-4 text-gray-500 pointer-events-none" />
              </div>
            </div>
            <div>
              <label className="block text-gray-700 mb-1.5">Time</label>
              <div className="relative">
                <input 
                  type="time" 
                  value={formState.time}
                  onChange={(e) => handleInputChange('time', e.target.value)}
                  className="w-full pl-3 pr-10 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
                />
                <Clock className="absolute right-3 top-2.5 h-4 w-4 text-gray-500 pointer-events-none" />
              </div>
            </div>
          </div>

          <div>
            <label className="block text-gray-700 mb-1.5">Attendees</label>
            <input 
              type="text" 
              value={formState.attendees}
              onChange={(e) => handleInputChange('attendees', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
              placeholder="Enter names or search..."
            />
          </div>

          <div>
            <label className="block text-gray-700 mb-1.5">Topics Discussed</label>
            <div className="relative">
              <textarea 
                value={formState.topics_discussed}
                onChange={(e) => handleInputChange('topics_discussed', e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500 resize-none"
                placeholder="Enter key discussion points..."
              />
              <Mic className="absolute right-2 bottom-3 h-4 w-4 text-gray-500" />
            </div>
            <button className="mt-2 text-gray-700 bg-gray-100 px-3 py-1.5 rounded-md hover:bg-gray-200 transition-colors flex items-center border border-gray-200">
              <Sparkles className="h-4 w-4 mr-2 text-gray-600" /> Summarize from Voice Note (Requires Consent)
            </button>
          </div>

          <div>
            <h3 className="text-gray-800 font-medium mb-3">Materials Shared / Samples Distributed</h3>
            
            <div className="border border-gray-200 rounded p-4 mb-4">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="text-gray-700 mb-2">Materials Shared</h4>
                  <p className="text-gray-400 italic">No materials added.</p>
                </div>
                <button className="flex items-center px-3 py-1.5 border border-gray-300 rounded text-gray-700 hover:bg-gray-50">
                  <Search className="h-4 w-4 mr-2" /> Search/Add
                </button>
              </div>
            </div>

            <div className="border border-gray-200 rounded p-4">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="text-gray-700 mb-2">Samples Distributed</h4>
                  <p className="text-gray-400 italic">No samples added.</p>
                </div>
                <button className="flex items-center px-3 py-1.5 border border-gray-300 rounded text-gray-700 hover:bg-gray-50">
                  <Search className="h-4 w-4 mr-2" /> Add Sample
                </button>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-gray-800 font-medium mb-2">Observed/Inferred HCP Sentiment</label>
            <div className="flex items-center space-x-6">
              <label className="flex items-center cursor-pointer">
                <input 
                  type="radio" 
                  name="sentiment" 
                  value="Positive"
                  checked={formState.sentiment === 'Positive'}
                  onChange={(e) => handleInputChange('sentiment', e.target.value)}
                  className="mr-2"
                />
                😊 Positive
              </label>
              <label className="flex items-center cursor-pointer">
                <input 
                  type="radio" 
                  name="sentiment" 
                  value="Neutral"
                  checked={formState.sentiment === 'Neutral'}
                  onChange={(e) => handleInputChange('sentiment', e.target.value)}
                  className="mr-2"
                />
                😐 Neutral
              </label>
              <label className="flex items-center cursor-pointer">
                <input 
                  type="radio" 
                  name="sentiment" 
                  value="Negative"
                  checked={formState.sentiment === 'Negative'}
                  onChange={(e) => handleInputChange('sentiment', e.target.value)}
                  className="mr-2"
                />
                😞 Negative
              </label>
            </div>
          </div>

          <div>
            <label className="block text-gray-800 font-medium mb-1.5">Outcomes</label>
            <textarea 
              value={formState.outcomes}
              onChange={(e) => handleInputChange('outcomes', e.target.value)}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500 resize-none"
              placeholder="Key outcomes or agreements..."
            />
          </div>

          <div>
            <label className="block text-gray-800 font-medium mb-1.5">Follow-up Actions</label>
            <textarea 
              value={formState.follow_up_actions}
              onChange={(e) => handleInputChange('follow_up_actions', e.target.value)}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500 resize-none mb-2"
              placeholder="Enter next steps or tasks..."
            />
            
            {/* AI Suggested Follow-ups */}
            <div className="mt-2">
              <h4 className="text-gray-700 text-xs mb-1">AI Suggested Follow-ups:</h4>
              <div className="space-y-1">
                {(formState.suggested_follow_ups?.length > 0 ? formState.suggested_follow_ups : [
                  "+ Schedule follow-up meeting in 2 weeks",
                  "+ Send OncoBoost Phase III PDF",
                  "+ Add Dr. Sharma to advisory board invite list"
                ]).map((suggestion, idx) => (
                  <button 
                    key={idx}
                    onClick={() => dispatch(addFollowUp(suggestion.replace('+ ', '')))}
                    className="block text-blue-600 hover:underline text-xs text-left"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* Right Column: AI Assistant Chat (35%) */}
      <div className="w-[35%] h-full bg-white rounded-md shadow-sm border border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-100 flex items-center">
          <Sparkles className="h-5 w-5 text-blue-600 mr-2" />
          <div>
            <h2 className="font-semibold text-gray-800">AI Assistant</h2>
            <p className="text-xs text-gray-500">Log interaction via chat</p>
          </div>
        </div>

        <div className="flex-1 p-4 overflow-y-auto space-y-4">
          <div className="border border-gray-200 rounded p-4 text-gray-600">
            Log interaction details here (e.g., "Met Dr. Smith, discussed Product X efficacy, positive sentiment, shared brochure") or ask for help.
          </div>
          {messages.map((msg, idx) => (
            <div 
              key={idx} 
              className={`rounded p-3 max-w-[85%] ${msg.role === 'user' ? 'bg-gray-100 text-gray-800 self-end ml-auto' : 'bg-blue-50 text-blue-900 self-start border border-blue-100'}`}
            >
              {msg.content}
            </div>
          ))}
          {loading && (
            <div className="text-gray-500 italic text-xs">AI is typing...</div>
          )}
        </div>

        <div className="p-4 border-t border-gray-100 bg-gray-50 flex gap-2">
          <input 
            type="text" 
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendChat()}
            placeholder="Describe interaction..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
          />
          <button 
            onClick={handleSendChat}
            disabled={loading || !chatInput.trim()}
            className="px-4 py-2 bg-gray-500 text-white rounded font-medium hover:bg-gray-600 focus:outline-none disabled:opacity-50 flex items-center"
          >
            <Sparkles className="w-4 h-4 mr-2" /> Log
          </button>
        </div>
      </div>
    </div>
  );
}
